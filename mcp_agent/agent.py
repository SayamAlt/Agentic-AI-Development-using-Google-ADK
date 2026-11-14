from google.adk.agents.llm_agent import Agent
from pathlib import Path
import os
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams, StreamableHTTPConnectionParams
from mcp import StdioServerParameters
from dotenv import load_dotenv

load_dotenv()

github_token = os.environ.get("GITHUB_TOKEN")

if not github_token:
    raise ValueError("GITHUB_TOKEN environment variable is not set. Please set it in your .env file.")

folder = Path(__file__).parent.joinpath("files").resolve()
folder.mkdir(exist_ok=True)

root_agent = Agent(
    model='gemini-3.5-flash-lite',
    name='filesystem_and_github_agent',
    description="A helpful agent that can manage files in a specified folder and interact with GitHub repositories. It can read, write, and modify files, as well as perform Git operations using the provided GitHub token.",
    instruction=f"""
        You have access to the filesystem and GitHub MCP servers.
        Use their respective tools to manage local files and handle GitHub repositories and workflows.
        Local files are located in the folder: {folder}. Use absolute paths for all filesystem operations.
    """,
    tools=[
        # Manage local files using the filesystem MCP server
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", str(folder)],
                )
            )   
        ),
        # Interact with GitHub using the GitHub MCP server
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url="https://api.githubcopilot.com/mcp/", # GitHub MCP server URL
                headers={"Authorization": f"Bearer {github_token}"}
            )
        )
    ]
)