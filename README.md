# Agentic AI Development using Google ADK

This repo is a hands-on learning project built while learning [Google ADK](https://google.github.io/adk-docs/). Each folder is a separate AI agent that shows a specific concept or use case.

## Agents

### ai_chatbot
A simple AI chatbot powered by GPT-4o. Answers user questions in a conversational way. Good starting point to understand how ADK agents work.

### google_agent
An agent that uses Google Search to find real-time information from the web. Built on Gemini 2.5 Flash Lite. Useful when the question needs up-to-date facts.

### tavily_search_agent
Similar to the Google agent but uses Tavily as the search tool instead. Shows how to plug in a third-party LangChain tool into an ADK agent.

### code_execution_agent
An agent that can write and run code to answer questions. Great for math problems, data tasks, or anything that needs actual computation.

### world_clock_agent
An agent that tells you the current date and time in any timezone. Uses a custom Python function as a tool.

### combined_tool_agent
The most complete agent in this repo. Combines all the tools together: code execution, timezone lookup, Tavily web search, and a Google Search sub-agent. Shows how to build a multi-tool agent with both function tools and sub-agents.

### nexuslearn_refund_agent
A refund assistant for a demo learning platform called NexusLearn. It checks if a student is eligible for a refund based on a 7-day window and 20% completion limit. Uses a local SQLite database with sample students, courses, and enrollments. Shows how to build a tool-heavy agent with real database interactions and user confirmation flows.

## Setup

1. Clone the repo
2. Create a virtual environment and activate it
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install Google ADK
   ```bash
   pip install google-adk
   ```
4. Go into any agent folder and create a `.env` file with your API keys
5. Run the agent
   ```bash
   adk web
   ```

## Notes

- `.env` files are excluded from git for security
- Each agent folder has its own `agent.py` as the entry point
- The `nexuslearn_refund_agent` needs the database set up first by running `setup_database.py`

## License

MIT
