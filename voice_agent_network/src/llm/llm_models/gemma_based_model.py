from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict


class GemmaBasedModel:
    @abstractmethod
    def give_prompt(self, messages: List[Dict[str, str]]) -> str:
        raise NotImplementedError
