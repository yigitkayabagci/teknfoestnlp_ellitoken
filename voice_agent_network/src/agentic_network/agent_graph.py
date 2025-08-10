from langgraph.graph import START, END, StateGraph

from agentic_network.agents import ClusterAgent, TopicManagerAgent, DiognosisAgent, AppointmentAgent
from agentic_network.core import AgentState


class AgentGraph:
    topic_manager_agent: ClusterAgent = None
    diognosis_agent: ClusterAgent = None
    appointment_agent: ClusterAgent = None

    def __init__(self):
        self.initialize_agents()
        self.build_graph()

    def initialize_agents(self) -> None:
        self.topic_manager_agent = TopicManagerAgent()
        self.diognosis_agent = DiognosisAgent()
        self.appointment_agent = AppointmentAgent()

    def build_graph(self) -> None:
        builder = StateGraph(AgentState)

        # Add the nodes
        builder.add_node("topic_manager_agent", self.topic_manager_agent)
        builder.add_node("diognosis_agent", self.diognosis_agent)
        builder.add_node("appointment_agent", self.appointment_agent)

        # builder.add_edge(START, "topic_manager_agent")
        #
        # # The transformer's output goes to the router
        # builder.add_conditional_edges(
        #     "tool_parser",
        #     decide_tools,
        #     {"tools": "tools", "end": END},
        # )
        # builder.add_edge("tools", "assistant")
