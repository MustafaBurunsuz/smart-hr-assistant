"""
Supervisor Agent (Multi-Agent Coordinator & Routing).
Analyzes user intent and orchestrates routing across specialized agents:
Onboarding, Leave, Document, and Interview, using LangGraph.
"""

import os
from typing import Dict, Any, List, Optional, TypedDict, Annotated, Sequence
import operator

try:
    from langgraph.graph import StateGraph, START, END
    from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
except ImportError:
    START = "__start__"
    END = "__end__"
    class BaseMessage:
        def __init__(self, content="", **kwargs):
            self.content = content
    class AIMessage(BaseMessage):
        pass
    class HumanMessage(BaseMessage):
        pass

    class StateGraph:
        def __init__(self, state_schema):
            self.nodes = {}
            self.edges = {}
            self.conditional_edges = {}

        def add_node(self, name, action):
            self.nodes[name] = action

        def add_edge(self, start, end):
            self.edges[start] = end

        def add_conditional_edges(self, source, router, path_map):
            self.conditional_edges[source] = (router, path_map)

        def compile(self):
            return CompiledGraph(self.nodes, self.edges, self.conditional_edges)

    class CompiledGraph:
        def __init__(self, nodes, edges, conditional_edges):
            self.nodes = nodes
            self.edges = edges
            self.conditional_edges = conditional_edges

        def invoke(self, state):
            curr_state = dict(state)
            # Run supervisor node
            sup_out = self.nodes["supervisor"](curr_state)
            curr_state.update(sup_out)

            # Route conditionally
            if "supervisor" in self.conditional_edges:
                router, path_map = self.conditional_edges["supervisor"]
                next_key = router(curr_state)
                target = path_map.get(next_key, "fallback")
                if target != END and target in self.nodes:
                    node_out = self.nodes[target](curr_state)
                    if "messages" in node_out:
                        # Append or update messages
                        curr_state["messages"] = node_out["messages"]
                    if "context" in node_out:
                        curr_state["context"] = node_out["context"]
                    if "sender" in node_out:
                        curr_state["sender"] = node_out["sender"]

            return curr_state

from agents.onboarding_agent import OnboardingAgent
from agents.leave_agent import LeaveAgent
from agents.document_agent import DocumentAgent
from agents.interview_agent import InterviewAgent
from utils.ollama_client import OllamaClient


