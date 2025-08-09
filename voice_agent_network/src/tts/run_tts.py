from synthesizer import CoquiTRTTS

def on_chunk_ready(path):
    print("[ready chunk] ", path)
    # Callback executed when each synthesized sentence chunk is ready
    # Here we could immediately push the audio to the mobile client
    # (convert to base64 and send via WebSocket/HTTP)

# reference wav
tts = CoquiTRTTS(use_gpu=True, speaker_wav='ref_tr.wav')
text = "Belirttiğiniz şikâyetler değerlendirilmiş olup, gerekli muayene ve tetkikler için sizi Dahiliye Polikliniği’ne yönlendiriyorum. Lütfen randevu saatinizden 15 dakika önce hazır bulununuz. Sağlıklı günler dilerim."

res = tts.synthesize_chunked(
    text,
    filename="output.wav",
    silence_ms=50,
    return_base64=False,  # If True, also return audio as Base64 string
    on_chunk=on_chunk_ready
)

print("Final WAV:", res["wav_path"])
print("Sentences:", res["sentences"])
