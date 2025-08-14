from langchain_core.messages import SystemMessage, HumanMessage

from llm.core import Device
from llm.core.gemma_adapter import GemmaAdapter
from llm.llm_models.gemma_based_models import MedGemma

llm = MedGemma(False, is_thinking=False, model_variant=MedGemma.Variant.MEDGEMMA_4B_IT, device_map=Device.AUTO)
adapter = GemmaAdapter(llm)
print(adapter.invoke([SystemMessage("You are a master cardiologist. Top of your class."), HumanMessage("Who are you? Can you tell me about the most recent advancements in your field?")]))
