import json
import os
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
api_key = os.getenv("GEMINI_KEY")

tools_metadata = """
{
  "fill_slot": {
    "description": "Bu tool randevu için gerekli olan isim, kimlik, telefon, yaş, kilo, boy, sigara, şehir, ilçe, gün ve saat bilgilerini JSON yapısına kayıt etmek için kullanılır.",
    "input_schema": {
      "isim": "string",
      "kimlik": "integer",
      "telefon": "string",
      "yaş": "integer",
      "kilo": "integer",
      "boy": "integer",
      "sigara": "boolean",
      "klinik": "string",
      "şehir": "string",
      "ilçe": "string",
      "gün": "string",
      "saat": "string"
    }
  },
  "get_appointment_options": {
    "description": "Bu tool kullanıcının belirlediği klinik, şehir, ilçe, gün ve saat bilgilerine göre uygun randevu seçeneklerini sorgular. Randevu seçenekleri olmadığında boş bir liste döndürebilir.",
    "input_schema": {
        "klinik": "string",
        "şehir": "string",
        "ilçe": "string",
        "gün": "string",
        "saat": "string"
    },
    "output_schema": {
      "randevu_seçenekleri": "array of {şehir, ilçe, klinik, gün, saat, id}"
    }
  },
  "make_an_appointment": {
    "description": "Bu tool randevu ID'si ile randevu oluşturma işlemini tamamlar. Randevu oluşturulduktan sonra başarı mesajı döner.",
    "input_schema": {
      "randevu_id": "string"
    },
    "output_schema": {
      "durum": "string"
    }
  }
}
"""
user_data = {
    "isim": "Fadime Agent Müezzir",
    "kimlik": 345345345,
    "telefon": "+905554443322",
    "yaş": 19,
    "kilo": 130,
    "boy": 150,
    "sigara": False,
    "randevu": {
        "şehir": None,
        "ilçe": None,
        "gün": None,
        "saat": None,
        "id": None
    }
}

role_instruction = """
Sen kullanıcıların randevu almasına yardım eden bir asistansın. Görevin kullanıcıdan randevu ayarlamak için gerekli bilgileri toplamak ve kullanıcıyı semptomlarına göre randevu için doğru kliniğe yönlendirmek. Konu dağıldığında veya kullanıcı başka bir konu hakkında konuşmak istediğinde kullanıcıyı kibarca görevin olan randevu alma bağlamına yönlendir. Unutma, tek ve en önemli görevin kullanıcının randevu almasına yardımcı olmak!

Akış şu şekilde olmalı:
1) Kullanıcı bilgilerini (isim, kimlik, telefon, yaş, kilo, boy, sigara) kontrol et. Eksik olanları kullanıcıya sorarak tamamla ve her eksik bilgiyi topladığında `fill_slot` tool çağrısı yapıp bilgiyi kaydet.
2) Tüm kullanıcı bilgileri tamamlandığında, randevu alınacak kliniği belirle. Kullanıcıya randevu almak istediği kliniği sor, eğer isterse klinik seçiminde yardımcı olabileceğini söyle. Eğer klinik seçimi konusunda yardım isterse kullanıcıya semptomlarını ve neden muayene olmak istediğini sor. 
3) Klinik tespitini yap ve kullanıcının bu klinikten randevu almak isteyip istemediğini sorarak durumu netleştir. Netleştikten sonra `fill_slot` tool çağrısı ile klinik bilgisini kaydet.
4) Klinik bilgisi tespit edildikten sonra artık kullanıcının istediği şehir, ilçe, randevu günü ve randevu saati bilgilerini tespit etmekte. Eğer kullanıcının şehir, ilçe, randevu günü ve randevu saati bilgisi eksik ise onları kullanıcıya sorarak doldur.
5) Önceki adımları eksiksiz bir şekilde tamamladığına emin olduktan sonra artık `get_appointment_options` tool çağırma vakti. Uygulama bu tool çağırır ve elde ettiğin bilgilere göre en iyi 2 randevu opsiyonunu modele verir. Kullanıcının bu iki randevu seçeneğinden birini isteyip istemediğini sorarak netleştir. Netleştikten sonra `make_an_appointment tool` çağrısı ile randevuyu ayarla.
Kurallar:
- Türkçe cevap ver.
- Bir adımı tamamlamadan daha ilerideki bir adıma atlaman yasak!
- Kullanıcı randevu ayarlamak için gereken tüm bilgileri tek seferde vermeyebilir. Bu yüzden bilgi verdiğinde fill_slot tool çağrısı yapmanı ve bu bilgiyi kaydetmen zorunlu.
- Tool çağrıları kesinlikle şu formatta olmalı. Tool çağrıları için bu formatın dışına çıkman tamamen yasak! (tek satır JSON, başka metin yok):
   <TOOL_CALL>{"name":"tool_name","args":{...}}</TOOL_CALL>
- Uygulama gerçek tool'u çağırıp çıktıyı aynı formatta modele geri verir:
   <TOOL_RESPONSE>{"name":"tool_name","result":{...}}</TOOL_RESPONSE>
- Eğer tool çağrısı yapman gerekirse sakın başka bir şeyler yazma!
- Tool seçiminde `TOOLS_METADATA` içindeki açıklama, input şeması ve output şeması bilgilerini dikkate al.
- Tool çağrısı yapıldığında model yalnızca tek bir <TOOL_CALL> üretmeli; daha fazla veri gerekirse uygulama sonucu modele <TOOL_RESPONSE> formatında iletip model oturumu devam ettirir.
- Unutma kullanıcıya tool bahsetmek kesinlikle yasak! Zaten kullanıcının tool erişimi yoktur, kullanamaz! Sistem tool kullanmayı kullanıcıdan gizli bir şekilde arka planda ele alır, tool çağrısı mesajını kullanıcıya iletmez.
- Kullanıcının cevaplayabileceği soruları kullanıcıya sorabilirsin. Ama unutma kullanıcının sorunun cevabını verebilecek olması oldukça önemli. 
- Uygulama kullanıcının cevabını alıp modele geri verir.

""" + f"TOOLS_METADATA: {tools_metadata}" + """
Bunlar senin erişimine açık tool'lar. Ekstra bir bilgiye ihtiyaç duyduğunda ilk bakman gereken şey bu tool listesi. Bu tool'ları çağırdığında sana hangi bilgileri sağlayacağını iyi anla (tool hakkındaki tüm bilgiler TOOLS_METADATA olarak verildi) ve gerekirse kullanmaktan çekinme! 
Unutma kullanıcıya yanıt vermeden önce tool kullanarak elde edeceğin bilgilerin senin yanıtını geliştireceğini tespit edersen tool çağrısını gerçekleştirmelisin!
"""

