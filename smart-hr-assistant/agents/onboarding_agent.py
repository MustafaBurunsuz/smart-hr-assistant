"""
Onboarding Agent.
Specialist agent managing the 30-day onboarding journey for new hires,
checklist tracking, mentor connections, and orientation milestones.
"""

import os
import json
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

from tools.onboarding_tools import (
    check_onboarding_checklist,
    start_onboarding,
    get_onboarding_progress,
    assign_buddy
)
from utils.helpers import get_current_employee_id
from utils.ollama_client import OllamaClient


class OnboardingAgent:
    """Agent responsible for new employee onboarding workflows."""

    def __init__(self, llm=None):
        self.name = "onboarding_agent"
        self.llm = llm
        self.ollama = OllamaClient()
        self.tools = [
            check_onboarding_checklist,
            start_onboarding,
            get_onboarding_progress,
            assign_buddy
        ]

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming messages and return agent response.

        Args:
            state: LangGraph agent state dictionary.

        Returns:
            Updated state containing the assistant response.
        """
        messages: List[BaseMessage] = state.get("messages", [])
        last_user_msg = messages[-1].content if messages else ""
        text = last_user_msg.lower()
        employee_id = state.get("context", {}).get("employee_id", get_current_employee_id())

        # Determine sub-intent and execute tool
        if any(w in text for w in ["ilerleme", "yüzde", "durum", "kaç tamamlandı", "ne kadar"]):
            tool_res = get_onboarding_progress.invoke({"employee_id": employee_id})
        elif any(w in text for w in ["mentor", "buddy", "atan"]):
            tool_res = check_onboarding_checklist.invoke({"employee_id": employee_id})
        else:
            tool_res = check_onboarding_checklist.invoke({"employee_id": employee_id})
            if tool_res.get("status") != "success":
                start_onboarding.invoke({"employee_id": employee_id})
                tool_res = check_onboarding_checklist.invoke({"employee_id": employee_id})

        # Try real Ollama AI generation
        ai_reply = None
        if self.ollama.is_available():
            system_prompt = (
                "Sen Smart HR Assistant'ın Onboarding Uzmanısın.\n"
                "Görevin yeni işe başlayan çalışanlara ilk gün ve ilk ay adımlarında rehberlik etmek.\n"
                "Aktif Çalışan: Mustafa Yılmaz (EMP-001)\n"
                "Mentorü (Buddy): Ayşe Demir (ayse.demir@sirket.com)\n"
                f"Sistem Kontrol Listesi Verisi: {json.dumps(tool_res, ensure_ascii=False)}\n\n"
                "Kullanıcının sorusunu yukarıdaki verilere dayanarak samimi, net ve maddeler halinde Türkçe yanıtla. "
                "İlk gün yapılacaklar listesini (IT ekipman teslimi, İK oryantasyon vb.) ve mentor bilgisini mutlaka belirt."
            )
            chat_msgs = [{"role": "user", "content": last_user_msg}]
            ai_reply = self.ollama.chat(system_prompt, chat_msgs, temperature=0.3)

        if ai_reply:
            reply = ai_reply
        else:
            # Deterministic fallback
            items = tool_res.get("checklist", [])
            formatted_items = []
            for idx, it in enumerate(items, 1):
                icon = "✅" if it.get("status") == "completed" else "⏳"
                status_str = "Tamamlandı" if it.get("status") == "completed" else "Bekleniyor"
                formatted_items.append(f"{idx}. {icon} {it.get('task')} ({status_str})")

            checklist_str = "\n".join(formatted_items)
            buddy = tool_res.get("buddy", {})

            reply = (
                "Hoş geldiniz! Onboarding sürecinizi başlatıyorum...\n\n"
                f"İlk gün yapılacaklar:\n"
                f"{checklist_str}\n\n"
                f"Mentorünüz: {buddy.get('name', 'Ayşe Demir')} ({buddy.get('email', 'ayse.demir@sirket.com')})\n"
                f"İlk hafta ilerlemenizi takip edeceğim!"
            )

        new_message = AIMessage(content=reply)
        return {
            "messages": messages + [new_message],
            "sender": self.name,
            "next_agent": "supervisor"
        }
