# Test cases for STT module
# test_stt.py
# \teknfoestnlp_ellitoken\voice_agent_network> bu yoldayken python -m tests.test_stt bu commandle çalıştırmayı deneyebilirsiniz
import sys
from src.stt import FileSTT, MicSTT

def test_file_stt(file_path):
    stt = FileSTT()
    try:
        result = stt.transcribe_from_file(file_path)
        print("=== FileSTT Transcription ===")
        print(f"Metin: {result['transcription']}")
        print(f"Dil: {result['language']} (Olasılık: {result['language_probability']:.2f})")
    except Exception as e:
        print(f"Hata: {e}")

def test_mic_stt():
    stt = MicSTT()
    print("Mikrofon testi başlıyor. Konuşmaya başlayın...")
    result = stt.start_recording()  # artık dict dönecek
    print(f"Metin: {result['transcription']}")
    print(f"Dil: {result['language']} (Olasılık: {result['language_probability']:.2f})")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        test_file_stt(file_path)
    else:
        test_mic_stt()