import random
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain.tools import Tool
from langgraph.graph.message import add_messages
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode

from llm import LlmAdapter
from llm.llm_models import GeminiClient
import json, uuid


def main():
    # declare tools
    @tool
    def get_weather_info(location: str) -> str:
        """Fetches dummy weather information for a given location."""
        print(f"--- Calling get_weather_info tool for {location} ---")
        weather_conditions = [
            {"condition": "Rainy", "temp_c": 15},
            {"condition": "Clear", "temp_c": 25},
            {"condition": "Windy", "temp_c": 20}
        ]
        data = random.choice(weather_conditions)
        print("Tool output:", f"Weather in {location}: {data['condition']}, {data['temp_c']}°C")
        return f"Weather in {location}: {data['condition']}, {data['temp_c']}°C"

    # initialize the tool
    weather_info_tool = Tool(
        name="get_weather_info",
        func=get_weather_info,
        description="Fetches dummy weather information for a given location."
    )

    # declare llm
    llm = GeminiClient()
    tools = [get_weather_info]
    chat = LlmAdapter(llm=llm, verbose=True).bind_tools(tools)

    # declare the state
    class AgentState(TypedDict):
        messages: Annotated[list[AnyMessage], add_messages]

    # declare nodes
    def assistant(state: AgentState):
        # System message
        textual_description_of_tool = """
            You have access to one tool: `get_weather_info`.

            If you need to call this tool to answer the user's question, you MUST respond with ONLY a single line in the following exact format:
            TOOL_CALL: {"name": "get_weather_info", "args": {"location": "THE_LOCATION"}}

            - Replace "THE_LOCATION" with the location you need to look up.
            - Note the use of "args" for the arguments dictionary.
            - Do NOT add any other text, explanation, or markdown formatting around this line.
            - Your entire response must be ONLY the TOOL_CALL line.

            If you do not need to call a tool, just respond to the user normally.
            """

        sys_msg = SystemMessage(
            content=(
                "You are a helpful weather assistant. "
                "You can call tools to get weather information. "
                "After getting the weather, provide a brief comment on what to wear."
                f"\n{textual_description_of_tool}\n"
            )
        )

        # print(f"\n\n{[sys_msg] + state["messages"]}\n\n")

        return {
            "messages": [chat.invoke([sys_msg] + state["messages"])],
        }

    def tool_transformer(state: AgentState) -> dict:
        """
        Parses a tool call from the model's text content and ensures it has a name, args, and id.
        """
        print("--- Transforming potential tool calls ---")
        last_message = state["messages"][-1]

        if isinstance(last_message, AIMessage) and last_message.content.strip().startswith("TOOL_CALL:"):
            print("--- Tool call detected ---")
            tool_call_str = last_message.content.strip().replace("TOOL_CALL:", "", 1).strip()
            try:
                tool_call_data = json.loads(tool_call_str)

                if "arguments" in tool_call_data:
                    tool_call_data["args"] = tool_call_data.pop("arguments")

                tool_call_data["id"] = f"tool_{uuid.uuid4()}"

                new_message = AIMessage(
                    content="",
                    tool_calls=[tool_call_data],
                    # The message ID is distinct from the tool call ID
                    id=last_message.id,
                )
                print(f"--- Transformed message to: {new_message} ---")

                state["messages"][-1] = new_message
            except (json.JSONDecodeError, KeyError) as e:
                print(f"--- Failed to parse JSON from TOOL_CALL: {e} ---")
                state["messages"].append(
                    ToolMessage(content=f"Error parsing tool call: {tool_call_str}", tool_call_id="error"))

        return {"messages": state["messages"]}

    # routing function
    def decide_tools(state: AgentState) -> str:
        """Checks the last AI message for tool calls and decides the next step."""
        print("--- Deciding next step ---")
        last_message = state["messages"][-1]

        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            print("Decision: Call tools.")
            return "tools"

        print("Decision: End conversation.")
        return END

    # build the graph
    builder = StateGraph(AgentState)
    builder.add_node("assistant", assistant)
    builder.add_node("tool_transformer", tool_transformer)  # Add the new node
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "assistant")
    # The assistant's output now goes to the transformer first
    builder.add_edge("assistant", "tool_transformer")

    # The transformer's output goes to the router
    builder.add_conditional_edges(
        "tool_transformer",
        decide_tools,
        {"tools": "tools", END: END},
    )
    builder.add_edge("tools", "assistant")
    graph = builder.compile()

    # Run the AI
    while True:
        prompt = input("Prompt (or 'quit' to exit): ")
        if prompt.lower() == 'quit':
            break
        messages = [HumanMessage(content=prompt)]
        response = graph.invoke({"messages": messages})

        print("\n" + "=" * 34 + " FINAL RESPONSE " + "=" * 34)
        final_message = response['messages'][-1]
        final_message.pretty_print()
        print("=" * 58 + "\n")


# print("response:", response)
# for m in response["messages"]:
#     print(type(m), m)

# display the network
# display(Image(graph.get_graph().draw_mermaid_png()))

if __name__ == "__main__":
    main()
