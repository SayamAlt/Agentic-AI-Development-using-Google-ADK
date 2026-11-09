from google.adk.agents.llm_agent import Agent
from google.adk.tools.google_search_agent_tool import google_search

root_agent = Agent(
    model='gemini-2.5-flash-lite',
    name='root_agent',
    description='A helpful assistant that can perform web search.',
    instruction="""
        Answer user questions accurately and concisely.
        Use Google Search to find any current information that is not available in your training data or when you need to verify facts.
        If you cannot answer a question, say "I don't know."
    """,
    tools=[google_search]
)