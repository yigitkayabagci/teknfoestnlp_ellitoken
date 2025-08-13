from langchain_core.messages import AIMessage
from agentic_network.core import AgentState, GraphRoutes
from agentic_network.core.topic_manager_util import get_current_topic


def decide_cluster_agent(agent_state: AgentState) -> GraphRoutes:
    """Checks the cluster agent calls and decides the next step."""
    print("--- Deciding next cluster agent ---")

    current_topic = get_current_topic(agent_state)
    if not current_topic or current_topic["agent"] == "":
        # TODO: We can make the Topic Manager Agent roll back to itself if it fails to call other agents
        print("ERROR: No cluster agents were called by the AI.")
        print("Decision: End conversation.")
        return GraphRoutes.END

    cluster_agent = current_topic["agent"]

    if cluster_agent == GraphRoutes.DIAGNOSIS_AGENT:
        print("Decision: Call Diagnosis Agent.")
        return GraphRoutes.DIAGNOSIS_AGENT

    elif cluster_agent == GraphRoutes.APPOINTMENT_AGENT:
        print("Decision: Call Appointment Agent.")
        return GraphRoutes.APPOINTMENT_AGENT

    elif cluster_agent == GraphRoutes.SMALL_TALK_AGENT:
        print("Decision: Call Small Talk Agent.")
        return GraphRoutes.DIAGNOSIS_AGENT

    elif cluster_agent == GraphRoutes.OUT_OF_TOPIC_AGENT:
        print("Decision: Call Out Of Topic Agent.")
        return GraphRoutes.DIAGNOSIS_AGENT

    else:
        # TODO: We can make the Topic Manager Agent roll back to itself if it fails to call other agents
        print("ERROR: No cluster agents were called by the AI.")
        print("Decision: End conversation.")
        return GraphRoutes.END
