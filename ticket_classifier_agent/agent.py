from google.adk.agents.llm_agent import Agent
from typing import Literal
from pydantic import BaseModel, Field

class Ticket(BaseModel):
    category: Literal["refund", "technical", "product_query", "payment", "other"] = Field(
        description="The main concern of the customer's question",
        default_factory=list
    ),
    urgency: Literal["low", "medium", "high"] = Field(
        default_factory=list,
        description="high = blocked right now or upset; medium = needs help soon; low = general question"
    ),
    needs_human: bool = Field(
        description="True if a human intervention is required: money disputes, anger, or anything unclear"
    )

root_agent = Agent(
    model='gemini-3.5-flash-lite',
    name='ticket_classifier_agent',
    description='A helpful agent that classifies customer messages into relevant support ticket categories.',
    instruction="""
        You classify support ticket messages sent by our customers.
        Read the message very carefully and classify it into the most appropriate ticket.
        Adopt a conservative approach: if money, anger, or any confusion is involved, immediately escalate to human by setting needs_human to true.
        Strictly never assume anything by yourself.
    """,
    output_schema=Ticket,
    output_key="ticket"
)