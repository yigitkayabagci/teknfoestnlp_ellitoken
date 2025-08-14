from typing import Optional, Literal, Iterable
from uuid import uuid4

from agentic_network.core import AgentState
from agentic_network.core import GraphRoutes
from agentic_network.core.agent_state import Topic
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage


# ----- Helpers -----
def _new_id() -> str:
    return str(uuid4())


# ----- API -----
def find_topic_index(topics: list[Topic], topic_id: str) -> int:
    for i, topic in enumerate(topics):
        if topic["id"] == topic_id:
            return i
    return -1


def get_current_topic(agent_state: AgentState) -> Optional[Topic]:
    if not agent_state["topic_stack"]: return None
    return agent_state["topic_stack"][-1]


# TODO: we should also populate the person data
def create_topic(state: AgentState, agent: GraphRoutes) -> AgentState:
    """
    Create a Topic and push it to the top of topic_stack.
    Returns a patch suitable for LangGraph (no in-place mutation).
    """
    topic: Topic = {
        "id": _new_id(),
        "agent": agent,
        "person_data": {
            "name": "",
            "symptoms": [],
            "appointment_data": {
                "hospital_name": "",
                "doctor_name": "",
                "clinic": "",
                "date": "",
                "time": "",
            },
        },
    }
    return {"topic_stack": (state.get("topic_stack") or []) + [topic]}


def disclose_current_topic(state: AgentState) -> AgentState:
    """
    Move the top topic from topic_stack to disclosed_topics.
    If topic_id is None, pops the top of the stack.
    No-ops if not found.
    """
    stack = list(state.get("topic_stack") or [])
    disclosed = list(state.get("disclosed_topics") or [])

    if not stack: return {}

    idx = len(stack) - 1

    topic = stack[idx]
    new_stack = stack[:idx]
    new_disclosed = disclosed + [topic]

    return {
        "topic_stack": new_stack,
        "disclosed_topics": new_disclosed,
    }


def resurface_topic(state: AgentState, topic_id: str) -> AgentState:
    """
    Find a topic by id in either topic_stack or disclosed_topics,
    and bring it to the top of topic_stack. Removes it from wherever it was.
    No-op if not found anywhere.
    """
    stack = list(state.get("topic_stack") or [])
    disclosed = list(state.get("disclosed_topics") or [])

    # 1) Try stack first: move to top if present
    idx = find_topic_index(stack, topic_id)
    if idx != -1:
        topic = stack[idx]
        new_stack = stack[:idx] + stack[idx + 1:] + [topic]
        return {"topic_stack": new_stack}

    # 2) Else try disclosed: remove from disclosed and push onto stack
    didx = find_topic_index(disclosed, topic_id)
    if didx != -1:
        topic = disclosed[didx]
        new_disclosed = disclosed[:didx] + disclosed[didx + 1:]
        new_stack = stack + [topic]
        return {
            "topic_stack": new_stack,
            "disclosed_topics": new_disclosed,
        }

    # 3) Not found anywhere → no-op
    return {}


def add_topic_id_to_message(msg: AnyMessage, topic_id: str | None) -> AnyMessage:
    """Return a copy of msg with metadata['topic_id']=topic_id."""
    meta = dict(getattr(msg, "metadata", {}) or {})
    meta["topic_id"] = topic_id
    # pydantic models support .copy(update=...)
    try:
        return msg.model_copy(update={"metadata": meta})  # type: ignore[attr-defined]
    except Exception:
        # fallback for dataclass-like messages
        return msg.__class__(content=msg.content, metadata=meta)


def make_msg(role: Literal["user", "assistant", "system"], content: str, topic_id: str | None) -> AnyMessage:
    base: AnyMessage = (
        HumanMessage(content=content)
        if role == "user"
        else AIMessage(content=content)
        if role == "assistant"
        else SystemMessage(content=content)
    )
    return add_topic_id_to_message(base, topic_id)


def add_message_to_dialogue(state: AgentState, role: Literal["user", "assistant", "system"], content: str) -> AgentState:
    stack = state.get("topic_stack") or []
    topic_id = stack[-1]["id"] if stack else None

    if topic_id is None:
        raise RuntimeError("Topic Stack is somehow empty.")

    msg = make_msg(role, content, topic_id)
    return {"all_dialog": [msg]}


def get_messages_for_topic(state: AgentState, topic_id: str) -> list[AnyMessage]:
    return [
        m for m in state.get("all_dialog", [])
        if (getattr(m, "metadata", {}) or {}).get("topic_id") == topic_id
    ]


def get_messages_for_current_topic(state: AgentState) -> list[AnyMessage]:
    stack = state.get("topic_stack") or []
    topic_id = stack[-1]["id"] if stack else None

    if topic_id is None:
        raise RuntimeError("Topic Stack is somehow empty.")

    return get_messages_for_topic(state, topic_id)


def _role_of(msg: AnyMessage) -> str:
    # "human" -> "user" for friendlier logs
    t = getattr(msg, "type", "") or msg.__class__.__name__.lower()
    return "user" if t == "human" else "assistant" if t == "ai" else t

def _content_str(msg: AnyMessage) -> str:
    c = getattr(msg, "content", "")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        # multimodal content: try to extract text parts
        parts = []
        for item in c:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(c)

def format_dialog_with_topics(messages: Iterable[AnyMessage]) -> str:
    """Format messages as lines that include [topic:<id>] when present."""
    lines = []
    for m in messages:
        topic_id = (getattr(m, "metadata", {}) or {}).get("topic_id")
        topic_tag = f"[topic:{topic_id}] " if topic_id else ""
        lines.append(f"{topic_tag}{_role_of(m)}: {_content_str(m)}")
    return "\n".join(lines)


def format_dialog(messages: Iterable[AnyMessage]) -> str:
    """Format messages as lines without topic IDs."""
    return "\n".join(f"{_role_of(m)}: {_content_str(m)}" for m in messages)


def redirect_to_appointment_agent(agent_state: AgentState):
    get_current_topic(agent_state)["agent"] = GraphRoutes.APPOINTMENT_AGENT

# tests:
# messages = [add_topic_id_to_message(HumanMessage("hello!"), "12341235245"), HumanMessage("lets go!")]
# print(format_dialog_with_topics(messages))
