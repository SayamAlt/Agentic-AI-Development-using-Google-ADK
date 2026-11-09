from google.adk.agents.llm_agent import Agent
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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
    
root_agent = Agent(
    model='gemini-2.5-flash-lite',
    name='clock_agent',
    description='A helpful assistant that can get the current date and time in a specific location.',
    instruction="""
        Answer user questions accurately and concisely.
        When a question involves getting the current date or time in a specific timezone, use the get_current_time function to retrieve the information.
        If the timezone is invalid, return an error message.
        If you cannot answer a question, say "I don't know."
        Once you have the answer, provide it to the user in a clear and precise manner.
    """,
    tools=[get_current_time]
)