from agentic_network.core import AgentState


class ClusterAgent:
    def __call__(self, agent_state: AgentState) -> dict:
        return self.get_node(agent_state)

    def get_node(self, agent_state: AgentState) -> dict:
        return {}
