from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import re
import json


class LlmClient(ABC):
    """
    Framework-agnostic base client for chat LLMs.

    Standard contract:
      chat(messages_json) -> {
        "text": str,         # primary model text (may be "")
        "raw": dict,         # raw provider response
        "tool_call": dict|None  # parsed {"name":..., "args": {...}} if model requested a tool
      }

    Subclasses must implement:
      - _build_payload(messages_json) -> provider request payload (dict)
      - _post(payload) -> provider raw response (dict)
      - _extract_text(resp) -> str

    Optionally override:
      - _maybe_parse_tool_call(text) if you use a different protocol
    """

    def __init__(self, *, tool_call_regex: Optional[str] = None):
        # Default protocol:  TOOL_CALL: {"name":"...","args":{...}}
        self._tool_call_re = re.compile(
            tool_call_regex or r'^TOOL_CALL:\s*(\{.*\})\s*$',
            flags=re.DOTALL,
        )

    # ---- Public API --------------------------------------------------------
    def chat(self, messages_json: List[Dict]) -> Dict:
        """
        Orchestrates: build -> post -> extract -> parse tool call.
        Subclasses usually don't override this.
        """
        payload = self._build_payload(messages_json)
        resp = self._post(payload)
        text = self._extract_text(resp) or ""
        tool_call = self._maybe_parse_tool_call(text)
        return {"text": text, "raw": resp, "tool_call": tool_call}

    # ---- Hooks to implement ------------------------------------------------
    @abstractmethod
    def _build_payload(self, messages_json: List[Dict]) -> Dict:
        raise NotImplementedError

    @abstractmethod
    def _post(self, payload: Dict) -> Dict:
        raise NotImplementedError

    @abstractmethod
    def _extract_text(self, resp: Dict) -> str:
        raise NotImplementedError

    # ---- Optional hook -----------------------------------------------------
    def parse_tool_call(self, text: str) -> Optional[Dict]:
        if not text: return None

        tool_call_re = re.compile(
            r'^TOOL_CALL:\s*(\{.*\})\s*$',
            flags=re.DOTALL,
        )

        m = tool_call_re.match(text.strip())
        if not m: return None

        try:
            return json.loads(m.group(1))

        except Exception:
            return None
