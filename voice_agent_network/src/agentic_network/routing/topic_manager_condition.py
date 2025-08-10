from langchain_core.messages import AIMessage
from agentic_network.core import AgentState, GraphRoutes


def decide_tools(agent_state: AgentState) -> GraphRoutes:
    """Checks the last AI message for tool calls and decides the next step."""
    print("--- Deciding next step ---")


def decide_topic_manager(agent_state: AgentState) -> GraphRoutes:
    """Checks the last AI message for Topic Manager Agent calls and decides the next step."""
    print("--- Deciding next step ---")
    last_message = agent_state["all_dialog"][-1]
    message_content = last_message.content.strip()

    if isinstance(last_message, AIMessage) and message_content.count("CALL TOPIC MANAGER") != 0:
        print("Decision: Call the Topic Manager Cluster.")
        return GraphRoutes.TOPIC_MANAGER_AGENT

    print("Decision: End conversation.")
    return GraphRoutes.END
