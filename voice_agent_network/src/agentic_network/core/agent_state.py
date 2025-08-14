from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph.message import add_messages


class Topic(TypedDict):
    id: str
    agent: str
    appointment_data: dict


class AgentState(TypedDict):
    current_message: str
    all_dialog: Annotated[list[AnyMessage], add_messages]
    thoughts: Annotated[list[AnyMessage], add_messages]
    topic_stack: list[Topic]
    disclosed_topics: list[Topic]
