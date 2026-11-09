from google.adk.agents.llm_agent import Agent
from google.adk.tools.langchain_tool import LangchainTool
from langchain_tavily import TavilySearch

# Create the LangChain-powered Tavily search tool
tavily_search = TavilySearch(
    max_results=5,
    topic="general"
)

# Wrap it in a LangchainTool for integration with the ADK Agent
tavily_search_tool = LangchainTool(tool=tavily_search, name="TavilySearch", description="A tool to search the web using Tavily.")

root_agent = Agent(
    model='gemini-2.5-flash-lite',
    name='root_agent',
    description='A helpful assistant that can search the web using Tavily and provide relevant information.',
    instruction="""
        Answer user questions accurately and concisely.
        Use the TavilySearch tool to find information on the web when necessary.
        If you cannot answer a question, say "I don't know.
        Once you have the answer, provide it to the user in a clear and precise manner.
    """,
    tools=[tavily_search_tool]
)