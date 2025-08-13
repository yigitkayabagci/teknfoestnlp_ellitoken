from enum import StrEnum, auto
from langgraph.graph import START, END


class GraphRoutes(StrEnum):
    START = START
    END = END

    TOOLS = auto()

    TOPIC_MANAGER_AGENT = auto()
    DIAGNOSIS_AGENT = auto()
    APPOINTMENT_AGENT = auto()

    SMALL_TALK_AGENT = auto()
    OUT_OF_TOPIC_AGENT = auto()
