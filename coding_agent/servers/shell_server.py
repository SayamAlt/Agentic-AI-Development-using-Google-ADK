"""
safe-shell MCP server: runs allowlisted commands inside a workspace folder.

Run directly for testing:
    python coding_agent/servers/shell_server.py --root /path/to/workspace

ADK starts this automatically over stdio (see coding_agent/agent.py).
"""
import argparse
import atexit
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer

MAX_OUTPUT_CHARS = 4000
DEFAULT_TIMEOUT = 60
SERVER_PORT = 8001
LOG_FILE = Path(tempfile.gettempdir()) / "safe-shell-server.log"

# Programs the agent can run
ALLOWED = {"python", "pytest", "pip", "git"}

# Sub-commands that are always blocked
BLOCKED = {
    "git": {"push", "remote", "config", "reset", "clean", "rebase", "force"},
    "pip": {"uninstall", "download"},
}

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True, help="Workspace folder for all commands")
ROOT = Path(parser.parse_args().root).resolve()
ROOT.mkdir(parents=True, exist_ok=True)

mcp = MCPServer(
    "safe-shell",
    instructions=(
        "Runs allowlisted commands (python, pytest, pip, git) inside the project workspace. "
        "Use it to run code and tests. Use the filesystem server to read files."
    ),
)

def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return f"...[truncated {len(text) - MAX_OUTPUT_CHARS} chars]...\n" + text[-MAX_OUTPUT_CHARS:]

def _check(parts: list[str]) -> str | None:
    if not parts:
        return "Empty command."
    prog = parts[0]
    if prog not in ALLOWED:
        return f"'{prog}' is not allowed. Allowed: {sorted(ALLOWED)}"
    if len(parts) > 1 and parts[1] in BLOCKED.get(prog, set()):
        return f"'{prog} {parts[1]}' is blocked."
    if any(t in {"|", "&&", ";", ">", "<", "||", "`"} for t in parts):
        return "Pipes, redirects and chaining are not allowed. Run one command at a time."
    return None

def _resolve(parts: list[str]) -> list[str]:
    # Always use the same Python interpreter as this server
    if parts[0] == "python":
        return [sys.executable, *parts[1:]]
    if parts[0] in {"pytest", "pip"}:
        return [sys.executable, "-m", parts[0], *parts[1:]]
    return parts

def _read_log() -> str:
    try:
        return _truncate(LOG_FILE.read_text(errors="replace")) or "(no output yet)"
    except FileNotFoundError:
        return "(no log yet)"

_server: subprocess.Popen | None = None

@mcp.tool()
def run_command(command: str, timeout_seconds: int = DEFAULT_TIMEOUT) -> str:
    """Run one allowed command in the workspace and return its output.

    Allowed: python, pytest, pip, git (git push/remote/config/reset/clean/rebase are blocked).
    Examples: "pytest -q", "python main.py", "git status", "git add .", "git commit -m 'msg'".

    Args:
        command: Command line to run, e.g. "pytest -q".
        timeout_seconds: Max run time in seconds (capped at 60).
    """
    try:
        parts = shlex.split(command)
    except ValueError as e:
        return f"Could not parse command: {e}"
    err = _check(parts)
    if err:
        return f"REJECTED: {err}"
    parts = _resolve(parts)
    timeout = max(1, min(timeout_seconds, DEFAULT_TIMEOUT))
    try:
        result = subprocess.run(
            parts,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return f"TIMEOUT: command did not finish within {timeout}s."
    except FileNotFoundError:
        return f"'{parts[0]}' is not installed."
    output = (result.stdout or "") + (result.stderr or "")
    return f"exit code: {result.returncode}\n{_truncate(output) or '(no output)'}"

@mcp.tool()
def workspace_info() -> str:
    """Return the workspace path and the list of allowed programs."""
    return f"workspace: {ROOT}\nallowed: {sorted(ALLOWED)}"

@mcp.tool()
def start_server(module: str) -> str:
    """Start a FastAPI/ASGI app with uvicorn in the background on http://127.0.0.1:8001.

    Use this instead of run_command for web apps since servers never exit.

    Args:
        module: ASGI app to serve as 'module:variable', e.g. 'app:app'.
    """
    global _server
    if not re.fullmatch(r"[A-Za-z_][\w.]*:[A-Za-z_]\w*", module):
        return "REJECTED: module must look like 'app:app'."
    if _server and _server.poll() is None:
        return f"Already running (pid {_server.pid}). Use stop_server first."
    log = open(LOG_FILE, "w")
    _server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", module, "--host", "127.0.0.1", "--port", str(SERVER_PORT)],
        cwd=ROOT,
        stdout=log,
        stderr=subprocess.STDOUT,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    time.sleep(2)
    if _server.poll() is not None:
        return f"Server exited (code {_server.returncode}). Log:\n{_read_log()}"
    return f"Server running at http://127.0.0.1:{SERVER_PORT} (pid {_server.pid}).\n{_read_log()}"

@mcp.tool()
def stop_server() -> str:
    """Stop the background server started with start_server."""
    global _server
    if not _server or _server.poll() is not None:
        return "No server is running."
    _server.terminate()
    try:
        _server.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _server.kill()
    _server = None
    return "Server stopped."

@mcp.tool()
def server_logs() -> str:
    """Return the latest output from the background server."""
    status = "running" if _server and _server.poll() is None else "not running"
    return f"server is {status}\n{_read_log()}"

@mcp.tool()
def check_url(path: str = "/") -> str:
    """Send a GET request to the running app and return the status and body.

    Only the local app server can be reached.

    Args:
        path: URL path to request, e.g. '/todos/'.
    """
    if not path.startswith("/"):
        return "REJECTED: path must start with '/', e.g. '/todos/'."
    url = f"http://127.0.0.1:{SERVER_PORT}{path}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return f"HTTP {resp.status}\n{_truncate(resp.read().decode(errors='replace'))}"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}\n{_truncate(e.read().decode(errors='replace'))}"
    except Exception as e:
        return f"Could not reach {url}: {e}. Is the server running? Try server_logs."

@atexit.register
def _cleanup() -> None:
    if _server and _server.poll() is None:
        _server.terminate()

if __name__ == "__main__":
    mcp.run()
