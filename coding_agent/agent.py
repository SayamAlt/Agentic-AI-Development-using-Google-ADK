import os, sys
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams, StreamableHTTPConnectionParams
from pathlib import Path
from dotenv import load_dotenv
from mcp import StdioServerParameters
from google.adk.models.lite_llm import LiteLlm

# Load settings
AGENT_DIR = Path(__file__).resolve().parent
load_dotenv(AGENT_DIR / '.env')

WORKSPACE_DIR = Path(
    os.getenv("WORKSPACE_DIR", AGENT_DIR / "workspace")
).resolve()
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

NPX = "npcx.cmd" if os.name == "nt" else "npx"
SHELL_SERVER = AGENT_DIR / "servers" / "shell_server.py"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable is not set. Please set it in the .env file.")

# Decide which shell tools require approval for execution. If True, the user must approve each command before it is run.
AUTO_APPROVED_PREFIXES = (
    "pytest",
    "python -m pytest",
    "git status",
    "git log",
    "git diff"
)

def shell_needs_approval(command=None, module=None):
    """ Returns True to ask the user for approval before executing a shell command; returns False to execute the command immediately without approval. """
    # Starting a server always needs approval, since it can be a long-running process that the user may not want to start.
    if module is not None:
        return True
    
    # Tools without a command do not need any approval.
    if command is None:
        return False
    
    # Commands matching these prefixes are automatically approved.
    if command.strip().startswith(AUTO_APPROVED_PREFIXES):
        return False
    
    # All other commands need approval.
    return True
    
# Connect to the local filesystem MCP server
filesystem_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=NPX,
            args=[
                "-y",
                "@modelcontextprotocol/server-filesystem",
                str(WORKSPACE_DIR)
            ]
        ),
        timeout=60
    ),
    tool_filter=[
        "list_directory",
        "directory_tree",
        "read_text_file",
        "read_multiple_files",
        "search_files",
        "get_file_info",
        "create_directory",
        "write_file",
        "edit_file"
    ]
)

# Connect to the local Shell MCP server
shell_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[
                str(SHELL_SERVER),
                "--root",
                str(WORKSPACE_DIR)
            ]
        ),
        timeout=90
    ),
    tool_filter=[
        "run_command",
        "check_url",
        "server_logs",
        "start_server",
        "stop_server",
        "workspace_info"
    ],
    require_confirmation=shell_needs_approval
)

# Initialize the agent with the list of tools
tools = [filesystem_tools, shell_tools]

# Add GitHub tools if GITHUB_TOKEN is set
if GITHUB_TOKEN:
    github_env = {**os.environ, "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN}

    github_read_tools = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=NPX,
                args=["-y", "@modelcontextprotocol/server-github"],
                env=github_env
            ),
            timeout=30
        ),
        tool_filter=[
            "get_me",
            "get_file_contents",
            "list_branches",
            "list_issues",
            "list_pull_requests",
            "get_pull_request",
            "get_pull_request_files",
            "get_pull_request_diff",
            "get_pull_request_reviews",
            "issue_read"
        ]
    )

    github_write_tools = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=NPX,
                args=["-y", "@modelcontextprotocol/server-github"],
                env=github_env
            ),
            timeout=30
        ),
        tool_filter=[
            "create_repository",
            "create_pull_request",
            "update_pull_request",
            "merge_pull_request",
            "create_pull_request_review",
            "create_branch",
            "push_files",
            "add_issue_comment"
        ],
        require_confirmation=True
    )

    tools.extend([github_read_tools, github_write_tools])
    
# Define the agent's instructions
INSTRUCTION = f"""
    You are a careful coding agent. You can build, fix, and run code projects.

    Your workspace is: {WORKSPACE_DIR}
    All files you create must be inside it.

    Tools:
    - Files: use filesystem tools to list, read, create, and edit files. Prefer edit_file for small changes.
    - Running code: use run_command (e.g. "pytest -q", "python main.py"). Never use it to read or list files.
    - GitHub: use GitHub tools for remote work (repos, issues, branches, pull requests). Use push_files to publish code, never "git push".

    How to work:
    1. Check what already exists in the workspace before writing anything.
    2. Work in small steps. Run tests after each change.
    3. If tests fail, read the error, fix the cause, and retry. Stop after 3 failed attempts and explain what's wrong.
    4. For web apps, test with pytest first. To run the app, use start_server, then check_url and server_logs. Leave it running unless told to stop.
    5. When done, summarize what changed and the final test result.
"""

# Create the agent
root_agent = Agent(
    model=LiteLlm(model="gpt-4o-mini"),
    name='coding_agent',
    description='A coding agent that can edit files, run shell tests, and use GitHub.',
    instruction=INSTRUCTION,
    tools=tools
)