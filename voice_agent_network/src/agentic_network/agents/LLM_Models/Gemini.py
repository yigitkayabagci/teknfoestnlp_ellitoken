from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
import os
import json
import requests
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


class GeminiClient:
    """
    Minimal wrapper for Google Gemini (generateContent) REST API.
    - Builds proper payload from a list of {role, content} messages.
    - Supports a 'system' message via system_instruction.
    - Extracts model text safely.
    - Detects TOOL_CALL: {...} lines when you use the tool-call protocol in your system prompt.
    """

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None, timeout: int = 30):
        load_dotenv()  # will auto-discover .env in project
        self.api_key = api_key or os.getenv("GEMINI_KEY")
        self.url = endpoint or os.getenv("GEMINI_ENDPOINT")
        self.timeout = timeout
        if not self.api_key or not self.url:
            raise ValueError("Missing GEMINI_KEY or GEMINI_ENDPOINT")

        self.session = requests.Session()
        self.headers = {"Content-Type": "application/json"}

    # --- Public API ---------------------------------------------------------

    def chat(self, messages_json: List[Dict]) -> Dict:
        """
        Send a conversation (list of {role, content}) and return:
        {
          "text": <model_text_or_empty_string>,
          "raw": <full_response_json>,
          "tool_call": <dict_or_None_if_not_detected>
        }
        """
        payload = self._build_payload(messages_json)
        resp = self._post(payload)
        text = self._extract_text(resp)
        tool_call = self._maybe_parse_tool_call(text)
        return {"text": text, "raw": resp, "tool_call": tool_call}

    # --- Internals ----------------------------------------------------------

    def _build_payload(self, messages_json: List[Dict]) -> Dict:
        """
        Convert your messages into the Gemini REST payload.
        - 'system' becomes system_instruction
        - 'user' -> role 'user'
        - 'assistant' -> role 'model'
        """
        system_prompt, contents = self._split_messages(messages_json)

        payload = {"contents": contents}
        if system_prompt:
            payload["system_instruction"] = {"parts": [{"text": system_prompt}]}
        return payload

    def _split_messages(self, messages_json: List[Dict]) -> Tuple[Optional[str], List[Dict]]:
        system_prompt = None
        contents: List[Dict] = []

        for msg in messages_json:
            role = msg.get("role", "").lower()
            text = msg.get("content", "")

            if role == "system":
                system_prompt = text if system_prompt is None else (system_prompt + "\n" + text)
                continue

            if role == "user": mapped_role = "user"
            elif role in ("assistant", "model"): mapped_role = "model"
            else: mapped_role = "user"

            contents.append({
                "role": mapped_role,
                "parts": [{"text": text}]
            })

        return system_prompt, contents

    def _post(self, payload: Dict) -> Dict:
        r = self.session.post(
            self.url,
            params={"key": self.api_key},
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def _extract_text(self, resp: Dict) -> str:
        """
        Safely pull the first candidate text. Returns "" if missing.
        """
        try:
            candidates = resp.get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            # Concatenate all text parts if present
            texts = [p.get("text", "") for p in parts if "text" in p]
            return "".join(texts)
        except Exception:
            return ""

    def _maybe_parse_tool_call(self, text: str) -> Optional[Dict]:
        """
        Detect and parse: TOOL_CALL: {"name": "...", "args": {...}}
        Returns dict or None.
        """
        if not text:
            return None
        m = re.match(r'^TOOL_CALL:\s*(\{.*\})\s*$', text.strip(), flags=re.DOTALL)
        if not m:
            return None
        try:
            return json.loads(m.group(1))
        except Exception:
            return None

# EXAMPLE USAGE
#
# if __name__ == "__main__":
#     client = GeminiClient()  # Uses GEMINI_KEY and GEMINI_ENDPOINT from env
#
#     base_messages = [
#         {
#             "role": "system",
#             "content": """
#             You are a helpful weather assistant.
#             You can call tools to get weather information.
#             After getting the weather, provide a brief comment on what to wear.
#
#             You have access to one tool: get_weather_info.
#
#             If you need to call this tool to answer the user's question, you MUST respond with ONLY a single line in the following exact format:
#             TOOL_CALL: {"name": "get_weather_info", "args": {"location": "THE_LOCATION"}}
#
#             - Replace "THE_LOCATION" with the location you need to look up.
#             - Note the use of "args" for the arguments dictionary.
#             - Do NOT add any other text, explanation, or markdown formatting around this line.
#             - Your entire response must be ONLY the TOOL_CALL line.
#
#             If you do not need to call a tool, just respond to the user normally, and do not answer in the tool call format.
#             """.strip()
#         },
#         {"role": "user", "content": "Merhaba. Bana nasıl yardımcı olabilirsin?"},
#         {"role": "assistant", "content": "Merhaba! Hava durumunu öğrenmenize yardımcı olabilirim. Ne yapmak istersiniz?"},
#     ]
#
#     # Simple REPL
#     while True:
#         user_text = input("User prompt: ")
#         messages = base_messages + [{"role": "user", "content": user_text}]
#         response = client.chat(messages)
#
#         # Print raw text response (UTF-8 safe)
#         print(response["text"])
#
#         # If the model asked for a tool call, you'd handle it here:
#         if response["tool_call"]:
#             print(f"(Detected tool call) -> {response['tool_call']}")
