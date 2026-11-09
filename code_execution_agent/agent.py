from google.adk.agents.llm_agent import Agent
from google.adk.code_executors import BuiltInCodeExecutor

root_agent = Agent(
    model='gemini-2.5-flash-lite',
    name='root_agent',
    description='A helpful assistant that can write and execute code in various programming languages.',
    instruction="""
        Answer user questions accurately and concisely.
        When a question involves any calculations, data analysis, or anything pertaining to programming, write code in the appropriate programming language and execute it to get the answer.
        If you cannot answer a question, say "I don't know.
        Once you have the answer, provide it to the user in a clear and precise manner.
    """,
    code_executor=BuiltInCodeExecutor()
)