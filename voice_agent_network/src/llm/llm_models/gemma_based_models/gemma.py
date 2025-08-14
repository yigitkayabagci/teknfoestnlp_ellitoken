from llm.core.devices import Device
from transformers import (BitsAndBytesConfig, AutoModelForCausalLM, AutoTokenizer, AutoModel)
from llama_cpp import Llama
import accelerate
import torch
import os
from enum import Enum
from typing import List, Dict

from llm.llm_models import GemmaBasedModel


class Gemma(GemmaBasedModel):
    """
    A class to load Gemma models and their corresponding tokenizers.
    The loaded model and tokenizer are available as instance variables.
    """

    class Variant(Enum):
        """
        Represents different Gemma model variants.

        Each tuple contains the folder name and a flag indicating if it's a GGUF model.
        The folder names are assumed to be local paths inside the 'gemma_models' directory.
        """
        GEMMA_3_1B_IT_QAT_Q4_0_GGUF = ("google/gemma-3-1b-it-qat-q4_0-gguf", True)
        GEMMA_3_1B_IT_QAT_Q4_0_UNQUANTIZED = ("google/gemma-3-1b-it-qat-q4_0-unquantized", False)
        GEMMA_3_1B_IT = ("google/gemma-3-1b-it", False)
        GEMMA_3_4B_IT = ("google/gemma-3-4b-it", False)
        GEMMA_3_12B_IT = ("google/gemma-3-12b-it", False)
        GEMMA_3_12B_IT_QAT_Q4_0_GGUF = ("google/gemma-3-12b-it-qat-q4_0-gguf", True)
        GEMMA_3_12B_IT_QAT_Q4_0_UNQUANTIZED = ("google/gemma-3-12b-it-qat-q4_0-unquantized", False)

        @property
        def _is_gguf(self):
            """Returns True if the variant is a GGUF model."""
            return self.value[1]

        @property
        def _folder_name(self):
            """Returns the local folder name for the model."""
            return self.value[0]


    def __init__(self,
                 use_quantized: bool,
                 is_thinking: bool = False,
                 device_map: Device = Device.AUTO,
                 model_variant: Variant = Variant.GEMMA_3_1B_IT):

        # Store the variant and device as instance variables
        self.model_variant = model_variant
        self.device_map = device_map
        self.use_quantized = use_quantized
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder_path = os.path.join(script_dir, self.model_variant._folder_name)
        self.folder_path = os.path.normpath(self.folder_path)

        self.model = self._load_model(use_quantized)
        if not self.model_variant._is_gguf:
            self.tokenizer = self._load_tokenizer()
        else:
            self.tokenizer = None  # GGUF models don't need a separate Hugging Face tokenizer

        # A dictionary to hold generation parameters that can be easily updated.
        self.model_settings = dict(max_new_tokens=400,
                                   do_sample=False,
                                   temperature=None,
                                   top_p=None,
                                   top_k=None)

    def _load_model(self, use_quantized: bool):
        """
        Loads the Gemma model from a local directory.
        Quantizes the model to 4-bit if `use_quantized` is True.
        """

        if self.model_variant._is_gguf:
            # Dynamically find the .gguf file within the model directory.
            gguf_filename = None

            # This will print the directory your script is currently running in
            print(os.getcwd())
            for file in os.listdir(self.folder_path):
                if file.endswith(".gguf"):
                    gguf_filename = file
                    break

            if not gguf_filename:
                raise FileNotFoundError(f"No .gguf file found in the directory: {self.folder_path}")

            model = Llama(self.folder_path + "/" + gguf_filename)

        else:
            # For other Hugging Face models, use AutoModelForCausalLM.
            quantization_config = BitsAndBytesConfig(load_in_4bit=True) if use_quantized else None

            model = AutoModel.from_pretrained(
                self.model_variant.value[0],
                cache_dir="../model_files/gemma_models"
            )

        return model

    def _load_tokenizer(self):
        """
        Loads the tokenizer for the non-GGUF model variants.
        """
        # GGUF models handle tokenization internally.
        if self.model_variant._is_gguf:
            return None

        # Use .folder_name to get the string from the Enum
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_variant.value[0],
            cache_dir="../model_files/gemma_models")
        return tokenizer

    def set_model_settings(self,
                           max_new_tokens: int = None,
                           do_sample: bool = None,
                           temperature: float = None,
                           top_p: float = None,
                           top_k: int = None):
        """
        Updates the model settings with the provided values.

        Args:
            max_new_tokens (int): The maximum number of new tokens to generate.
            do_sample (bool): Whether to use sampling for generation.
            temperature (float): The sampling temperature.
            top_p (float): The nucleus sampling probability.
            top_k (int): The number of top tokens to consider.
        """
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
        if self.model_variant._is_gguf:
            # For GGUF models, use the create_chat_completion method.
            # The response is a dictionary, so we extract the text content.
            response = self.model.create_chat_completion(
                messages=messages,
                max_tokens=self.model_settings.get('max_new_tokens'),
                temperature=self.model_settings.get('temp') or 0.2,
                top_p=self.model_settings.get('top_p') or 0.95,
                top_k=self.model_settings.get('top_k') or 40
            )
            return response['choices'][0]['message']['content']

        # Prepares the messages into a format the Hugging Face model understands
        inputs = self.tokenizer.apply_chat_template(
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
        response = self.tokenizer.decode(generation, skip_special_tokens=True)
        return response