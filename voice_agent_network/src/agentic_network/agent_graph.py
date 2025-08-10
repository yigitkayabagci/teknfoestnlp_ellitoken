from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import StateGraph

from agentic_network.agents import ClusterAgent, TopicManagerAgent, DiognosisAgent, AppointmentAgent, SmallTalkAgent, \
    OutOfTopicAgent
from agentic_network.core import AgentState, GraphRoutes
from agentic_network.routing import decide_cluster_agent, decide_topic_manager


class AgentGraph:
    """Orchestrates the agent network as a LangGraph state machine.

    This class wires up agent nodes, connects them with edges, and compiles a
    runnable graph. Routing between nodes is delegated to the `decide_*`
    functions imported from `agentic_network.routing`.
    """

    # The compiled, runnable graph (set in _build_graph)
    graph: CompiledStateGraph = None

    # Concrete agent instances (all share a common base: ClusterAgent)
    topic_manager_agent: ClusterAgent = None
    diagnosis_agent: ClusterAgent = None
    appointment_agent: ClusterAgent = None
    small_talk_agent: ClusterAgent = None
    out_of_topic_agent: ClusterAgent = None

    def __init__(self):
        """Create agents and build the graph once."""
        self._initialize_agents()
        self._build_graph()

    # ---- Public API --------------------------------------------------------------
    def invoke(self, state: AgentState):
        """Run the compiled graph."""
        self.graph.invoke(state=state)

    # ---- Internal Methods --------------------------------------------------------
    def _initialize_agents(self) -> None:
        """Instantiate concrete agent nodes.

        Each agent should implement the callable interface expected by LangGraph
        (i.e., accept and return the `AgentState` mapping or compatible object).
        """
        self.topic_manager_agent = TopicManagerAgent()
        self.diagnosis_agent = DiognosisAgent()
        self.appointment_agent = AppointmentAgent()
        self.small_talk_agent = SmallTalkAgent()
        self.out_of_topic_agent = OutOfTopicAgent()

    def _build_graph(self) -> None:
        """Declare nodes, edges, and routing, then compile the graph.

        Structure:
            - Nodes: one per agent.
            - Start edge: START → Topic Manager.
            - Conditional edges:
                * From Topic Manager → a specific cluster agent or end,
                  decided by `decide_cluster_agent`.
                * From Diagnosis/Appointment → either loop back to Topic Manager
                  or end, decided by `decide_topic_manager`.

        Notes:
            - `GraphRoutes` values are used as node identifiers to keep routing
              consistent and type-safe across the codebase.
            - `AgentState` is the shared mutable state carried across nodes.
        """
        # Initialize a typed state graph; all node callables must accept&return AgentState
        graph_builder = StateGraph(AgentState)

        # ---------------------- Nodes -------------------------------------------------
        # Register each agent under a stable route key from GraphRoutes.
        graph_builder.add_node(GraphRoutes.TOPIC_MANAGER_AGENT, self.topic_manager_agent)
        graph_builder.add_node(GraphRoutes.DIAGNOSIS_AGENT, self.diagnosis_agent)
        graph_builder.add_node(GraphRoutes.APPOINTMENT_AGENT, self.appointment_agent)
        graph_builder.add_node(GraphRoutes.SMALL_TALK, self.small_talk_agent)
        graph_builder.add_node(GraphRoutes.OUT_OF_TOPIC, self.out_of_topic_agent)

        # ---------------------- Linear Edge(s) ----------------------------------------
        # Entry point: start the graph at Topic Manager.
        graph_builder.add_edge(GraphRoutes.START, GraphRoutes.TOPIC_MANAGER_AGENT)

        # ---------------------- Conditional Routing -----------------------------------
        # 1) Topic Manager decides which specialized cluster agent should handle the turn.
        #    `decide_cluster_agent(state: AgentState) -> A Cluster Agent | END`
        graph_builder.add_conditional_edges(
            GraphRoutes.TOPIC_MANAGER_AGENT,
            decide_cluster_agent
        )
        # 2) After specialized handling, decide whether to loop back to the Topic Manager
        #    (to reach another agent) or finish. Both diagnosis and appointment reuse
        #    the same router for that decision.
        #    `decide_topic_manager(state: AgentState) -> GraphRoutes.TOPIC_MANAGER_AGENT | END`
        graph_builder.add_conditional_edges(
            GraphRoutes.DIAGNOSIS_AGENT,
            decide_topic_manager,
        )
        graph_builder.add_conditional_edges(
            GraphRoutes.APPOINTMENT_AGENT,
            decide_topic_manager,
        )

        # ---------------------- Compile -----------------------------------------------
        # Finalize the graph into a runnable pipeline.
        self.graph = graph_builder.compile()
