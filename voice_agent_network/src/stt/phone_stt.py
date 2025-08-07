import os
import requests
from requests.auth import HTTPBasicAuth
from flask import Flask, request, jsonify
from twilio.twiml.voice_response import VoiceResponse
from .base_stt import BaseSTT
from dotenv import load_dotenv

load_dotenv() 

ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")

class PhoneSTT(BaseSTT):
    def __init__(self):
        super().__init__()
        self.app = Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/call', methods=['POST'])
        def handle_call():
            response = VoiceResponse()
            response.say("Lütfen kaydınızı yapmak için konuşmaya başlayın.")
            response.record(
                timeout=5,
                action='/transcribe',
                max_length=30,          #en fazla otuz saniye
                recording_status_callback='/recording-status',
                recording_channels='mono',     #tek kanal
                recording_status_callback_event='completed'
            )
            return str(response)

        @self.app.route('/transcribe', methods=['POST'])
        def transcribe_recording():
            recording_url = request.form.get('RecordingUrl')
            if not recording_url:
                return jsonify({"error": "Recording URL is missing"}), 400

            print("Twilio kayıt URL:", recording_url)

            try:
                response = requests.get(recording_url, auth=HTTPBasicAuth(ACCOUNT_SID, AUTH_TOKEN))
                if response.status_code != 200:
                    return jsonify({"error": "Audio download failed", "details": response.text[:200]}), 500

                audio_file_path = "recording.mp3"
                with open(audio_file_path, "wb") as f:
                    f.write(response.content)

                print(f"Dosya kaydedildi: {audio_file_path} ({os.path.getsize(audio_file_path)} byte)")

                transcription_text, info = self.transcribe(audio_file_path)

                print("Transkripsiyon:", transcription_text)
                print(f"Algılanan dil: {info.language} (Olasılık: {info.language_probability:.2f})")

                return jsonify({
                    "transcription": transcription_text.strip(),
                    "detected_language": info.language,
                    "language_confidence": round(info.language_probability, 2)
                })

            except Exception as e:
                print("Transkripsiyon hatası:", str(e))
                return jsonify({"error": "Transcription failed", "details": str(e)}), 500

            finally:
                if os.path.exists(audio_file_path):
                    os.remove(audio_file_path)

        @self.app.route('/recording-status', methods=['POST'])
        def recording_status():
            print("✅ Twilio: Kayıt tamamlandı bildirimi geldi.")
            return "OK", 200

    def run(self, debug=True, host="0.0.0.0", port=5000):
        self.app.run(debug=debug, host=host, port=port)

if __name__ == '__main__':
    server = PhoneSTT