genai.configure(api_key=api_key)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=role_instruction
)

chat = model.start_chat(history=[])

print("🤖 Chatbot: Merhaba! Ne konuşmak istersiniz?. Konuşmayı sonlandırmak için 'exit' yazın.")
print("---------------------------------------------------------------------------------------")

while True:
    try:
        user_message = input("👨‍💻 You: ")

        if user_message.lower() == "exit":
            print("🤖 Chatbot: Goodbye! 👋")
            break

        # Append USER_DATA to the user's message before sending to the model
        user_message_with_data = user_message + f"\nUSER_DATA: {json.dumps(user_data)}"

        # Send the user's message to the model
        response = chat.send_message(user_message_with_data)

        # Check if the model's response contains a tool call
        if "<TOOL_CALL>" in response.text:
            # Extract the JSON payload from the tool call
            tool_call_text = response.text.split("<TOOL_CALL>")[1].split("</TOOL_CALL>")[0]
            tool_call_json = json.loads(tool_call_text)

            tool_name = tool_call_json.get("name")
            tool_args = tool_call_json.get("args")

            if tool_name == "fill_slot" and tool_args:
                # Update user_data with the arguments from the tool call
                for key, value in tool_args.items():
                    # Handle nested randevu data
                    if key in user_data["randevu"]:
                        user_data["randevu"][key] = value
                    else:
                        user_data[key] = value

                print("🤖 Chatbot: [SYSTEM] Kullanıcı bilgileri güncellendi.")
                # You can optionally print the updated user_data to see the changes
                # print("Güncellenmiş kullanıcı verisi:", user_data)

                # Now, send a TOOL_RESPONSE back to the model to continue the conversation
                # The TOOL_RESPONSE will contain the updated user_data for the model to see
                tool_response_payload = {
                    "name": "fill_slot",
                    "result": user_data
                }
                tool_response_text = f"<TOOL_RESPONSE>{json.dumps(tool_response_payload)}</TOOL_RESPONSE>"

                # Send the tool response and get a new response from the model
                final_response = chat.send_message(tool_response_text)
                print("🤖 Chatbot:", final_response.text)
            else:
                # Handle other tool calls here (get_appointment_options, make_an_appointment)
                # For this example, we'll just print a message
                print(f"🤖 Chatbot: [SYSTEM] Tool çağrısı tespit edildi: {tool_name} (Bu kısım henüz uygulanmadı)")
        else:
            # If there's no tool call, just print the model's text response
            print("🤖 Chatbot:", response.text)

    except Exception as e:
        print(f"An error occurred: {e}")
        break