from typing import Literal
from agentic_network import AgentState
from langchain_core.messages import AIMessage


def tools_condition(agent_state: AgentState) -> Literal["tools", "end"]:
    """Checks the last AI message for tool calls and decides the next step."""
    print("--- Deciding next step ---")
    last_message = agent_state["all_dialog"][-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        print("Decision: Call tools.")
        return "tools"

    print("Decision: End conversation.")
    return "end"
