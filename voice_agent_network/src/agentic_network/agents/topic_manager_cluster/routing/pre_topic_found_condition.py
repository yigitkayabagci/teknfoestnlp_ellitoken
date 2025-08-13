import uuid

from agentic_network.core import AgentState
from agentic_network.agents.topic_manager_cluster.core import TopicManagerRoutes
from agentic_network.agents.topic_manager_cluster.routing.condition_util import strip_braces, clean_thoughts
from agentic_network.core.topic_manager_util import find_topic_index, resurface_topic


def _is_valid_uuid(value, version=4):
    try:
        uuid_obj = uuid.UUID(value, version=version)

    except ValueError:
        return False

    return str(uuid_obj) == value.lower()


def decide_pre_topic_found(agent_state: AgentState) -> TopicManagerRoutes:
    """Parses:
       - FINAL ANSWER: [topic_id]
       - FINAL ANSWER: NEW TOPIC
       - THOUGHT: anything...
   """
    ai_message = agent_state["all_dialog"][-1].content.upper()  # TODO: this should change to thought dialog

    if ai_message.find("FINAL ANSWER"):
        if ai_message.find("NEW"):
            clean_thoughts(agent_state)
            return TopicManagerRoutes.NEW_TOPIC_AGENT

        else:
            topic_id = ai_message.split("FINAL ANSWER:")[1].strip()
            topic_id = strip_braces(topic_id)
            topic_id = topic_id.lower()

            if not _is_valid_uuid(topic_id): return TopicManagerRoutes.PRE_TOPICS_AGENT  # TODO: add the thought that the topic_id is not a valid uuid
            if find_topic_index(agent_state, topic_id): return TopicManagerRoutes.PRE_TOPICS_AGENT  # TODO: add the thought that the topic_id cannot be found

            resurface_topic(agent_state, topic_id)
            clean_thoughts(agent_state)
            return TopicManagerRoutes.END

    else: return TopicManagerRoutes.PRE_TOPICS_AGENT
