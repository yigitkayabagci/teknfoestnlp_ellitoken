from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import io
import numpy as np
from scipy.io.wavfile import write

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
            tts_output_bytes = io.BytesIO()
            tts_model.tts_to_file(
                text=islenmis_metin,
                file_path=tts_output_bytes
            )
            tts_output_bytes.seek(0)

            # 6. Oluşturulan ses dosyasını geri gönder
            return StreamingResponse(tts_output_bytes, media_type="audio/wav")

    