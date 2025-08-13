from agentic_network.core import AgentState
from agentic_network.core import GraphRoutes
from agentic_network.agents.topic_manager_cluster.core import TopicManagerRoutes
from agentic_network.agents.topic_manager_cluster.routing.condition_util import strip_braces, clean_thoughts
from agentic_network.core.topic_manager_util import create_topic


_allowed_agents = {
        GraphRoutes.DIAGNOSIS_AGENT,
        GraphRoutes.APPOINTMENT_AGENT,
        GraphRoutes.SMALL_TALK_AGENT,
        GraphRoutes.OUT_OF_TOPIC_AGENT,
    }


def _strip_prefix_graphroutes(s: str) -> str:
    # Accept GraphRoutes.<NAME> (case-insensitive)
    if "." in s:
        left, right = s.split(".", 1)
        if left.strip().lower() == "graphroutes":
            return right.strip()
    return s.strip()


def _parse_router_output(agent_state: AgentState, text: str) -> bool:
    """Parses:
       - FINAL ANSWER: {GraphRoutes.NAME}
       - FINAL ANSWER: NAME
       - THOUGHT: anything...
       Returns FINAL / THOUGHT / MALFORMED without using regex.
    """
    text = (text or "").strip()
    text = text.upper()

    # FINAL ANSWER: ...
    if text.find("FINAL ANSWER"):
        route = text.split("FINAL ANSWER:")[1].strip()
        route = strip_braces(route)
        route = _strip_prefix_graphroutes(route)
        route = route.upper()

        if route in _allowed_agents:
            create_topic(agent_state, GraphRoutes[route])
            return True

        return False


def decide_new_topic_found(agent_state: AgentState) -> TopicManagerRoutes:
    ai_message = agent_state["thoughts"][-1].content
    new_topic_is_found = _parse_router_output(agent_state, ai_message)

    if new_topic_is_found:
        clean_thoughts(agent_state)
        return TopicManagerRoutes.END

    return TopicManagerRoutes.NEW_TOPIC_AGENT
