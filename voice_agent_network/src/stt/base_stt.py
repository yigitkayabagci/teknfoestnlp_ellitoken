from faster_whisper import WhisperModel
#from config.settings import MODEL_SIZE, DEVICE, COMPUTE_TYPE


"""
beam_size farklı olasıkları değerlendirir, language sesin hangi dil olduğunu belirtince performansı artar
vad_filter sessizliği filtreleyen
min_silence_duration: sessiz diye etiketlemesi için 0.8 saniye yeterli, 
max_speech_duration: bir segmentin max süresi, ses eğer bu süreden büyükse sesi segmentlere böler
json formatı döner
"""
class BaseSTT:
    def __init__(self):
        MODEL_SIZE="large"              #medium görece çok hızlı ama doğruluğu düşük
        DEVICE="cpu"
        COMPUTE_TYPE="int8"
    
        self.model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)

    def transcribe(self, audio_source):
        segments, info = self.model.transcribe(
            audio_source,
            beam_size=10,   #arttıkça doğruluk artar, hız düşer
            language="tr",
            vad_filter=True,      # sessizlik filtresi
            vad_parameters=dict(min_silence_duration_ms=800, max_speech_duration_s=15)
        )
        text = "".join([segment.text for segment in segments])
        result = {
            "transcription": text,
            "language": info.language,
            "language_probability": info.language_probability
        }
        return result