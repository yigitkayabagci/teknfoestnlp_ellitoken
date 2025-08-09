from __future__ import annotations
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from llm.LlmClient import LlmClient
import os
import requests
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")

except Exception:
    pass


class GeminiClient(LlmClient):
    """
    Minimal wrapper for Google Gemini (generateContent) REST API,
    implemented on top of AIClient.
    """

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None, timeout: int = 30, **kwargs):
        # kwargs lets you pass tool_call_regex=... if you customize the protocol
        super().__init__(**kwargs)

        load_dotenv()
        self.api_key = api_key or os.getenv("GEMINI_KEY")
        self.url = endpoint or os.getenv("GEMINI_ENDPOINT")
        self.timeout = timeout

        if not self.api_key or not self.url:
            raise ValueError("Missing GEMINI_KEY or GEMINI_ENDPOINT")

        self.session = requests.Session()
        self.headers = {"Content-Type": "application/json"}

    # --- AIClient hooks -----------------------------------------------------

    def _build_payload(self, messages_json: List[Dict]) -> Dict:
        """
        Convert messages into the Gemini REST payload.
        - 'system' -> system_instruction
        - 'user'   -> role 'user'
        - 'assistant'/'model' -> role 'model'
        """
        system_prompt, contents = self._split_messages(messages_json)

        payload = {"contents": contents}
        if system_prompt: payload["system_instruction"] = {"parts": [{"text": system_prompt}]}

        return payload

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
            if not candidates: return ""

            parts = candidates[0].get("content", {}).get("parts", [])
            texts = [p.get("text", "") for p in parts if "text" in p]

            return "".join(texts)

        except Exception:
            return ""

    # --- Internals ----------------------------------------------------------

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
