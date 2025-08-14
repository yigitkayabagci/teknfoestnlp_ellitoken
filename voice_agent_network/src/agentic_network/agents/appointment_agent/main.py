from __future__ import annotations

import re
from typing import Optional, Dict

from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from copy import copy
import json, uuid

from agentic_network.core import AgentState
from agentic_network.core.topic_manager_util import add_message_to_dialogue
from llm.core.gemma_based_model_adapter import GemmaBasedModelAdapter
from llm.core.llm_singletons import llmSingleton
from agent_tools import ToolManager

# 1. ToolManager örneğini oluştur ve araçları tanımla
tool_manager_instance = ToolManager()


@tool
def authenticate_user(identity_number: str) -> str:
    """
    Kullanıcının kimlik numarasını doğrulayarak randevu alma işlemlerine devam etmesini sağlar.
    Kullanıcı 'randevu almak istiyorum' dediğinde ve kimlik bilgisi belirtmediğinde önce bu tool'u çağırmak için bir istem oluşturmalısın.
    """
    try:
        return json.dumps(tool_manager_instance.authenticate_user(identity_number), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Kimlik doğrulama sırasında bir hata oluştu: {str(e)}"}, ensure_ascii=False)

@tool
def get_hospitals_by_city_and_district(city: str, district: str) -> str:
    """Belirtilen şehir ve ilçedeki hastanelerin listesini döndürür.
    Konuma göre arama yapmak için tercih edilen araçtır.
    KURAL: Kullanıcı hem şehir hem de ilçe girerse, 'şehir' ve 'ilçe'yi tek bir 'konum' parametresi olarak değil, ayrı ayrı doldurmalısınız.
    Hiçbir hastane bulunamazsa, şu mesajı döndürün: 'Hastane bulunamadı, lütfen şehir/ilçeyi tekrar kontrol edin."""
    return json.dumps(tool_manager_instance.get_hospitals_by_city_and_district(city, district), ensure_ascii=False)

@tool
def get_hospitals_by_location(location: str) -> str:
    """Belirtilen şehir veya ilçedeki hastanelerin listesini döndürür. Bu aracı yalnızca şehir ve ilçe aynı anda belirtilmemişse kullanın."""
    return json.dumps(tool_manager_instance.get_hospitals_by_location(location), ensure_ascii=False)

@tool
def get_policlinics_by_hospital_name(hospital_name: str) -> str:
    """
    Belirtilen hastanedeki tüm polikliniklerin listesini döndürür.
    Bu araç, bir kullanıcı belirli bir hastaneyi seçtikten sonra bölüm veya polikliniklerin listesini istediğinde kullanılmalıdır.
    """
    return json.dumps(tool_manager_instance.get_policlinics_by_hospital_name(hospital_name), ensure_ascii=False)

@tool
def get_doctors_by_hospital_and_policlinic(hospital_name: str, policlinic: str) -> str:
    """Belirli bir hastane ve poliklinikte çalışan doktorların listesini döndürür."""
    return json.dumps(tool_manager_instance.get_doctors_by_hospital_and_policlinic(hospital_name, policlinic), ensure_ascii=False)

@tool
def get_available_dates_for_doctor(doctor_name: str) -> str:
    """Belirli bir doktor için uygun tüm tarihlerin listesini döndürür. Bu araç, bir doktor seçildikten sonra, ancak belirli bir tarih istenmeden önce kullanılmalıdır."""
    return json.dumps(tool_manager_instance.get_available_dates_for_doctor(doctor_name), ensure_ascii=False)

@tool
def get_available_appointments(doctor_name: str, date: str) -> str:
    """Bu fonksiyon yalnızca doktorun müsaitlik listesinde bulunan ve henüz rezerve edilmemiş zamanları döndürür."""
    return json.dumps(tool_manager_instance.get_available_appointments(doctor_name, date), ensure_ascii=False)

@tool
def book_appointment(doctor_name: str, date: str, time: str) -> str:
    """Eğer kullanıcı kimlik bilgisini doğru girdiyse belirli bir doktor, tarih ve saat için randevu oluşturur.
    YAnlış girdiyse hata döndürür."""
    if not tool_manager_instance.authenticated:
        return json.dumps({"status": "error", "message": "Randevu almadan önce kimlik doğrulama yapmanız gerekiyor. Lütfen kimlik numaranızı girin."}, ensure_ascii=False)
    return tool_manager_instance.book_appointment(doctor_name, date, time)

@tool
def cancel_appointment_by_id(appointment_id: int) -> str:
    """Randevu listesinden benzersiz tanımlayıcısını (ID) kullanarak rezerve edilmiş bir randevuyu iptal eder."""
    return tool_manager_instance.cancel_appointment_by_id(appointment_id)

@tool
def get_my_appointments() -> str:
    """Kullanıcının mevcut tüm randevularını listeler ve her birine benzersiz bir kimlik (ID) atar. Randevuları iptal etmek için önce bu aracı kullanarak mevcut randevuları görmeniz önerilir."""
    return json.dumps(tool_manager_instance.get_my_appointments(), ensure_ascii=False)

# Tüm araçları listele
tools = [
    authenticate_user,
    get_hospitals_by_city_and_district,
    get_hospitals_by_location,
    get_policlinics_by_hospital_name,
    get_doctors_by_hospital_and_policlinic,
    get_available_dates_for_doctor,
    get_available_appointments,
    book_appointment,
    cancel_appointment_by_id,
    get_my_appointments
]


def parse_tool_call(text: str) -> Optional[Dict]:
    if not text: return None

    tool_call_re = re.compile(
        r'^TOOL_CALL:\s*(\{.*\})\s*$',
        flags=re.DOTALL,
    )

    m = tool_call_re.match(text.strip())
    if not m: return None

    try:
        return json.loads(m.group(1))

    except Exception:
        return None

# LLM'in araç çağrıları yapmasını sağlayan özel bir düğüm
def call_llm(state: AgentState) -> dict:
    messages = state["all_dialog"]

    tool_descriptions = json.dumps([
        {
            "name": t.name,
            "description": t.description,
            "parameters": t.args
        }
        for t in tools
    ], ensure_ascii=False)
    
    system_prompt = f"""
    Sen, bir hastane ve randevu asistanısın. Görevin, kullanıcının taleplerine en uygun aracı çağırarak yanıt vermektir.
    Kullanabileceğin tool'lar ve açıklamaları:
    {tool_descriptions}

    Eğer bir tool çağırman gerekiyorsa, yanıtın sadece aşağıdaki formatta olmalıdır:
    TOOL_CALL: {{"name":"arac_adi","args":{{"param1":"deger1", "param2":"deger2"}}}}

    Eğer bir tool çağırmana gerek yoksa, kullanıcıya doğrudan yanıt ver.
    """
    
    chat = GemmaBasedModelAdapter(llmSingleton.gemma_3_1b_it)
    response = chat.invoke([SystemMessage(system_prompt), messages])
    
    # Kendi istemcimizin çıktısını LangGraph'ın beklediği formata dönüştürün
    tool_call = parse_tool_call(response)
    
    if tool_call:
        tool_message = AIMessage(
            content="",
            tool_calls=[{
                "name": tool_call['name'],
                "args": tool_call['args'],
                "id": str(uuid.uuid4())  # Burada benzersiz bir ID oluşturup ekliyoruz
            }]
        )
        return {"messages": [tool_message]}
    else:
        return {"messages": [AIMessage(content=response)]}

tool_node = ToolNode(tools)

def should_continue(state: AgentState) -> str:
    last_message = state['messages'][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "continue"
    else:
        return "end"

def update_state_with_appointment(state: AgentState) -> dict:
    print("---Durum Güncelleniyor---")
    last_message = state['messages'][-1]
    
    if not isinstance(last_message, ToolMessage):
        print("Son mesaj bir ToolMessage değil.")
        return state

    try:
        tool_output = json.loads(last_message.content)
        # last_message.tool_call doğrudan kullanılamaz, ToolMessage'ın kendisi bir tool_call içermez.
        # Bu bilgi genellikle AIMessage içinde yer alır. Bu nedenle bir önceki AIMessage'ı kontrol etmeliyiz.
        tool_call_info = None
        if len(state['messages']) >= 2 and isinstance(state['messages'][-2], AIMessage) and state['messages'][-2].tool_calls:
            tool_call_info = state['messages'][-2].tool_calls[0] # İlk tool_call'ı al

        if tool_call_info and tool_call_info.get('name') == 'book_appointment' and isinstance(tool_output, dict) and tool_output.get("status") == "success":
            new_state = copy(state)
            new_state['last_booked_appointment'] = {
                "doctor_name": tool_output.get("randevu", {}).get("doktor"),
                "date": tool_output.get("randevu", {}).get("tarih"),
                "time": tool_output.get("randevu", {}).get("saat"),
                "hospital": tool_output.get("randevu", {}).get("hastane_adi")
            }
            print(f"Yeni randevu bilgisi duruma eklendi: {new_state['last_booked_appointment']}")
            return new_state
    except (json.JSONDecodeError, KeyError, IndexError) as e: # IndexError'ı da ekleyelim
        print(f"Tool çıktısı işlenirken hata oluştu: {e}")
        pass
            
    return state


# Grafiği oluşturma
workflow = StateGraph(AgentState)

# Düğümleri ekleme
workflow.add_node("llm", call_llm)
workflow.add_node("action", tool_node)
workflow.add_node("update_state", update_state_with_appointment)

# Geçişleri tanımlama
workflow.add_edge(START, "llm")
workflow.add_conditional_edges(
    "llm",
    should_continue,
    {"continue": "action", "end": END}
)
workflow.add_edge("action", "update_state")
workflow.add_edge("update_state", "llm")

# Başlangıç noktasını belirleme
workflow.set_entry_point("llm")

# Grafiği derleme
app = workflow.compile()

# Main conversation loop (replaces your original run_agent function)
def run_langgraph_agent(agent_state: AgentState):
    system_prompt = """
    Rolünüz ve Yönergeleriniz
    Bir hastane ve doktor randevu sistemi için akıllı bir asistansınız. Temel göreviniz, kullanıcıların hastane, doktor ve randevu bilgilerine erişimini kolaylaştırmak ve rezervasyon sürecine yardımcı olmaktır. Doğru bilgi sağlamak ve görevleri tamamlamak için sağlanan tool'ları kullanmalısınız.

    **İLK KURAL**: Kullanıcı hangi dille seninle iletişime giriyorsa, sen de aynı dille cevap vermek zorundasın.
    **KURAL**: Unutma kullanıcıya tool bahsetmek kesinlikle yasak! Zaten kullanıcının tool erişimi yoktur, kullanamaz! Sistem tool kullanmayı kullanıcıdan gizli bir şekilde arka planda ele alır, tool çağrısı mesajını kullanıcıya iletmez.
    **KURAL**: Tool isimleri, parametreleri veya "TOOL_CALL" formatı kullanıcıya asla gösterilmez.

    **KİMLİK DOĞRULAMA KURALI**:
    Randevu oluşturma işlemi başlamadan önce, kullanıcının girdiği kimlik numarasını **doğrudan ve olduğu gibi** `authenticate_user` aracına iletmelisiniz.
    Kimlik doğrulama başarıyla tamamlanana kadar başka hiçbir adıma veya araca geçmeyin.
    Başarılı olursa, kullanıcıdan hastane aramak için şehir ve ilçe bilgisi isteyin.
    Başarısız olursa, kimlik bilgisinin yanlış olduğunu nazikçe belirtin ve kullanıcıdan tekrar denemesini isteyin.



    Kullanım Talimatları
    
    1. **Gerekli Bilgilerin Sorgulanması**: Kullanıcının talebini işlemek için gereken parametreler eksikse, eksik bilgileri **açıkça ve tek tek** isteyin.
        * **ÖZEL KURAL**: Yeni bir randevu talebi başlattığınızda (örneğin, "KBB'de randevu almak istiyorum"), her zaman önce hastane konumu (şehir ve ilçe) için get_hospitals_by_city_and_district tool'unun parametrelerini sormalısınız.
        * **ÖZEL KURAL**: Hastane bilgilerini aldıktan sonra, eğer poliklinik bilgisi yoksa (yani NONE'sa) get_policlinics_by_hospital_name aracıyla poliklinikleri listelemelisın. Daha sonrasında hangi polikliniği istediğini kullanıcıya sormalı, cevabı almalısın.
        * **KRİTİK GÜNCELLEME**: Kullanıcı açıkça bir doktor listesi isterse (örneğin, "hangi doktorlar var?", "doktorları listele"), mevcut bilgilerle (hastane, poliklinik) `get_doctors_by_hospital_and_policlinic` tool'unu kullanarak önceliklendirme yapmalısınız. Bu aşamada **tarih sormayın**, çünkü kullanıcı bir rezervasyon değil, bir liste talep ediyor.

    2. **Yanıtları Açıkça Biçimlendirin**: Tool'lardaki ham verileri (JSON listeleri veya sözlükler gibi) doğrudan kullanıcıya göstermeyin. Bunun yerine, bu verileri net, iyi yapılandırılmış ve okunabilir bir metne dönüştürün.
        * **Kullanıcı için Liste Seçenekleri**: Bir tool bir öğe listesi (hastaneler, klinikler, doktorlar veya müsait saatler) döndürdüğünde, bu seçenekleri kullanıcıya açıkça sunmalı ve bir seçim yapmasını istemelisiniz. Bu, etkileşimli ve yönlendirilmiş bir konuşma yaratır. * Örnek: "A (il), B (ilçe)'deki hastaneler: C Hastanesi ve D Hastanesi. Hangisini tercih edersiniz?"

    3. **Hataları Zarifçe Yönetin**: Bir tool boş bir sonuç döndürürse (örneğin, boş bir liste [] veya '{"error": ...}' hata mesajı), bunu kullanıcıya anlayışlı ve çözüm odaklı bir şekilde iletin.
        * Örnek: "Üzgünüm, kriterlerinize uygun herhangi bir hastane bulamadım. Lütfen şehir ve ilçe adlarını kontrol edip tekrar deneyebilir misiniz?"
        * Örnek: "Bu poliklinikte şu anda müsait doktor yok. Başka bir poliklinik veya hastaneye bakmamı ister misiniz?"

    4. **Randevuları Onayla**: Bir randevu başarıyla alındığında ("status": "success"), **ilgili tüm randevu ayrıntılarını (doktor adı, hastane adı, şehir, ilçe, poliklinik, tarih ve saat)** içeren net ve onaylayıcı bir mesaj verin.
        * **Örnek**: "Randevunuz Kardiyoloji bölümünden Dr. Ayşe Yılmaz'a Ankara, Çankaya'daki Ankara Şehir Hastanesi'nde 10 Ağustos 2025, saat 09:00 için başarıyla tamamlandı. İyi günler geldi."

    5. **Randevu İptali**: Randevu iptal etme işlemi belirli bir şekilde gerçekleştirilmelidir:
        * Bir kullanıcı randevusunu iptal etmek istediğinde (örneğin, "randevumu iptal et"), önce **`get_my_appointments`** aracını kullanarak mevcut tüm randevuların listesini alın.
        * Bu listeyi, her randevu için benzersiz bir kimlikle kullanıcıya sunun.
        * Kullanıcıdan iptal etmek istediği randevunun kimliğini belirtmesini isteyin.
        * Kullanıcı bir kimlik verdikten sonra, verilen kimlikle **`cancel_appointment_by_id`** aracını kullanın.
        * Bir randevu başarıyla iptal edildiğinde ("status": "success"), açık ve onaylayıcı bir mesaj sağlayın.
        * **Örnek**: "Dr. Ayşe Yılmaz'a Ankara Şehir Hastanesi'nde 10 Ağustos 2025 tarihindeki randevunuz başarıyla iptal edildi."

    6. **Tool Seçimine Öncelik Verin**: Kullanıcının isteğine en uygun aracı seçmek için tool tanımlarını dikkatlice okuyun.
        * `get_hospitals_by_city_and_district`: Kullanıcı hem şehri hem de ilçeyi aynı anda girdiğinde her zaman bu aracı kullanın. Parametreleri doğru şekilde ayrıştırmayı unutmayın.
        * `get_available_dates_for_doctor`: **Kullanıcı bir doktor seçtikten sonra, uygun tarihleri bulup kullanıcıya sunmak için bu aracı kullanın. Manuel olarak tarih sormayın; bunun yerine, kullanıcıya aracın çıktısına göre net bir seçenek listesi sunun.**
        * `get_hospitals_by_location`: Kullanıcı hem şehri hem de ilçeyi girdiğinde bu aracı kullanmamalısınız. Bu durumlarda, `get_hospitals_by_city_and_district` tarafından istenen eksik parametreleri istemelisiniz.

    7. **Birden Fazla Randevuyu Yönetme**: Bir kullanıcının aynı doktorla birden fazla randevu veya farklı bir zaman aralığı için randevu almak isteyebileceğini unutmayın. Başarılı bir randevu alımından sonra, kullanıcıya mevcut diğer randevu aralıkları hakkında bilgi verin ve başka bir randevu almak isteyip istemediğini sorun.

    Diğer tüm tool'lar: Bu tool'ları yalnızca gerekli tüm parametreler mevcut olduğunda çağırın.
    """

    # full_conversation_history = [SystemMessage(content=system_prompt)]


    print("Merhaba, ben sizin randevu asistanınızım. Size nasıl yardımcı olabilirim?")
    while True:
        user_prompt = input("Siz: ")

        var = add_message_to_dialogue(agent_state, HumanMessage(content=user_prompt))

        final_state = app.invoke({"messages": full_conversation_history})

        ai_response_message = final_state['messages'][-1]
        
        # Son yanıtı al ve kullanıcıya göster
        ai_response_content = ai_response_message.content
        add_message_to_dialogue(agent_state, AIMessage(content=ai_response_message))
        print(f"Asistan: {ai_response_content}")


if __name__ == "__main__":
    run_langgraph_agent()


