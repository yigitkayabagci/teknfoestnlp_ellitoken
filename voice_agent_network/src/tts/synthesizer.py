from pathlib import Path
from transformers import VitsTokenizer, VitsModel
import torch
import scipy.io.wavfile as wavfile
import os

class MMSTTS:
    def __init__(self, model_name="facebook/mms-tts-tur", output_dir="tts_out", offline=True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        kwargs = {"local_files_only": True} if offline else {}

        self.tokenizer = VitsTokenizer.from_pretrained(model_name, **kwargs)
        self.model = VitsModel.from_pretrained(model_name, **kwargs)
        self.model.eval()

    def synthesize(self, text, filename="output.wav"):
        output_path = self.output_dir / filename
        inputs = self.tokenizer(text, return_tensors="pt")

        with torch.no_grad():
            waveform = self.model(**inputs).waveform[0]

        wavfile.write(output_path, self.model.config.sampling_rate, waveform.numpy())
        return str(output_path)
