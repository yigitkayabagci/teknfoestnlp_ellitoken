from langchain_core.messages import SystemMessage, HumanMessage

from agentic_network.agents.topic_manager_cluster.agents import TopicAgent
from agentic_network.core import AgentState
from llm.llm_models import GeminiClient
from llm.core import LlmAdapter


class TopicChangeCheckerAgent(TopicAgent):
    system_message = SystemMessage(
        content=(
            "You are a helpful weather assistant. "
            "You can call tools to get weather information. "
            "After getting the weather, provide a brief comment on what to wear."
            # f"\n{textual_description_of_tool}\n"
        )
    )

    def __init__(self):
        pass

    # ---- Internal Methods --------------------------------------------------------
    def _get_node(self, agent_state: AgentState) -> dict:
        pass

        llm = GeminiClient()
        chat = LlmAdapter(llm=llm, verbose=True)

        return {
            "messages": [chat.invoke([self.system_message] + agent_state["all_dialog"])],
        }

# Run the AI
agent = TopicChangeCheckerAgent()
while True:
    prompt = input("Prompt (or 'quit' to exit): ")
    if prompt.lower() == 'quit': break

    messages = [HumanMessage(content=prompt)]
    response = agent({"all_dialog": messages})

    print("\n" + "=" * 34 + " FINAL RESPONSE " + "=" * 34)
    final_message = response['messages'][-1]
    final_message.pretty_print()
    print("=" * 58 + "\n")
