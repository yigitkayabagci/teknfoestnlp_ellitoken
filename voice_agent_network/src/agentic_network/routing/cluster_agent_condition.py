from typing import Literal
from agentic_network.core import AgentState
from langchain_core.messages import AIMessage


def cluster_agent_condition(agent_state: AgentState) -> Literal["diognosis", "appointment", "out_of_topic", "small_talk", "end"]:
    """Checks the last AI message for cluster agent calls and decides the next step."""
    print("--- Deciding next cluster agent ---")
    last_message = agent_state["all_dialog"][-1]
    message_content = last_message.content.strip()

    if not isinstance(last_message, AIMessage) or not message_content.startswith("CLUSTER AGENT: "):
        # TODO: We can make the Topic Manager Agent roll back to itself if it fails to call other agents
        print("No cluster agents were called by the AI.")
        print("Last Message:", last_message.content.strip())
        print("Decision: End conversation.")
        return "end"

    # if

    print("Decision: Call tools.")
    return "tools"

