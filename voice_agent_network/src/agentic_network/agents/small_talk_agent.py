from .cluster_agent import ClusterAgent
from agentic_network.core import AgentState
from llm.core.llm_singletons import llmSingleton
from llm.core.gemma_based_model_adapter import GemmaBasedModelAdapter
from agentic_network.core.topic_manager_util import get_messages_for_current_topic


class SmallTalkAgent(ClusterAgent):
    def __init__(self):
        pass

    # ---- Internal Methods --------------------------------------------------------
    def _get_node(self, agent_state: AgentState) -> dict:
        llm = llmSingleton.gemma_3_1b_it
        chat = GemmaBasedModelAdapter(llm)

        system_message = "You are part of an AI assistant designed to help users with medical conditions get diagnosed and get hospital appointments. Your task here is to answer to user's messages kindly and remind them you can help them with their hospital appointments."

        messages = [system_message]
        messages.extend(get_messages_for_current_topic(agent_state))
        chat.invoke(messages)

        return {}
