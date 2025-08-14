from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from typing import List

from llm.llm_models import GemmaBasedModel


# Assume your Gemma class is defined elsewhere
# from llm.llm_models.gemma import Gemma

# The custom wrapper class, now with full message type support
class GemmaBasedModelAdapter:
    """
    A LangChain-compatible wrapper for the custom Gemma client.
    Handles System, Human, AI, and Tool message types.
    """
    def __init__(self, gemma_based_model: GemmaBasedModel):
        self.gemma_based_client = gemma_based_model

    def invoke(self, messages: List[BaseMessage], stop: List[str] | None = None, **kwargs) -> str:
        """
        The core method that LangChain will invoke.
        """
        prompt_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                role = 'system'
            elif isinstance(msg, HumanMessage):
                role = 'user'
            elif isinstance(msg, AIMessage):
                role = 'assistant'
            else:
                raise ValueError(f"Unsupported message type: {type(msg).__name__}")

            prompt_messages.append({"role": role, "content": [{"type": "text", "text": msg.content}]})

        response = self.gemma_based_client.give_prompt(prompt_messages)
        return response
