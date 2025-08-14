from langchain_core.messages import SystemMessage, HumanMessage

from agentic_network.agents.topic_manager_cluster.agents import TopicAgent
from agentic_network.core.topic_manager_util import format_dialog
from agentic_network.core import AgentState, GraphRoutes
from llm.core.llm_singletons import llmSingleton
from llm.core.gemma_based_model_adapter import GemmaBasedModelAdapter


class NewTopicAgent(TopicAgent):
    def __init__(self):
        pass

    # ---- Internal Methods --------------------------------------------------------d
    def _get_node(self, agent_state: AgentState) -> dict:
        print("-NEW TOPIC AGENT-")

        llm = llmSingleton.gemma_3_1b_it
        chat = GemmaBasedModelAdapter(llm)
        current_message = agent_state["current_message"]
        thoughts = format_dialog(agent_state["thoughts"])
        system_message = self._build_system_message(current_message, thoughts)

        return {
            "thoughts": [chat.invoke([system_message, HumanMessage(content="Follow the instruction above and answer.")])]
        }

    def _build_system_message(self, message: str, thoughts: str) -> SystemMessage:
        system_message = SystemMessage(content=(
            f"""You are part of a medical assistant. Your sole task is **agent routing for a new topic**: based ONLY on the latest user message, choose which specialized agent should handle it.

    AGENTS & THEIR SCOPES
    - DIAGNOSIS_AGENT
      Purpose: Clinical questions and symptom triage.
      Route here when the message:
      • Describes symptoms, concerns, or a medical problem (“fever and cough”, “rash on my arm”).
      • Asks about causes, severity, risks, next clinical steps, labs/imaging interpretation, or treatment options.
      • Asks about medications in a clinical sense (side effects, interactions, dosing, safety, effectiveness).
      • Mentions urgent/emergency-sounding issues (chest pain, shortness of breath, suicide/self-harm) — still classify here.
      Examples: “My throat hurts and I have a fever.” / “Is 101°F dangerous?” / “What does a high WBC mean?” / “Is it safe to take ibuprofen with amoxicillin?”
    
    - APPOINTMENT_AGENT
      Purpose: Care logistics, scheduling, and visit-related admin.
      Route here when the message:
      • Requests to book, reschedule, confirm, or cancel appointments, tests, or procedures.
      • Specifies dates/times/locations/clinicians, preferences, or availability.
      • Handles visit logistics: telehealth vs. in-person, directions, preparation instructions, paperwork.
      • Handles visit-specific admin: insurance eligibility for this visit, referrals, prescription refills as an administrative request (“send to Walgreens”), change pharmacy for this prescription, provider/hospital choice for this booking.
      Examples: “Can you book me with Dr. Chen tomorrow at 3?” / “Move my MRI to next week.” / “Cancel my appointment.” / “Send the refill to CVS on 5th.”
    
    - SMALL_TALK_AGENT
      Purpose: Polite chatter and meta-assistant talk.
      Route here when the message:
      • Is greetings, thanks, acknowledgments, chit-chat, jokes, or short non-medical pleasantries.
      • Asks about the assistant itself (“what’s your name?”, “who made you?”) or generic “ok/thanks”.
      Examples: “Thanks!” / “hi there” / “lol that’s helpful” / “what are you?”
    
    - OUT_OF_TOPIC_AGENT
      Purpose: Everything irrelevant to healthcare tasks.
      Route here when the message:
      • Is clearly non-medical (shopping, travel, programming help, sports, etc.).
      • Is spam, empty, emoji-only, or not actionable.
      • Is administrative/billing not tied to a specific visit and cannot be addressed by scheduling logistics (e.g., “explain my insurance plan in general”).
      Examples: “Write me a Python script.” / “Plan my vacation.” / “What’s the stock price of XYZ?”
    
    INPUT
    - user_input — the latest user message (string):
    {message}
    
    DECISION RULES
    - Classify the **single best agent** for this new topic. Do not assume continuity with prior topics.
    - If the message contains both clinical details and an explicit scheduling action (e.g., “I have ear pain; book me with ENT tomorrow”), prefer **APPOINTMENT_AGENT** (the actionable request).
    - If there’s clinical content but no explicit scheduling/admin action, choose **DIAGNOSIS_AGENT**.
    - If the content is only greetings/thanks/acknowledgments or meta-chat, choose **SMALL_TALK_AGENT**.
    - If none of the above clearly applies or it’s unrelated to healthcare tasks, choose **OUT_OF_TOPIC_AGENT**.
    - Ambiguous? Prefer DIAGNOSIS_AGENT over OUT_OF_TOPIC_AGENT **only if** there is some medical substance (symptom/condition/med/drug/test term). Otherwise use OUT_OF_TOPIC_AGENT.
    
    STRICT OUTPUT (ONE LINE ONLY)
    Always print EXACTLY one of:
    - FINAL ANSWER: {GraphRoutes.DIAGNOSIS_AGENT}
    - FINAL ANSWER: {GraphRoutes.APPOINTMENT_AGENT}
    - FINAL ANSWER: {GraphRoutes.SMALL_TALK_AGENT}
    - FINAL ANSWER: {GraphRoutes.OUT_OF_TOPIC_AGENT}
    - THOUGHT: [your latest thoughts]
    (Do not output anything else.)
    
    LANGUAGE & STYLE
    - Apply the same rules for any language.
    - Ignore superficial formatting/casing; focus on meaning.
    - You are not giving medical advice — only attributing the new message to a topic.
    
    PROCESS
    Optionally reflect first using:
    THOUGHT: [brief reasoning about candidate agents and why]
    Then output exactly one final line as specified in STRICT OUTPUT.
    
    EXAMPLES
    1) “I’ve had a cough for a week and green phlegm.” → FINAL ANSWER: DIAGNOSIS_AGENT
    2) “Book me with Dr. Patel next Tuesday afternoon.” → FINAL ANSWER: APPOINTMENT_AGENT
    3) “Thanks!” → FINAL ANSWER: SMALL_TALK_AGENT
    4) “Can you explain my BluePlus plan in general?” → FINAL ANSWER: OUT_OF_TOPIC_AGENT
    5) “Refill my amoxicillin to Walgreens on 5th.” → FINAL ANSWER: APPOINTMENT_AGENT
    6) “Is it safe to take ibuprofen with amoxicillin?” → FINAL ANSWER: DIAGNOSIS_AGENT
    
    THOUGHTS:
    These are your lates thoughts on this task if you've had any:
    {thoughts}
    """
        ))
        return system_message