class AgentState(TypedDict):
    """LangGraph State representation for the multi-agent system."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str
    next_agent: Optional[str]
    context: Dict[str, Any]


class SupervisorAgent:
    """Central routing and coordinator agent for Smart HR Assistant."""

    def __init__(self, llm=None):
        self.llm = llm
        self.ollama = OllamaClient()
        self.onboarding_agent = OnboardingAgent(llm)
        self.leave_agent = LeaveAgent(llm)
        self.document_agent = DocumentAgent(llm)
        self.interview_agent = InterviewAgent(llm)
        self.graph = self._build_graph()

    def route_message(self, user_text: str, context: Dict[str, Any]) -> str:
        """Analyze intent and return target destination node name.

        Args:
            user_text: Plain text user query.
            context: Session context dictionary.

        Returns:
            One of: 'greeting', 'help', 'onboarding', 'leave', 'document', 'interview', 'fallback'.
        """
        text = user_text.lower().strip()

        # Check ongoing context slots
        if context.get("pending_leave_request"):
            return "leave"
        if context.get("reschedule_target"):
            return "interview"

        # Help request
        if text in ["help", "yardım", "/help", "?", "neler yapabilirsin"]:
            return "help"

        # Greetings
        greeting_words = ["merhaba", "selam", "günaydın", "iyi günler", "hey", "merhabalar", "iyi akşamlar"]
        if any(text == g or text.startswith(g + " ") or text.startswith(g + "!") for g in greeting_words):
            if not any(k in text for k in ["izin", "başladım", "mülakat", "belge", "gün"]):
                return "greeting"

        # Onboarding Keywords
        onboarding_keywords = [
            "başladım", "yeni işe", "ilk gün", "onboarding", "oryantasyon",
            "buddy", "mentor", "ekipman teslim", "tanışma"
        ]
        if any(k in text for k in onboarding_keywords):
            return "onboarding"

        # Leave Keywords
        leave_keywords = [
            "izin", "bakiyem", "yıllık izin", "hastalık", "mazeret", "kaç gün iznim",
            "izin kullanmak", "izin geçmiş", "izin durum"
        ]
        if any(k in text for k in leave_keywords) and not ("evlilik izni kaç gün" in text or "politika" in text):
            return "leave"

        # Document and Policy (RAG) Keywords
        doc_keywords = [
            "belge", "hizmet dökümü", "bordro", "maaş bordrosu", "vergi levhası",
            "teklif mektubu", "politika", "el kitabı", "evlilik izni", "yönetmelik",
            "uzaktan çalışma", "mesai", "kıdem tazminatı", "ihbar"
        ]
        if any(k in text for k in doc_keywords):
            return "document"

        # Interview Keywords
        interview_keywords = [
            "mülakat", "görüşme", "aday", "ertele", "takvim", "interview"
        ]
        if any(k in text for k in interview_keywords):
            return "interview"

        # Fallback
        return "fallback"

    def supervisor_node(self, state: AgentState) -> Dict[str, Any]:
        """Supervisor entrypoint node that determines routing."""
        messages = state.get("messages", [])
        last_msg = messages[-1].content if messages else ""
        context = state.get("context", {})

        next_destination = self.route_message(last_msg, context)
        return {
            "sender": "supervisor",
            "next_agent": next_destination,
            "context": context
        }

    def greeting_node(self, state: AgentState) -> Dict[str, Any]:
        """Handles greetings and welcome messages."""
        reply = (
            "Merhaba! Smart HR Assistant'a hoş geldiniz.\n"
            "Size nasıl yardımcı olabilirim?\n"
            "(Onboarding, izin, belge veya mülakat işlemleri)"
        )
        if self.ollama.is_available():
            msgs = state.get("messages", [])
            last_text = msgs[-1].content if msgs else "Merhaba"
            ai_text = self.ollama.chat(
                "Sen Smart HR Assistant'ın Supervisor Asistanısın. Kullanıcıyı sıcak, profesyonel bir şekilde karşıla. Onboarding, izin, belge ve mülakat konularında yardımcı olabileceğini belirt.",
                [{"role": "user", "content": last_text}]
            )
            if ai_text:
                reply = ai_text

        return {
            "messages": [AIMessage(content=reply)],
            "sender": "greeting_agent",
            "next_agent": END
        }

    def help_node(self, state: AgentState) -> Dict[str, Any]:
        """Returns comprehensive capability help menu."""
        reply = (
            "YAPABİLECEKLERİM:\n\n"
            "🎯 ONBOARDING:\n"
            "- İlk gün yapılacaklar (check_onboarding_checklist)\n"
            "- Onboarding durumu ve ilerleme yüzdesi\n"
            "- Mentor (Buddy) bilgisi ve ataması\n\n"
            "📅 İZİN:\n"
            "- İzin bakiyesi sorgulama (Yıllık, Hastalık, Mazeret)\n"
            "- İzin talebi oluşturma (Çok adımlı diyalog)\n"
            "- İzin iptali ve geçmişi\n\n"
            "📄 BELGE:\n"
            "- Hizmet dökümü oluşturma\n"
            "- Maaş bordrosu ve Vergi levhası\n"
            "- İK politikaları sorgulama (RAG / Vektör Veritabanı)\n\n"
            "🎤 MÜLAKAT:\n"
            "- Mülakat planlama ve erteleme\n"
            "- Mülakat iptali\n"
            "- Görüşmeci takvimi görüntüleme\n\n"
            "Örnek: '5 gün izin kullanmak istiyorum'\n"
            "Çıkış: 'exit' veya 'çıkış'"
        )
        return {
            "messages": [AIMessage(content=reply)],
            "sender": "help_agent",
            "next_agent": END
        }

    def fallback_node(self, state: AgentState) -> Dict[str, Any]:
        """Fallback node for queries outside HR scope."""
        reply = (
            "Bu konuda yardımcı olamıyorum.\n"
            "Ben İnsan Kaynakları ve Onboarding Asistanıyım. "
            "Onboarding adımları, izin sorgulama/talep, resmi belge temini ve mülakat takvimi konularında soru sorabilirsiniz.\n"
            "Yardım için 'help' yazabilirsiniz."
        )
        if self.ollama.is_available():
            msgs = state.get("messages", [])
            last_text = msgs[-1].content if msgs else ""
            ai_text = self.ollama.chat(
                "Sen Smart HR Assistant'sın. Kullanıcı İK kapsamı dışındaki bir konu hakkında soru sordu. "
                "Nazikçe bu konuda yardımcı olamayacağını, bir İK ve Onboarding asistanı olduğunu ve onboarding adımları, izin bakiyesi/talebi, resmi belgeler ve mülakat takvimi konularında yardımcı olabileceğini Türkçe olarak açıkla.",
                [{"role": "user", "content": last_text}]
            )
            if ai_text:
                reply = ai_text

        return {
            "messages": [AIMessage(content=reply)],
            "sender": "fallback_agent",
            "next_agent": END
        }

    def onboarding_node(self, state: AgentState) -> Dict[str, Any]:
        return self.onboarding_agent.process(state)

    def leave_node(self, state: AgentState) -> Dict[str, Any]:
        return self.leave_agent.process(state)

    def document_node(self, state: AgentState) -> Dict[str, Any]:
        return self.document_agent.process(state)

    def interview_node(self, state: AgentState) -> Dict[str, Any]:
        return self.interview_agent.process(state)

    def _build_graph(self):
        """Construct and compile the LangGraph workflow."""
        builder = StateGraph(AgentState)

        # Add Nodes
        builder.add_node("supervisor", self.supervisor_node)
        builder.add_node("greeting", self.greeting_node)
        builder.add_node("help", self.help_node)
        builder.add_node("fallback", self.fallback_node)
        builder.add_node("onboarding", self.onboarding_node)
        builder.add_node("leave", self.leave_node)
        builder.add_node("document", self.document_node)
        builder.add_node("interview", self.interview_node)

        # Start at supervisor
        builder.add_edge(START, "supervisor")

        # Conditional routing from supervisor
        def choose_next_agent(state: AgentState) -> str:
            return state.get("next_agent", "fallback")

        builder.add_conditional_edges(
            "supervisor",
            choose_next_agent,
            {
                "greeting": "greeting",
                "help": "help",
                "fallback": "fallback",
                "onboarding": "onboarding",
                "leave": "leave",
                "document": "document",
                "interview": "interview"
            }
        )

        # Each specialist node ends the round
        builder.add_edge("greeting", END)
        builder.add_edge("help", END)
        builder.add_edge("fallback", END)
        builder.add_edge("onboarding", END)
        builder.add_edge("leave", END)
        builder.add_edge("document", END)
        builder.add_edge("interview", END)

        return builder.compile()

    def run(self, user_input: str, conversation_messages: Optional[List[BaseMessage]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute one conversation turn through the LangGraph workflow.

        Args:
            user_input: Message string from the user.
            conversation_messages: History of BaseMessages.
            context: Session memory state dictionary.

        Returns:
            Dict containing final response string, updated messages, and updated context.
        """
        history = list(conversation_messages) if conversation_messages else []
        ctx = dict(context) if context else {}

        human_msg = HumanMessage(content=user_input)
        input_state: AgentState = {
            "messages": history + [human_msg],
            "sender": "user",
            "next_agent": None,
            "context": ctx
        }

        output_state = self.graph.invoke(input_state)
        final_msgs = output_state.get("messages", [])
        last_response = final_msgs[-1].content if final_msgs else "Bir hata oluştu."

        return {
            "response": last_response,
            "messages": final_msgs,
            "context": output_state.get("context", ctx),
            "sender": output_state.get("sender", "assistant")
        }
