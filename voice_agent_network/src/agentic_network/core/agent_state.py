from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph.message import add_messages


class AppointmentData(TypedDict):
    hospital_name: str
    doctor_name: str
    clinic: str
    date: str
    time: str

class PersonData(TypedDict):
    name: str
    symptoms: list[str]
    appointment_data: AppointmentData


class Topic(TypedDict):
    id: str
    agent: str
    person_data: PersonData


class AgentState(TypedDict):
    current_message: str
    all_dialog: Annotated[list[AnyMessage], add_messages]
    thoughts: Annotated[list[AnyMessage], add_messages]
    topic_stack: list[Topic]
    disclosed_topics: list[Topic]
