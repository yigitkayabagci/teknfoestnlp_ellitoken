from .cluster_agent import ClusterAgent
from agentic_network.core import AgentState


class OutOfTopicAgent(ClusterAgent):
    def __init__(self):
        pass

    # ---- Internal Methods --------------------------------------------------------
    def _get_node(self, agent_state: AgentState) -> dict:
        pass

        return {}
