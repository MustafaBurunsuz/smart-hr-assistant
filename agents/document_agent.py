"""
Document Agent.
Handles official HR document retrieval (service certificate, payslip, tax plate),
offer letter generation, document uploads, and policy inquiries via RAG.
"""

from typing import Dict, Any, List

try:
    from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
except ImportError:
    class BaseMessage:
        def __init__(self, content="", **kwargs):
            self.content = content
    class AIMessage(BaseMessage):
        pass
    class HumanMessage(BaseMessage):
        pass

from tools.document_tools import (
    find_document,
    generate_offer_letter,
    upload_document,
    get_policy_document
)
from utils.helpers import get_current_employee_id
from utils.ollama_client import OllamaClient


class DocumentAgent:
    """Agent responsible for HR paperwork, official certificates, and policy RAG."""

    def __init__(self, llm=None):
        self.name = "document_agent"
        self.llm = llm
        self.ollama = OllamaClient()
        self.tools = [
            find_document,
            generate_offer_letter,
            upload_document,
            get_policy_document
        ]

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process document requests or policy queries."""
        messages: List[BaseMessage] = state.get("messages", [])
        last_user_msg = messages[-1].content if messages else ""
        text = last_user_msg.lower()
        employee_id = state.get("context", {}).get("employee_id", get_current_employee_id())

        # Check if query is an HR policy question (e.g. "evlilik izni kaç gün?", "uzaktan çalışma", "politika", "kaç gün verilir")
        is_policy_query = any(w in text for w in [
            "kaç gün", "politika", "yönetmelik", "hakkı", "nedir", "kural", "şart", "nasıl uygulanır", "el kitabı"
        ])

        if is_policy_query and not any(w in text for w in ["döküm", "bordro", "belge indir", "belge lazım"]):
            res = get_policy_document.invoke({"policy_type": last_user_msg})
            reply = res.get("message", "İlgili politika dokümanına ulaşılamadı.")

            if self.ollama.is_available() and res.get("status") == "success":
                system_prompt = (
                    "Sen Smart HR Assistant'ın İK Politikaları ve Mevzuat Danışmanısın (RAG).\n"
                    "Şirket Veritabanından Getirilen Resmi Politika Maddesi:\n"
                    f"Başlık: {res.get('title')}\n"
                    f"İçerik: {res.get('content')}\n\n"
                    "Kullanıcının sorusunu bu resmi şirket politikasına sadık kalarak, doğrudan, samimi ve net bir şekilde Türkçe yanıtla. "
                    "Politika başlığını ve varsa belge/başvuru koşullarını belirt."
                )
                ai_text = self.ollama.chat(system_prompt, [{"role": "user", "content": last_user_msg}])
                if ai_text:
                    reply = ai_text

            return {
                "messages": messages + [AIMessage(content=reply)],
                "sender": self.name,
                "next_agent": "supervisor"
            }

        # Check for offer letter generation
        if any(w in text for w in ["teklif mektubu", "iş teklifi", "offer letter"]):
            res = generate_offer_letter.invoke({
                "position": "Kıdemli Yazılım Geliştirici",
                "salary": 95000.0,
                "start_date": "2026-12-01"
            })
            reply = res.get("message", "Teklif mektubu hazırlandı.")
            return {
                "messages": messages + [AIMessage(content=reply)],
                "sender": self.name,
                "next_agent": "supervisor"
            }

        # Document retrieval (service certificate, payslip, etc.)
        doc_type = "service_certificate"
        if "bordro" in text or "maaş" in text:
            doc_type = "payslip"
        elif "vergi" in text:
            doc_type = "tax_plate"

        res = find_document.invoke({
            "doc_type": doc_type,
            "employee_id": employee_id
        })

        reply = (
            f"{res.get('doc_type', 'Belge')}nizi oluşturuyorum...\n\n"
            f"{res.get('message', 'Belgeniz hazırlandı.')}"
        )

        return {
            "messages": messages + [AIMessage(content=reply)],
            "sender": self.name,
            "next_agent": "supervisor"
        }
