import io
import os
import numpy as np
import librosa
from scipy.io.wavfile import write as write_wav
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from faster_whisper import WhisperModel
from src.llm.core.devices import Device
from TTS.api import TTS


print("AI Modelleri yükleniyor...")
try:
    DEVICE = Device.CUDA.value
    whisper_model = WhisperModel("medium", device=DEVICE, compute_type="float16")

    tts_model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
    tts_model = TTS(tts_model_name).to(DEVICE)

    # TTS modelinin orijinal örnekleme oranını alalım.
    TTS_SAMPLERATE = tts_model.synthesizer.output_sample_rate

except Exception as e:
    print(f"Modeller yüklenirken kritik bir hata oluştu: {e}")
    raise e

print("AI Modelleri başarıyla yüklendi ve sunucu hazır.")

app = FastAPI(
    title="Uçtan Uca Sesli Asistan",
    description="Ses alır, işler ve sesli yanıt verir."
)


@app.post("/of68s90/process_audio_endpoint")
async def process_audio_endpoint(audio_file: UploadFile = File(...)):
    """
    Bu endpoint ses dosyasını işler ve yanıtı ses olarak stream eder.
    """
    try:
        # --- ADIM 1: Gelen Sesi Güvenli Bir Şekilde Oku ve Hazırla ---
        # Gelen dosyayı doğrudan librosa ile oku. Bu, formatı otomatik olarak algılar.
        # audio_file.file -> file-like object'i temsil eder.
        input_waveform, original_sr = librosa.load(audio_file.file, sr=None, mono=True)
        print(f"Gelen ses dosyası okundu. Orijinal Örnekleme Oranı: {original_sr} Hz")

        # Whisper'ın istediği 16kHz formatına yeniden örnekle (resample).
        target_sr = 16000
        if original_sr != target_sr:
            input_waveform = librosa.resample(input_waveform, orig_sr=original_sr, target_sr=target_sr)
            print(f"Ses {target_sr} Hz'e yeniden örneklendi.")

        # --- ADIM 2: Faster-Whisper ile Metne Çevir ---         
        segments, _ = whisper_model.transcribe(input_waveform, beam_size=10, language="tr",vad_filter=True, vad_parameters=dict(min_silence_duration_ms=800, max_speech_duration_s=15))     # eğer yavaşsa beam_size=5
        transkript = " ".join([segment.text for segment in segments]).strip()
        print(f"Transkripsiyon Sonucu: {transkript}")

        if not transkript:
            raise HTTPException(status_code=400, detail="Seste konuşma tespit edilemedi.")

        # --- ADIM 3: LLM ile Metni İşle (Sizin Projenize Özel Kısım) ---
        # Bu kısmı kendi LangGraph veya LLM çağrınızla değiştirin.
        response_text = f"Bana şunu söyledin: {transkript}. Harika bir analiz."
        print(f"LLM Yanıtı: {response_text}")

        # --- ADIM 4: CoquiTTS ile Yanıtı Sese Çevir (Bellekte) ---
        # PERFORMANS: Diske yazmak yerine doğrudan bellekte numpy array olarak al.
        reference_audio_path= "../tts/ref_tr.wav"
        tts_output_waveform = tts_model.tts(
            text=response_text,
            language="tr",
            speaker_wav=reference_audio_path
        )

        # --- ADIM 5: Ses Verisini WAV Formatında Hazırla ve Gönder ---
        # Bellek içi bir byte buffer oluştur
        wav_buffer = io.BytesIO()
        # NumPy array'ini WAV formatında bu buffer'a yaz
        # DİKKAT: tts_model'in kendi örnekleme oranını kullanıyoruz (örn: 22050 Hz)
        write_wav(wav_buffer, TTS_SAMPLERATE, np.array(tts_output_waveform))
        wav_buffer.seek(0)  # Buffer'ın başına dön

        return StreamingResponse(wav_buffer, media_type="audio/wav")

    except Exception as e:
        print(f"İşlem sırasında bir hata oluştu: {e}")
        raise HTTPException(status_code=500, detail=f"Sunucu hatası: {str(e)}")

# Sunucuyu çalıştırmak için terminalde: uvicorn dosya_adi:app --reload