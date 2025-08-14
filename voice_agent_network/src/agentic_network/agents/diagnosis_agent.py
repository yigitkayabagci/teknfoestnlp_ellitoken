# Diagnosis agent logic (Modül 1)
import json, re
from enum import Enum
from langchain_core.messages import AIMessage, HumanMessage, AnyMessage

from .cluster_agent import ClusterAgent
from agentic_network.core import AgentState
from agentic_network.core.topic_manager_util import get_messages_for_current_topic, add_message_to_dialogue
from llm.core.gemma_based_model_adapter import GemmaBasedModelAdapter
from llm.core.llm_singletons import llmSingleton


class DiognosisAgent(ClusterAgent):
    def __init__(self):
        medgemma = llmSingleton.medgemma_27b_text_it
        self.chat = GemmaBasedModelAdapter(medgemma)

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
                "output_schema": {"randevu_agent_çalıştı":"boolean"}
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
            14) Türkiye'de yürürlükte olan Tıbbi Deontoloji Nizamnamesi ve ilgili yasal düzenlemeler gereği, tanı koyma yetkisi sadece hekimlere aittir. Bu yasal zorunluluk ve kullanıcı sağlığını koruma sorumluluğum nedeniyle, kullanıcılara bir hastalık tanısı koymam mümkün değil. Tanı isteyen kullanıcılara bu mesajı ilet.
            15) Eğer tool çağrısı yaptığında bir hata alırsan, yaptığın geçmiş tool çağrısı mesajına ve error mesajına bakarak sebebini araştır. Hata senden kaynaklı çıkarsa hatanı düzelterek yeniden tool çağrısı yap. Sebep senden kaynaklı çıkmazsa kullanıcıya sistemde hata olduğunu bildir.

            """ + f"TOOLS_METADATA: {self.tools_metadata}" + """
            Bunlar senin erişimine açık tool'lar. Ekstra bir bilgiye ihtiyaç duyduğunda veya randevu oluşturmaya dair kullanıcıdan onay aldığında ilk bakman gereken bu tool listesi. Bu tool'ları çağırdığında sana hangi bilgileri sağlayacağını iyi anla (tool hakkındaki tüm bilgiler TOOLS_METADATA olarak verildi) ve gerekirse kullanmaktan çekinme! 
            Unutma kullanıcıya yanıt vermeden önce tool kullanarak elde edeceğin bilgilerin senin yanıtını geliştireceğini tespit edersen tool çağrısını gerçekleştirmelisin!
            """

        self.messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": self.role_instruction}]
            }
        ]

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
        # TODO: Change the topic flag
        self._create_report()
        return {"randevu_agent_çalıştı": True}

    def _save_txt(self, content: str, filename: str):
        with open(filename, "w") as file:
            file.write(content)

    def _create_report(self):
        system_prompt = "Konuşma geçmişindeki önemli tıbbi detayları ve semptomları özetleyen bir doktor raporu oluştur. Raporun amacı, randevu alınan doktora hastanın durumu hakkında hızlı ve kapsamlı bilgi sunmaktır. Raporda tool çağrılarından veya randevu bilgilerinden bahsetmen kesinlikle yasak. Yalnızca hastanın şikayetlerine, belirtilerine ve geçmişteki önemli tıbbi bilgilerine odaklanmak senin için çok önemli. Bu görevlerinin dışına çıkma. Randevu ile ilgili herhangi bir bilgi vermene hiç gerek yok, önemli olan hastanın semptom, şikayet ve tıbbi belirtileridir."
        self.messages[0] = {
            "role": "system",
            "content": [{"type": "text", "text": system_prompt}]
        }
        response = self.medgemma.give_prompt(messages=self.messages)
        print(self.messages)
        self.messages[0] = {
            "role": "system",
            "content": [{"type": "text", "text": self.role_instruction}]
        }
        self._save_txt(response, "report.txt")

    def _detect_function_call(self, ai_message: str, topic_messages: list[AnyMessage]) -> bool:
        match = re.search(r"<TOOL_CALL>(.*?)</TOOL_CALL>", ai_message, re.DOTALL)
        if not match: return False

        json_text = match.group(1).strip()

        try:
            call_info = json.loads(json_text)
            tool_name = call_info.get("name")
            tool_args = call_info.get("input")

            if not tool_name:
                error_message = "<TOOL_CALL> hata: \"name\" alanı eksik."
                raise ValueError(error_message)

            if not isinstance(tool_args, dict):
                error_message = "<TOOL_CALL> hata: \"input\" alanı eksik veya geçerli bir sözlük değil."
                raise ValueError(error_message)

            if tool_name not in self.AVAILABLE_TOOLS:
                error_message = f"<TOOL_CALL> hata: \"{tool_name}\" adında bir tool yoktur."
                raise ValueError(error_message)

            function_to_call = self.AVAILABLE_TOOLS[tool_name]
            result = function_to_call(**tool_args)
            return False

        except (json.JSONDecodeError, ValueError) as e:
            if isinstance(e, json.JSONDecodeError):
                error_message = f"<TOOL_CALL> hata: Hatalı JSON formatı: {e}"
            else:
                error_message = f"<TOOL_CALL> hata: {str(e)}"

            topic_messages.append(HumanMessage(error_message))
            print(f"👨‍💻 You: {error_message}")
            return True

        except Exception as e:
            error_message = f"<TOOL_CALL> hata: \"{tool_name}\" fonksiyonu çağrılırken bir hata oluştu: {e}"
            topic_messages.append(HumanMessage(error_message))
            print(f"👨‍💻 You: {error_message}")
            return True


    # ---- Internal Methods --------------------------------------------------------
    def _get_node(self, agent_state: AgentState) -> dict:
        topic_messages = get_messages_for_current_topic(agent_state)
        while True:
            response = self.chat.invoke(topic_messages)
            topic_messages.append(AIMessage(response))
            print("🤖 Chatbot:", response)
            if not self._detect_function_call(response, topic_messages): break

        add_message_to_dialogue(agent_state, AIMessage(response))
        return {}
