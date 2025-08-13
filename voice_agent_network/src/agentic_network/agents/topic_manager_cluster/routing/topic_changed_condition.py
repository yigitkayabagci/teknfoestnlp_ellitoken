from agentic_network.core import AgentState
from agentic_network.agents.topic_manager_cluster.core import TopicManagerRoutes
from agentic_network.agents.topic_manager_cluster.routing.condition_util import clean_thoughts


def decide_topic_has_changed(agent_state: AgentState) -> TopicManagerRoutes:
    """Parses:
       - FINAL ANSWER: SAME TOPIC
       - FINAL ANSWER: DIFFERENT TOPIC
       - THOUGHT: anything...
   """
    ai_message = agent_state["thoughts"][-1].content.upper()

    if ai_message.find("FINAL ANSWER"):
        if ai_message.find("SAME"):
            clean_thoughts(agent_state)
            return TopicManagerRoutes.END

        elif ai_message.find("DIFFERENT"):
            clean_thoughts(agent_state)
            return TopicManagerRoutes.PRE_TOPICS_AGENT

    else: return TopicManagerRoutes.TOPIC_CHANGE_CHECKER_AGENT
