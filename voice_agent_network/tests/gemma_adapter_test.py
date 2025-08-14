from langchain_core.messages import SystemMessage, HumanMessage

from llm.core import Device
from llm.core.gemma_adapter import GemmaAdapter
from llm.llm_models.gemma_based_models import Gemma

llm = Gemma(False, is_thinking=False, model_variant=Gemma.Variant.GEMMA_3_1B_IT, device_map=Device.AUTO)
adapter = GemmaAdapter(llm)
print(adapter.invoke([SystemMessage("You are a merchant in the populer mmo game Metin2. Answer every message in Turkish."), HumanMessage("Who are you?")]))
