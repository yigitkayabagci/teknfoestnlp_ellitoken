import numpy as np
import sounddevice as sd
import queue
from .base_stt import BaseSTT

"""
chunk_size: # her 1 saniyelik sesi bir defada işlemek
sample_rate_stadart önrekleme hızı
her seferinde queue'ya atar
silence_threshold ses frakansıyla ilgili, değiştirilirse "sessizlik" algısı değişir
"""


class MicSTT(BaseSTT):
    def __init__(self, sample_rate=16000, chunk_size=16000, silence_threshold=0.01, silence_duration=7):    # buradan silence_duration değiştirilecek, kaç saniyelik sessizlikte kapanacağı
        super().__init__()
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue()
        self.recording = []
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration  # saniye
        self.silent_chunks_required = int(silence_duration * sample_rate / chunk_size)

    def _callback(self, indata, frames, time, status):
        self.audio_queue.put(indata.copy())

    def _is_silent(self, data):
        rms = np.sqrt(np.mean(data**2))  # Sesin enerjisi (RMS)
        return rms < self.silence_threshold

    def start_recording(self):
        silent_chunks = 0
        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='float32',
                            blocksize=self.chunk_size, callback=self._callback):
            print("Konuşun... (sessizlik algılanırsa durur)")
            try:
                while True:
                    data = self.audio_queue.get()
                    self.recording.append(data.flatten())

                    if self._is_silent(data):
                        silent_chunks += 1
                    else:
                        silent_chunks = 0  # yeniden başla çünkü sessizlik bozuldu

                    if silent_chunks >= self.silent_chunks_required:
                        print("Sessizlik algılandı, durduruluyor...")
                        break
            except KeyboardInterrupt:
                print("Manuel olarak durduruldu.")
        
        full_audio = np.concatenate(self.recording)
        result = self.transcribe(full_audio)  # artık dict döner
        return result