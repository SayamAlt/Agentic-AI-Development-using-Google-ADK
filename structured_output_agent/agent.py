from google.adk.agents.llm_agent import Agent
from google.adk.agents.callback_context import CallbackContext
from pydantic import BaseModel, Field
from typing import Literal

class Enquiry(BaseModel):
    name: str | None = Field(default=None, description="Customer's full name in title case")
    email: str | None = Field(default=None, description="Customer's email address exactly as written")
    interested_in: list[Literal["GenAI", "Data Science", "MLOps", "Deep Learning", "Machine Learning", "Computer Vision", "NLP", "Other"]] | None = Field(description="Current fields which the customer is interested in")
    budget_inr: int | None = Field(default=None, ge=0, le=10000000, description="Total budget range of the customer in rupees as a plain number. Convert '20k' to 20000")

def append_enquiry(callback_context: CallbackContext):
    latest = callback_context.state.get('enquiry')
    
    if latest:
        history = callback_context.state.get('enquiries', [])
        history.append(latest)
        callback_context.state['enquiries'] = history

root_agent = Agent(
    model='gemini-3.5-flash-lite',
    name='enquiry_agent',
    description="A helpful agent that extracts a customer's enquiry details from a message.",
    instruction="""
        Read a customer's enquiry and extract all the relevant details.
        If something is not mentioned, leave it as empty.
        Never guess or invent any new details.
    """,
    output_schema=Enquiry,
    output_key='enquiry',
    after_agent_callback=append_enquiry
)