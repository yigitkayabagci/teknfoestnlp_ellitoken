from llm.llm_models.gemma_based_models import Gemma, MedGemma
from llm.core import Device


class LlmSingleton:
    def __init__(self):
        self.gemma_3_1b_it = Gemma(False, model_variant=Gemma.Variant.GEMMA_3_1B_IT, device_map=Device.CUDA)
        self.medgemma_27b_text_it = MedGemma(False, model_variant=MedGemma.Variant.MEDGEMMA_27B_TEXT_IT, device_map=Device.CUDA)


llmSingleton = LlmSingleton()
