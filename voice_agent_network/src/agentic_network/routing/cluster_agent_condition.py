from langchain_core.messages import AIMessage
from agentic_network.core import AgentState, GraphRoutes


def decide_cluster_agent(agent_state: AgentState) -> GraphRoutes:
    """Checks the last AI message for cluster agent calls and decides the next step."""
    print("--- Deciding next cluster agent ---")
    last_message = agent_state["all_dialog"][-1]
    message_content = last_message.content.strip()

    if not isinstance(last_message, AIMessage) or not message_content.startswith("CALL CLUSTER AGENT: "):
        # TODO: We can make the Topic Manager Agent roll back to itself if it fails to call other agents
        print("ERROR: No cluster agents were called by the AI.")
        print("Last Message:", last_message.content.strip())
        print("Decision: End conversation.")
        return GraphRoutes.END

    cluster_agent = message_content.split("CALL CLUSTER AGENT: ")[1].upper()

    if cluster_agent == GraphRoutes.DIAGNOSIS_AGENT:
        print("Decision: Call Diognosis Agent.")
        return GraphRoutes.DIAGNOSIS_AGENT

    elif cluster_agent == GraphRoutes.APPOINTMENT_AGENT:
        print("Decision: Call Appointment Agent.")
        return GraphRoutes.APPOINTMENT_AGENT

    elif cluster_agent == GraphRoutes.SMALL_TALK:
        print("Decision: Call Small Talk Agent.")
        return GraphRoutes.DIAGNOSIS_AGENT

    elif cluster_agent == GraphRoutes.OUT_OF_TOPIC:
        print("Decision: Call Out Of Topic Agent.")
        return GraphRoutes.DIAGNOSIS_AGENT

    else:
        print("ERROR: No cluster agents were called by the AI.")
        print("Last Message:", last_message.content.strip())
        print("Decision: End conversation.")
        return GraphRoutes.END
