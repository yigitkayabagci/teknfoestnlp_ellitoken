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


class AppointmentAgent:
    def __init__(self):
        self.app = self._build_graph()
        self.system_prompt = self._get_system_prompt()

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
        
    def _get_system_prompt(self):
        tool_descriptions = json.dumps([
            {"name": t.name, "description": t.description, "parameters": t.args}
            for t in tools
        ], ensure_ascii=False)
        
        return f"""
        Sen, bir hastane ve randevu asistanısın. Görevin, kullanıcının taleplerine en uygun aracı çağırarak yanıt vermektir.
        Kullanabileceğin tool'lar ve açıklamaları:
        {tool_descriptions}
        Eğer bir tool çağırman gerekiyorsa, yanıtın sadece aşağıdaki formatta olmalıdır:
        TOOL_CALL: {{"name":"arac_adi","args":{{"param1":"deger1", "param2":"deger2"}}}}
        Eğer bir tool çağırmana gerek yoksa, kullanıcıya doğrudan yanıt ver.
        """

    # LLM'in araç çağrıları yapmasını sağlayan özel bir düğüm
    def call_llm(self, state: AgentState) -> dict:
        messages = state["all_dialog"]
        chat = GemmaBasedModelAdapter(llmSingleton.gemma_3_1b_it)
        response = chat.invoke([SystemMessage(self.system_prompt), messages])
        
        tool_call = self._parse_tool_call(response)
        
        if tool_call:
            tool_message = AIMessage(
                content="",
                tool_calls=[{
                    "name": tool_call['name'],
                    "args": tool_call['args'],
                    "id": str(uuid.uuid4())
                }]
            )
            return {"messages": [tool_message]}
        else:
            return {"messages": [AIMessage(content=response)]}

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


    def _build_graph(self):
        workflow = StateGraph(AgentState)
        tool_node = ToolNode(tools)

        # Düğümleri ekleme
        workflow.add_node("llm", self._call_llm)
        workflow.add_node("action", tool_node)
        workflow.add_node("update_state", self._update_state_with_appointment)

        # Geçişleri tanımlama
        workflow.add_edge(START, "llm")
        workflow.add_conditional_edges(
            "llm",
            self._should_continue,
            {"continue": "action", "end": END}
        )
        workflow.add_edge("action", "update_state")
        workflow.add_edge("update_state", "llm")

        # Başlangıç noktasını belirleme
        workflow.set_entry_point("llm")

        # Grafiği derleme
        return workflow.compile()

    def run_agent(self, user_prompt: str, agent_state: AgentState) -> AgentState:
        new_state = add_message_to_dialogue(agent_state, HumanMessage(content=user_prompt))
        final_state = self.app.invoke(new_state)
        return final_state


def run_langgraph_agent():
    print("Merhaba, ben sizin randevu asistanınızım. Size nasıl yardımcı olabilirim?")
    agent = AppointmentAgent()
    
    # Yeni bir AgentState nesnesi oluştur
    initial_state = AgentState(
        all_dialog=[],
        last_booked_appointment=None,
        messages=[]
    )

    while True:
        user_prompt = input("Siz: ")
        if user_prompt.lower() in ["çıkış", "exit"]:
            print("Görüşmek üzere!")
            break

        result_state = agent.run_agent(user_prompt, initial_state)
        
        # Son durumu bir sonraki döngü için güncelle
        initial_state = result_state
        
        ai_response_message = result_state['messages'][-1]
        print(f"Asistan: {ai_response_message.content}")

if __name__ == "__main__":
    run_langgraph_agent()