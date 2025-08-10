from langchain_core.messages import AIMessage, ToolMessage
import json, uuid

from agentic_network.core import AgentState


class ToolParser:
    def get_node(self, state: AgentState) -> AgentState:
        """
        Parses a tool call from the model's text content and ensures it has a name, args, and id.
        """
        print("--- Parsing potential tool calls ---")
        last_message = state["all_dialog"][-1]

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

                state["all_dialog"][-1] = new_message

            except (json.JSONDecodeError, KeyError) as e:
                print(f"--- Failed to parse JSON from TOOL_CALL: {e} ---")

                state["all_dialog"].append(
                    ToolMessage(content=f"Error parsing tool call: {tool_call_str}", tool_call_id="error"))

        return {"all_dialog": state["all_dialog"]}
