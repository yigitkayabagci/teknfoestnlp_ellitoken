from __future__ import annotations

import json
from uuid import uuid4
from copy import copy
from typing import List, Dict, Sequence, Optional

from llm.llm_models.gemini_client import GeminiClient
from llm.llm_models.gemini_client import LlmClient

from langchain_core.messages import (
    BaseMessage,
    AIMessage,
    ToolMessage,
    SystemMessage,
    HumanMessage
)
from langchain_core.tools import BaseTool


class LlmAdapter:
    """
    A lightweight LangChain-style chat model that wraps your GeminiClient.

    Usage:
        chat = ChatGeminiAdapter(llm=GeminiClient(), verbose=True)
        chat_with_tools = chat.bind_tools([tool1, tool2])
        ai_msg = chat_with_tools.invoke(messages)

    Notes:
    - Produces AIMessage with structured tool_calls when your GeminiClient
      emits 'TOOL_CALL: {"name": "...", "args": {...}}'.
    - Maps ToolMessage -> 'user' message with a TOOL_RESULT prefix so your
      client/model can read tool outputs.
    """

    def __init__(
        self,
        llm: LlmClient,
        *,
        verbose: bool = False,
        tool_result_label: str = "TOOL_RESULT",
        auto_tool_system_prompt: bool = False,
        tool_call_template: Optional[str] = None,
    ):
        self.llm = llm
        self.verbose = verbose
        self.tool_result_label = tool_result_label
        self._bound_tools: List[BaseTool] = []
        self.auto_tool_system_prompt = auto_tool_system_prompt
        # Template for teaching the protocol if you want automatic prompting
        self.tool_call_template = tool_call_template or (
            "You may call tools. If you need a tool, respond ONLY with:\n"
            'TOOL_CALL: {"name":"<TOOL_NAME>","args":{...}}\n'
            f"After a tool runs, you'll receive a message like:\n"
            f"{self.tool_result_label} [<TOOL_NAME>]: {{...}}\n"
            "Use it to continue and then answer the user."
        )

    # -- LC-style API --------------------------------------------------------

    def bind_tools(self, tools: Sequence[BaseTool]) -> "LlmAdapter":
        """Return a shallow-copied adapter with tools bound."""
        new = copy(self)
        new._bound_tools = list(tools)
        return new

    def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        """
        LangChain-style invoke: takes LC messages, returns an AIMessage.
        """
        # Optionally prepend an auto system prompt describing tool protocol
        msgs_for_client = messages
        if self.auto_tool_system_prompt and self._bound_tools:
            tool_names = ", ".join(t.name for t in self._bound_tools)
            sys_text = self.tool_call_template + f"\nAvailable tools: {tool_names}"
            msgs_for_client = [SystemMessage(content=sys_text), *messages]

        client_msgs = self._lc_to_client_messages(msgs_for_client)
        result = self.llm.chat(client_msgs)

        if self.verbose:
            print("[LlmAdapter] -> client text:", result.get("text", ""))

            if result.get("tool_call"):
                print("[LlmAdapter] -> tool_call:", result["tool_call"])

        return self._client_result_to_ai_message(result)

    # Optional convenience so it can be used like a runnable
    __call__ = invoke

    # -- Internal mappers ----------------------------------------------------

    def _lc_to_client_messages(self, messages: List[BaseMessage]) -> List[Dict]:
        """
        Map LC messages -> [{role, content}] expected by LlmClient.
        """
        system_chunks: List[str] = []
        converted: List[Dict] = []

        for m in messages:
            if isinstance(m, SystemMessage):
                system_chunks.append(m.content)

            elif isinstance(m, HumanMessage):
                converted.append({"role": "user", "content": m.content})

            elif isinstance(m, AIMessage):
                if m.content:
                    converted.append({"role": "assistant", "content": m.content})
                # tool_calls already handled by LangGraph; we don't pass them back in.

            elif isinstance(m, ToolMessage):
                name = getattr(m, "name", None) or "tool"
                content = m.content if isinstance(m.content, str) else json.dumps(m.content, ensure_ascii=False)
                converted.append({
                    "role": "user",
                    "content": f"{self.tool_result_label} [{name}]: {content}",
                })

        if system_chunks:
            converted.insert(0, {"role": "system", "content": "\n".join(system_chunks)})

        return converted

    def _client_result_to_ai_message(self, result: Dict) -> AIMessage:
        """
        Map your client's result -> AIMessage (with structured tool_calls if present).
        """
        tc = result.get("tool_call")
        if tc:
            return AIMessage(
                content="",  # the action is in tool_calls
                tool_calls=[{
                    "name": tc["name"],
                    "args": tc.get("args", {}),
                    "id": str(uuid4()),
                }],
            )
        return AIMessage(content=result.get("text", ""))


# ---------------------- Minimal example ----------------------
# if __name__ == "__main__":
#     # Example only: you’d normally wire this into a LangGraph node.
#     from langchain_core.tools import tool
#     from langchain_core.messages import SystemMessage, HumanMessage
#
#
#     @tool
#     def get_weather_info(location: str) -> str:
#         """Fetches dummy weather information for a given location."""
#         print(f"--- Calling get_weather_info tool for {location} ---")
#         weather_conditions = [
#             {"condition": "Rainy", "temp_c": 15},
#             {"condition": "Clear", "temp_c": 25},
#             {"condition": "Windy", "temp_c": 20}
#         ]
#         data = weather_conditions[0]
#         print("Tool output:", f"Weather in {location}: {data['condition']}, {data['temp_c']}°C")
#         return f"Weather in {location}: {data['condition']}, {data['temp_c']}°C"
#
#     gemini = GeminiClient()
#     chat = LlmAdapter(llm=gemini, verbose=True).bind_tools([get_weather_info])
#
#     system_message = SystemMessage(content=(
#         "You are a helpful weather assistant. "
#         "If you need weather, respond ONLY with:\n"
#         'TOOL_CALL: {"name":"get_weather_info","args":{"location":"THE_LOCATION"}}\n'
#         "After a tool runs, you'll see a message like:\n"
#         "TOOL_RESULT [get_weather_info]: {...}\n"
#         "Use it to answer and add a clothing tip."
#     ))
#     user = HumanMessage(content="Ankara için hava nasıl?")
#
#     ai = chat.invoke([system_message, user])
#     print("AIMessage:", ai)
