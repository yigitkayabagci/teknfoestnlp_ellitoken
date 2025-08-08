from synthesizer import MMSTTS

tts = MMSTTS()
output_path = tts.synthesize("Merhaba, bu bir deneme metnidir Teknofest yarışması için bu deneme yapıldı.")
print("Ses dosyası kaydedildi:", output_path)
