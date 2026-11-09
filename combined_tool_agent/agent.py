from google.adk.agents.llm_agent import Agent
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from google.adk.code_executors import UnsafeLocalCodeExecutor
from google.adk.tools import google_search
from google.adk.tools.langchain_tool import LangchainTool
from langchain_tavily import TavilySearch
from datetime import datetime
from google.genai import types
from google.adk.models.lite_llm import LiteLlm

MODEL = "gpt-4o-mini"

# Function tool to fetch the current date and time for a given timezone
def get_current_time(timezone: str) -> dict:
    """
        Gets the current date and time for a given timezone.
        
        Use this whenever the user asks what date or time it is in a specific timezone. If the timezone is invalid, return an error message.
        
        Args:
            timezone (str): An IANA timezone string (e.g., 'America/New_York', 'Europe/London').
        
        Returns:
            dict: A dictionary containing the status, timezone, date, time, and weekday. If the timezone is invalid, returns an error message.
    """
    try:
        now = datetime.now(ZoneInfo(timezone))
    except ZoneInfoNotFoundError:
        return {
            "status": "error",
            "error_message": f"Invalid timezone: {timezone}. Please provide a valid timezone."
        }
        
    return {
        "status": "success",
        "timezone": timezone,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "weekday": now.strftime("%A")
    }
    
# Third-party tool to perform web searches using Tavily
tavily_search_tool = LangchainTool(
    name="tavily_search",
    description="A tool to perform web searches using Tavily. Use this tool to find information on the web when the answer is not readily available.",
    tool=TavilySearch(max_results=5, topic="general")
)

# Create a specialized Gemini subagent to handle native Google search engine grounding
search_sub_agent = Agent(
    model="gemini-2.5-flash-lite",
    name="gemini_search_specialist",
    description=(
        "Performs server-side Google searches using native search grounding."
    ),
    instruction=(
        "You are a dedicated search specialist. Use the google_search tool to"
        " fetch accurate real-time web information and return clear summaries."
    ),
    tools=[google_search],
)

# One unified agent with access to all tools: code execution, timezone fetching, and web search
root_agent = Agent(
    model=LiteLlm(model=MODEL),
    name='combined_tool_agent',
    description='A helpful assistant that can write and execute code, get the current date and time in a specific timezone, and perform web searches.',
    instruction="""
        Answer user questions accurately and concisely.
        When a question requires any calculations, data analysis, or anything pertaining to programming, write code in the appropriate programming language and execute it to get the answer.
        When a question involves getting the current date or time in a specific timezone, use the get_current_time function to retrieve the information.
        When a question requires information that is not readily available, use the tavily_search tool to perform a web search and provide the answer.
        If you cannot answer a question, say "I don't know."
        Once you have the answer, provide it to the user in a clear and precise manner.
    """,
    tools=[get_current_time, tavily_search_tool], # function tool + third-party tool
    code_executor=UnsafeLocalCodeExecutor(),
    sub_agents=[search_sub_agent],
    generate_content_config=types.GenerateContentConfig(
        tool_config=types.ToolConfig(
            include_server_side_tool_invocations=True
        )
    )
)