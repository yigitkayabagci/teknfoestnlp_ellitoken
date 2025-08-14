# client.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import re
import json
import requests


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
    def _maybe_parse_tool_call(self, text: str) -> Optional[Dict]:
        if not text: return None

        # Regex to handle optional markdown (**) and more flexible whitespace
        # It tries to find 'TOOL_CALL:' followed by an optional markdown, then captures the JSON object.
        m = re.search(r'(?:\*\*|\s*)TOOL_CALL:\s*(\*\*?\{.*?\})', text.strip(), flags=re.DOTALL)
        if not m:
            # Fallback to the original, stricter regex if the more flexible one fails
            m = self._tool_call_re.match(text.strip())
            if not m:
                return None

        try:
            # Extract the captured group which should contain the JSON string
            json_str = m.group(1).strip()
            # Remove any remaining asterisks around the JSON string if present
            json_str = json_str.strip('*')
            return json.loads(json_str)

        except Exception as e:
            print(f"Araç çağrısı JSON'ı ayrıştırılırken hata oluştu: {e} metinden: {text}")
            return None


# now, this class is arranged according to llama3, but you can change the model at line 126
class GeneralLlmClient(LlmClient):
    """
    Concrete implementation of LlmClient for Ollama.
    """
    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        super().__init__()
        self.model = model
        self.base_url = base_url

    def _build_payload(self, messages_json: List[Dict]) -> Dict:
        return {
            "model": self.model,
            "messages": messages_json,
            "stream": False,
        }

    def _post(self, payload: Dict) -> Dict:
        url = f"{self.base_url}/api/chat"
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()  # HTTP hatalarını kontrol et
            return response.json()
        except requests.exceptions.RequestException as e:
            # Daha açıklayıcı hata mesajları
            raise ConnectionError(f"Ollama'ya bağlanılamadı: {e}. Lütfen Ollama'nın çalıştığından ve modelin yüklü olduğundan emin olun.") from e

    def _extract_text(self, resp: Dict) -> str:
        # Ollama'dan dönen yanıttaki metni çıkar
        # Yanıt formatı: {"model": "...", "created_at": "...", "message": {"role": "...", "content": "..."}}
        return resp.get("message", {}).get("content", "")

# --- KULLANIM ÖRNEĞİ (Test için) ---
if __name__ == "__main__":

    # İstemciyi başlatma
    client = GeneralLlmClient(model="llama3")

    # Örnek mesajlar
    messages_to_llm = [
        {"role": "system", "content": "Sen bir randevu asistanısın."},
        {"role": "user", "content": "Merhaba, nasılsın?"}
    ]

    try:
        # Sohbet başlatma
        response = client.chat(messages_to_llm)
        print("Modelden Gelen Yanıt:")
        print(f"Metin: {response['text']}")
        print(f"Araç Çağrısı: {response['tool_call']}")
        print("---")

        # Araç çağırma örneği için bir başka mesaj
        tool_call_message = [
            {"role": "system", "content": "Sadece araçları kullan. Eğer bir hastane aramam gerekirse TOOL_CALL: {'name':'get_hospitals_by_location', 'args':{'location':'Ankara'}} şeklinde yanıt ver."},
            {"role": "user", "content": "Ankara'daki hastaneleri bul."}
        ]
        response_with_tool = client.chat(tool_call_message)
        print("Modelden Gelen Araç Çağrısı Yanıtı:")
        print(f"Metin: {response_with_tool['text']}")
        print(f"Araç Çağrısı: {response_with_tool['tool_call']}")

    except ConnectionError as e:
        print(f"Hata: {e}")