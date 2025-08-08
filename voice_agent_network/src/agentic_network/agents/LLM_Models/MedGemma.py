from voice_agent_network.src.agentic_network.agents.LLM_Models.Devices import Device
from transformers import (AutoProcessor, AutoModelForImageTextToText, BitsAndBytesConfig,
                          AutoModelForCausalLM, AutoTokenizer)
import torch
import os
from enum import Enum
from typing import List, Dict


class MedGemma:
    """
    A class to load MedGemma models and their corresponding processors/tokenizers.
    The loaded model and processor are available as instance variables.
    """

    class Variant(Enum):
        """
        Represents different MedGemma model variants.

        NOTE: These are assumed to be local folder names in the 'medgemma_models' directory.
        """
        MEDGEMMA_4B_IT = "medgemma_models/medgemma-4b-it"
        MEDGEMMA_27B_IT = "medgemma_models/medgemma-27b-it"
        MEDGEMMA_27B_TEXT_IT = "medgemma_models/medgemma-27b-text-it"

    def __init__(self,
                 use_quantized: bool,
                 is_thinking: bool = False,
                 device_map: Device = Device.AUTO,
                 model_variant: Variant = Variant.MEDGEMMA_4B_IT):

        # We store the variant and device as instance variables
        self.model_variant = model_variant
        self.device_map = device_map
        self.folder_path = os.path.join(os.getcwd(), "../src/agentic_network/agents/LLM_Models/")
        self.folder_path += self.model_variant.value
        self.folder_path = os.path.normpath(self.folder_path)

        self.model = self._load_model(use_quantized)
        self.processor = self._load_processor()

        # A dictionary to hold generation parameters, which can be easily updated.
        self.model_settings = dict(max_new_tokens=400,
                                   do_sample=False,
                                   temp=None,
                                   top_p=None,
                                   top_k=None)

    def _load_model(self, use_quantized: bool):
        """
        Loads the MedGemma model from a local directory.
        Quantizes the model to 4-bit if `use_quantized` is True.
        """
        quantization_config = BitsAndBytesConfig(load_in_4bit=True) if use_quantized else None

        # Determine which model class to use based on the model variant name
        if "text" in self.model_variant.value:
            model = AutoModelForCausalLM.from_pretrained(
                self.folder_path,
                torch_dtype=torch.bfloat16,
                device_map=self.device_map.value,
                quantization_config=quantization_config
            )
        else:
            model = AutoModelForImageTextToText.from_pretrained(
                self.folder_path,
                torch_dtype=torch.bfloat16,
                device_map=self.device_map.value,
                quantization_config=quantization_config
            )

        return model

    def _load_processor(self):
        """
        Loads the appropriate processor or tokenizer for the model variant.
        """
        # Use .value to get the string from the Enum
        if "text" in self.model_variant.value:
            processor = AutoTokenizer.from_pretrained(self.folder_path)
        else:
            processor = AutoProcessor.from_pretrained(self.folder_path)

        return processor

    def set_model_settings(self,
                           max_new_tokens: int = None,
                           do_sample: bool = None,
                           temp: float = None,
                           top_p: float = None,
                           top_k: int = None):
        """
        Updates the model settings with the provided values.

        Args:
            max_new_tokens (int): The maximum number of new tokens to generate.
            do_sample (bool): Whether to use sampling for generation.
            temp (float): The sampling temperature.
            top_p (float): The nucleus sampling probability.
            top_k (int): The number of top tokens to consider.
        """
        # Collect all the provided arguments into a local dictionary
        provided_args = locals()

        # Iterate through the arguments and update the settings if they are not None
        for key, value in provided_args.items():
            if key != 'self' and value is not None:
                self.model_settings[key] = value

    def give_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Processes chat messages and generates a text response from the model.

        Args:
            messages (List[Dict[str, str]]): A list of dictionaries representing the chat history.

        Returns:
            str: The generated text response.
        """
        # Prepares the messages into a format the model understands
        inputs = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.model.device)

        input_len = inputs["input_ids"].shape[-1]

        # Disables gradient calculations for faster inference
        with torch.inference_mode():
            # **self.model_settings dynamically unpacks the dictionary for model generation
            generation = self.model.generate(**inputs, **self.model_settings)
            generation = generation[0][input_len:]

        # Decodes the generated token IDs back into a readable string
        response = self.processor.decode(generation, skip_special_tokens=True)
        return response