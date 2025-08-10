from langchain_core.messages import AIMessage

from agentic_network.core import AgentState, GraphRoutes


def decide_tools(agent_state: AgentState) -> GraphRoutes:
    """Checks the last AI message for tool calls and decides the next step."""
    print("--- Deciding next step ---")
    last_message = agent_state["all_dialog"][-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        print("Decision: Call tools.")
        return GraphRoutes.TOOLS

    print("Decision: End conversation.")
    return GraphRoutes.END
