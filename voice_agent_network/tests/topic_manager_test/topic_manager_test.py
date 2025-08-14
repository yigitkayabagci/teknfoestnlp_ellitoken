from langchain_core.messages import AnyMessage
from agentic_network.agents.topic_manager_cluster.topic_manager_cluster import TopicManagerCluster
from agentic_network.core import AgentState

def main():
    topic_manager = TopicManagerCluster()

    all_dialog: list[AnyMessage] = []
    new_message: str = ""

    agent_state["current_message"] = "Merhaba, ben böbrek ağrılarımdan dolayı aradım."

    print(topic_manager.graph.invoke({"current_message"}))



if __name__ == "__main__":
    main()
