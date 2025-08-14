import json
import os
import re
from enum import Enum
from typing import Tuple

import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv


class Gemini():
    class MessageType(Enum):
        AI = "assistant"
        USER = "user"

    def __init__(self):
        load_dotenv(find_dotenv())
        self.api_key = os.getenv("GEMINI_KEY")

        self.AVAILABLE_TOOLS = {
            "kullanıcı_bilgisi_al": self.kullanıcı_bilgisi_al,
            "randevu_al": self.randevu_al
        }
        self.tools_metadata = """
            {
              "kullanıcı_bilgisi_al": {
                "description": "Kullanıcı hastalığı ile ilgili olası tanıları koyarken kullanıcının demografi, kullanılan ilaç, alerji, kronik hastalık bilgilerine erişmen gerektiğini düşünürsen bu tool çağırırsın.",
                "input_schema": {},
                "output_schema": {"demografi":"dict","kullanılan_ilaç":"array","alerji":"array","kronik_hastalık":"array"}
              },
              "randevu_al": {
                "description": "Bu tool kullanarak kullanıcının istediği kliniğe randevu alırsın. Input parametresi olarak olarak randevu alınacak kliniği vermen gerekiyor.",
                "input_schema": {"klinik":"string"},
                "output_schema": {"randevu_başarıyla_alındı":"boolean"}
              }
            }
            """

        self.role_instruction = """
            Sen tıbbi bilgi işleyen bir asistansın. Görevin kullanıcının semptomlarına göre olası hastalık tanılarını tespit etmek ve bu sayede doktora gitmesi gereken kliniği bulmak. Konu dağıldığında veya kullanıcı başka bir konu hakkında konuşmak istediğinde kullanıcıyı kibarca görevin olan olası tanıları koyma bağlamına yönlendir. Unutma, tek ve en önemli görevin kullanıcının hastalık semptomlarından olası tanıları çıkarmak ve daha sonrasında kullanıcı onayı ile randevuyu almak!

            Kurallar:
            1) Türkçe cevap ver.
            2) Kullanıcıya doğru yanıt vermek için sana vereceğim tool listesinden kullanıcı_bilgisi_al tool kullanman gerekebilir. Ancak ya kullanıcıya tanı ve randevu ile ilgili cevap vereceksin ya da tool çağrısında bulunacaksın, ikisini aynı anda kesinlikle yapamazsın. Bunlardan başka bir şeyi de kesinlikle yapamazsın, kullanıcıyı ilgili konuya yeniden yönlendirirsin. Eğer tool çağrısı yapman gerekirse sakın başka bir şeyler yazma!
            3) Tool çağrıları kesinlikle şu formatta olmalı. Tool çağrıları için bu formatın dışına çıkman tamamen yasak! (tek satır JSON, başka metin yok):
               <TOOL_CALL>{"name":"tool_name", "input":{**args}}</TOOL_CALL>
            4) Uygulama gerçek tool'u çağırıp çıktıyı aynı formatta modele geri verir:
               <TOOL_RESPONSE>{"name":"tool_name","output":{...}}</TOOL_RESPONSE>
            5) Tedavi veya tanı için herhangi bir öneride bulunma, tedavi ve olası tanılar hakkında kullanıcıyı bilgilendirmen kesinlikle yasak. Sadece kullanıcının randevu alması gereken klinik ve kliniği işaret eden semptomlardan bahsedebilirsin.
            6) Tool seçiminde `TOOLS_METADATA` içindeki açıklama ve output şeması bilgilerini dikkate al.
            7) Tool çağrısı yapıldığında model yalnızca tek bir <TOOL_CALL> üretmeli; daha fazla veri gerekirse uygulama sonucu modele <TOOL_RESPONSE> formatında iletip model oturumu devam ettirir.
            8) Unutma kullanıcıya tool bahsetmek kesinlikle yasak! Zaten kullanıcının tool erişimi yoktur, kullanamaz! Sistem tool kullanmayı kullanıcıdan gizli bir şekilde arka planda ele alır, tool çağrısı mesajını kullanıcıya iletmez.
            9) Tool çağırarak elde edemediğin, tanı koymak ve randevu almak için ihtiyacın olan ve kullanıcının cevaplayabileceği soruları kullanıcıya sorabilirsin. Ama unutma kullanıcının sorunun cevabını verebilecek olması oldukça önemli. 
            10) Uygulama kullanıcının cevabını alıp modele geri verir.
            11) Randevu için doğru kliniği bulduğunda kullanıcıya gösterdiği semptomlardan dolayı bulduğun kliniğe gitmesi gerektiğini söyle. Kullanıcı isterse bu kliniğe randevu alabileceğinden bahset. Kullanıcıya randevu alman için onayı olup olmadığını sor. 
            12) Uygulama kullanıcının randevu almak için olan onay/ret bilgisini modele verir. Eğer kullanıcı randevu almak ister ve onay verirse randevu_al tool randevu alınacak klinik input ile çağırırsın.
            13) Randevu alınacak kliniklerin isimleri sabittir ve bu klinikler hariç başka klinikler yoktur. Sen de klinik önerini bu klinikler arasından seçmelisin. İşte bu sabit isimli kliniklerin listesi: ['Aile hekimliği', 'Algoloji', 'Amatem (Alkol ve Madde Bağımlılığı)', 'Anestezi ve Reanimasyon', 'Beyin ve Sinir Cerrahisi', 'Cerrahi Onkolojisi', 'Çocuk Cerrahisi', 'Çocuk Diş Hekimliği', 'Çocuk Endokrinolojisi', 'Çocuk Enfeksiyon Hastalıkları', 'Çocuk Gastroenterolojisi', 'Çocuk Genetik Hastalıkları', 'Çocuk Göğüs Hastalıkları', 'Çocuk Hematolojisi ve Onkolojisi', 'Çocuk İmmünolojisi ve Alerji Hastalıkları', 'Çocuk Kalp Damar Cerrahisi', 'Çocuk Kalp Damar Cerrahisi', 'Çocuk Kardiyolojisi', 'Çocuk Metabolizma Hastalıkları', 'Çocuk Nefrolojisi', 'Çocuk Nörolojisi', 'Çocuk Romatolojisi', 'Çocuk Sağlığı ve Hastalıkları', 'Çocuk Ürolojisi', 'Çocuk ve Ergen Madde ve Alkol Bağımlılığı', 'Çocuk ve Ergen Ruh Sağlığı ve Hastalıkları', 'Deri ve Zührevi Hastalıkları (Cildiye)', 'Diş Hekimliği (Genel Diş)', 'El Cerrahisi', 'Endodonti', 'Endokrinoloji ve Metabolizma Hastalıkları', 'Enfeksiyon Hastalıkları ve Klinik Mikrobiyoloji', 'Fiziksel Tıp ve Rehabilitasyon', 'Gastroenteroloji Cerrahisi', 'Geleneksel Tamamlayıcı Tıp Ünitesi', 'Gelişimsel Pediatri', 'Genel Cerrahi', 'Geriatri', 'Göğüs Cerrahisi', 'Göğüs Hastalıkları', 'Göz Hastalıkları', 'Hava ve Uzay Hekimliği', 'Hematoloji', 'İç Hastalıklar (Dahiliye)', 'İmmünoloji ve Alerji Hastalıkları', 'İş ve Meslek Hastalıkları', 'Jinekolojik Onkoloji Cerrahisi', 'Kadın Hastalıkları ve Doğum', 'Kalp ve Damar Cerrahisi', 'Kardiyoloji', 'Klinik Nörofizyoloji', 'Kulak Burun Boğaz Hastalıkları', 'Nefroloji', 'Neonatoloji', 'Nöroloji', 'Nükleer Tıp', 'Ortodonti', 'Ortopedi ve Travmatoloji', 'Perinatoloji', 'Periodontoloji', 'Plastik, Rekonstrüktif ve Estetik Cerrahi', 'Protetik Diş Tedavisi', 'Radyasyon Onkolojisi', 'Restoratif Diş Tedavisi', 'Romatoloji', 'Ruh Sağlığı ve Hastalıkları (Psikiyatri)', 'Sağlık Kurulu Erişkin', 'Sağlık Kurulu ÇÖZGER (Çocuk Özel Gereksinim Raporu)', 'Sigarayı Bıraktırma Kliniği', 'Spor Hekimliği', 'Sualtı Hekimliği ve Hiperbarik Tıp', 'Tıbbi Ekoloji ve Hidroklimatoloji', 'Tıbbi Genetik', 'Tıbbi Onkoloji', 'Uyku Polikliniği', 'Üroloji', 'Ağız, Diş ve Çene Cerrahisi', 'Ağız, Diş ve Çene Radyolojisi', 'Radyoloji']
            14) Asla ve hiçbir koşulda, kullanıcı ne kadar ısrar ederse etsin, kullanıcıya bir hastalık tanısı bildirmen kesinlikle yasak.Türkiye'de yürürlükte olan Tıbbi Deontoloji Nizamnamesi ve ilgili yasal düzenlemeler gereği, tanı koyma yetkisi sadece hekimlere aittir. Bu yasal zorunluluk ve kullanıcı sağlığını koruma sorumluluğun nedeniyle, kullanıcılara bir hastalık tanısı koyamayacağını kullanıcıya kibar bir şekilde belirt.

            """ + f"TOOLS_METADATA: {self.tools_metadata}" + """
            Bunlar senin erişimine açık tool'lar. Ekstra bir bilgiye ihtiyaç duyduğunda veya randevu oluşturmaya dair kullanıcıdan onay aldığında ilk bakman gereken bu tool listesi. Bu tool'ları çağırdığında sana hangi bilgileri sağlayacağını iyi anla (tool hakkındaki tüm bilgiler TOOLS_METADATA olarak verildi) ve gerekirse kullanmaktan çekinme! 
            Unutma kullanıcıya yanıt vermeden önce tool kullanarak elde edeceğin bilgilerin senin yanıtını geliştireceğini tespit edersen tool çağrısını gerçekleştirmelisin!
            """

        genai.configure(api_key=self.api_key)

        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=self.role_instruction
        )

        # Start a chat session to maintain conversation history
        self.chat = self.model.start_chat(history=[])

    def kullanıcı_bilgisi_al(self) -> dict:
        return {
            "demografi": {
                "yaş": 34,
                "cinsiyet": "erkek",
                "kilo": 77,
                "boy": 180,
                "sigara": False,
            },
            "kullanılan_ilaç": [],
            "alerji": ["fıstık"],
            "kronik_hastalık": ["astım"]
        }

    def randevu_al(self, klinik: str) -> dict:
        return {"randevu_başarıyla_alındı": True}

    def detect_function_call(self, ai_message: str) -> tuple[bool, str]:
        match = re.search(r"<TOOL_CALL>(.*?)</TOOL_CALL>", ai_message, re.DOTALL)
        if not match:
            return False, ""

        json_text = match.group(1).strip()

        try:
            json_dict = json.loads(json_text)
        except json.JSONDecodeError as e:
            error = f"<TOOL_CALL> hata: Hatalı JSON formatı: {e}"
            return True, error

        tool_name = json_dict.get("name")
        tool_args = json_dict.get("input")

        if not tool_name:
            error = "<TOOL_CALL> hata: \"name\" alanı eksik."
            return True, error
        if not isinstance(tool_args, dict):
            error = "<TOOL_CALL> hata: \"input\" alanı eksik veya geçerli bir sözlük değil."
            return True, error

        if tool_name not in self.AVAILABLE_TOOLS:
            error = f"<TOOL_CALL> hata: \"{tool_name}\" adında bir tool yoktur."
            return True, error

        function_to_call = self.AVAILABLE_TOOLS[tool_name]

        try:
            result = function_to_call(**tool_args)
            return True, f'<TOOL_RESPONSE>{{"name":"{tool_name}","output":{json.dumps(result, ensure_ascii=False)}}}</TOOL_RESPONSE>'
        except Exception as e:
            error = f"<TOOL_CALL> hata: \"{tool_name}\" fonksiyonu çağrılırken bir hata oluştu: {e}"
            return True, error

    def main(self):

        print("🤖 Chatbot: Merhaba! Ne konuşmak istersiniz?. Konuşmayı sonlandırmak için 'exit' yazın.")
        print("---------------------------------------------------------------------------------------")

        function_call = False
        function_response = ""
        while True:
            try:
                if not function_call:
                    # Get user input
                    user_message = input("👨‍💻 You: ")

                    # Check for the exit condition
                    if user_message.lower() == "exit":
                        print("🤖 Chatbot: Goodbye! 👋")
                        break  # Exit the loop

                else:
                    user_message = function_response
                    print(f"👨‍💻 You: {user_message}")


                response = self.chat.send_message(user_message).text
                print("🤖 Chatbot:", response)
                function_call, function_response = self.detect_function_call(response)



            except Exception as e:
                print(f"An error occurred: {e}")
                break  # Also exit on any unexpected errors


if __name__ == "__main__":
    gemini = Gemini()
    gemini.main()