from pathlib import Path
from TTS.api import TTS
import base64, torch, os, re, hashlib
import soundfile as sf
import numpy as np

torch.serialization.add_safe_globals([
    __import__("TTS.tts.configs.xtts_config", fromlist=["XttsConfig"]).XttsConfig,
    __import__("TTS.tts.models.xtts", fromlist=["XttsAudioConfig"]).XttsAudioConfig,
    __import__("TTS.tts.models.xtts", fromlist=["XttsArgs"]).XttsArgs,
    __import__("TTS.config.shared_configs", fromlist=["BaseDatasetConfig"]).BaseDatasetConfig
])

class CoquiTRTTS:
    """
    A wrapper class for Coqui TTS (XTTS v2) with:
    Sentence splitting for faster perceived response
    Output caching to avoid regenerating identical sentences
    Optional per-chunk callback for streaming use cases
    WAV concatenation with silence between chunks
    """

    def __init__(self, model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                 output_dir="tts_out", use_gpu=True, speaker_wav=None, language="tr"):
        
        self.output_dir = Path(output_dir); self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir = self.output_dir / "cache"; self.cache_dir.mkdir(exist_ok=True)
        self.language = language

        if speaker_wav:
            sw = Path(speaker_wav)
            self.speaker_wav = str(sw.resolve()) if sw.is_file() else None
        else:
            self.speaker_wav = None

        self.model_name = model_name
        device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        self.tts = TTS(model_name=model_name)
        self.tts.to(device)

    def _normalize_text(self, t: str) -> str:
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def _split_sentences(self, text: str):
        text = self._normalize_text(text)
        parts = re.split(r"([\.!\?])", text)
        sents = []
        for i in range(0, len(parts)-1, 2):
            s = (parts[i] + parts[i+1]).strip()
            if s: sents.append(s)
        if len(parts) % 2 == 1 and parts[-1].strip():
            sents.append(parts[-1].strip())
        return [s for s in sents if s]

    # Generate a unique SHA1 key for the text+model+lang+speaker combination.
    def _cache_key(self, text: str) -> str:
        norm = self._normalize_text(text).lower()
        key_src = "|".join([self.model_name, self.language or "", self.speaker_wav or "", norm])
        return hashlib.sha1(key_src.encode("utf-8")).hexdigest()

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.wav"

    # if cached, return the cached file. Otherwise, synthesize and cache it.
    def _synthesize_sentence(self, sentence: str, on_ready=None) -> Path:
        key = self._cache_key(sentence)
        out = self._cache_path(key)
        if out.is_file():
            if on_ready: on_ready(str(out))
            return out
        self.tts.tts_to_file(text=sentence, file_path=str(out),
                             speaker_wav=self.speaker_wav, language=self.language)
        if on_ready: on_ready(str(out))
        return out

    def synthesize_chunked(self, text: str, filename: str = "output.wav",
                           silence_ms: int = 120, return_base64: bool = False,
                           on_chunk=None):
        out_path = self.output_dir / filename
        sentences = self._split_sentences(text)
        if not sentences:
            raise ValueError("Empty text.")

        sr = None
        chunks = []
        silence = None

        for s in sentences:
            wav_path = self._synthesize_sentence(s, on_ready=on_chunk)
            audio, cur_sr = sf.read(wav_path, dtype="float32")
            if sr is None:
                sr = cur_sr
                silence = np.zeros(int(sr * (silence_ms / 1000.0)), dtype=np.float32)
            elif cur_sr != sr:
                pass
            chunks.append(audio)
            chunks.append(silence)

        if len(chunks) > 0:
            chunks = chunks[:-1]

        full = np.concatenate(chunks) if chunks else np.zeros(1, dtype=np.float32)
        sf.write(out_path, full, sr)

        if return_base64:
            b64 = base64.b64encode(out_path.read_bytes()).decode("utf-8")
            return {"wav_path": str(out_path), "base64": b64, "sentences": sentences}
        return {"wav_path": str(out_path), "sentences": sentences}
    
    # Synthesize the entire text in one go without sentence splitting or caching.
    def synthesize(self, text: str, filename: str = "output.wav", return_base64: bool = False):
        out_path = self.output_dir / filename
        self.tts.tts_to_file(text=text, file_path=str(out_path),
                             speaker_wav=self.speaker_wav, language=self.language)
        if return_base64:
            return {"wav_path": str(out_path),
                    "base64": base64.b64encode(out_path.read_bytes()).decode("utf-8")}
        return {"wav_path": str(out_path)}
