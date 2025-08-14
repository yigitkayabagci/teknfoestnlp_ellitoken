from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import io
import numpy as np
from scipy.io.wavfile import write
import os
from pathlib import Path

class STTServer:
    def __init__(self):
        self.app = FastAPI()

        @self.app.post("/14u38o/stt_server")
        async def ses_isle(self, audioData: UploadFile = File(...)):
            # 1. Gelen ham ses byte'larını oku
            ses_bytes = await audioData.read()

            # 2. Ham ses verisini WAV dosyasına dönüştür
            # Bellek içi dosya olarak işlem yapmak daha performanslıdır
            wav_file = io.BytesIO()
            audio_data_int16 = np.frombuffer(ses_bytes, dtype=np.int16)
            write(wav_file, 16000, audio_data_int16)
            wav_file.seek(0)  # Dosyanın başına dön

            # 3. Faster-Whisper ile metne çevir
            segments, info = whisper_model.transcribe(wav_file, beam_size=5)
            transkript = " ".join([segment.text for segment in segments])
            print(f"Konuşma metni: {transkript}")

            # 4. LLM ile metni işle (bu kısım sizin projenize özel)
            islenmis_metin = f"Söylediğin: '{transkript}'. Bu harika bir konuşma."


            # 5. CoquiTTS ile metni sese çevir
            temp_wav_path = Path("temp_tts_output.wav")

            try:
                self.tts_model.synthesize(text=islenmis_metin, filename=str(temp_wav_path))

                with open(temp_wav_path, "rb") as f:
                    tts_output_bytes = io.BytesIO(f.read())
                tts_output_bytes.seek(0)

                return StreamingResponse(tts_output_bytes, media_type="audio/wav")
            finally:
                if temp_wav_path.exists():
                    os.remove(temp_wav_path)

    