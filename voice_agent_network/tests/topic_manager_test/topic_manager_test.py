from langchain_core.messages import AnyMessage
from agentic_network.agents.topic_manager_cluster.topic_manager_cluster import TopicManagerCluster
from agentic_network.core import AgentState


def main():
    topic_manager = TopicManagerCluster()

    all_dialog: list[AnyMessage] = []
    current_message: str = "Merhaba."

    agent_state: AgentState = {
        "current_message": current_message,
        "all_dialog": all_dialog,
        "topic_stack": [],
        "disclosed_topics": []
    }

    print(topic_manager.graph.invoke(agent_state))


if __name__ == "__main__":
    main()
