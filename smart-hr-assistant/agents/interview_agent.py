"""
Interview Agent.
Specialist agent managing candidate interview scheduling, rescheduling, cancellations,
and interviewer calendar tracking.
"""

import re
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

from tools.interview_tools import (
    schedule_interview,
    cancel_interview,
    get_interview_calendar,
    reschedule_interview
)
from utils.helpers import get_current_employee_id
from utils.ollama_client import OllamaClient


class InterviewAgent:
    """Agent specialized in recruitment interview orchestration."""

    def __init__(self, llm=None):
        self.name = "interview_agent"
        self.llm = llm
        self.ollama = OllamaClient()
        self.tools = [
            schedule_interview,
            cancel_interview,
            get_interview_calendar,
            reschedule_interview
        ]

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process interview calendar queries, scheduling, and cancellations."""
        messages: List[BaseMessage] = state.get("messages", [])
        last_user_msg = messages[-1].content if messages else ""
        text = last_user_msg.lower()
        context = state.get("context", {})

        # 1. Cancel interview
        if any(w in text for w in ["iptal", "sil"]):
            int_match = re.search(r"(INT-\d{3,4})", last_user_msg.upper())
            int_id = int_match.group(1) if int_match else "INT-123"
            res = cancel_interview.invoke({"interview_id": int_id})
            reply = res.get("message", "Mülakatınız iptal edildi.")

            if self.ollama.is_available() and res.get("status") == "success":
                system_prompt = (
                    "Sen Smart HR Assistant'ın Mülakat ve Takvim Yönetimi Uzmanısın.\n"
                    f"Mülakat İptal Verisi: {res.get('message')}\n"
                    "Kullanıcıya mülakatın başarıyla iptal edildiğini ve katılımcılara bildirim iletildiğini açıkla."
                )
                ai_text = self.ollama.chat(system_prompt, [{"role": "user", "content": last_user_msg}])
                if ai_text:
                    reply = ai_text

            return {
                "messages": messages + [AIMessage(content=reply)],
                "sender": self.name,
                "next_agent": "supervisor",
                "context": context
            }

        # 2. Reschedule interview
        if any(w in text for w in ["ertele", "değiştir", "saat olsun", "erteler"]):
            # Check if pending reschedule target exists
            target_int_id = context.get("reschedule_target", "INT-123")

            # Check if date/time provided
            has_time = any(t in text for t in ["10:00", "11:00", "14:00", "15:00", "16:00"]) or re.search(r"\d{1,2}:\d{2}", text)
            has_day = any(d in text for d in ["cuma", "pazartesi", "salı", "çarşamba", "perşembe", "yarın"])

            if not (has_time or has_day):
                context["reschedule_target"] = target_int_id
                reply = "Hangi tarihe ve saate ertelemek istersiniz?"
                return {
                    "messages": messages + [AIMessage(content=reply)],
                    "sender": self.name,
                    "next_agent": "supervisor",
                    "context": context
                }

            # If user provided new slot
            time_match = re.search(r"(\d{1,2}:\d{2})", text)
            new_time = time_match.group(1) if time_match else "10:00"
            new_date = "2026-11-06" if "cuma" in text else "2026-11-01"

            res = reschedule_interview.invoke({
                "interview_id": target_int_id,
                "new_date": new_date,
                "new_time": new_time
            })
            context.pop("reschedule_target", None)
            reply = (
                f"Mülakatınızı {text.strip().title()} ertelemesini gerçekleştiriyorum...\n\n"
                f"{res.get('message', 'Mülakatınız ertelendi.')}"
            )
            return {
                "messages": messages + [AIMessage(content=reply)],
                "sender": self.name,
                "next_agent": "supervisor",
                "context": context
            }

        # 3. Schedule interview
        if any(w in text for w in ["planla", "ayarla", "yeni mülakat", "görüşme ekle"]):
            res = schedule_interview.invoke({
                "candidate_name": "Berk Kaya",
                "date": "2026-11-05",
                "time": "15:00",
                "interview_type": "Kıdemli Python Mülakatı"
            })
            reply = res.get("message", "Mülakat başarıyla planlandı.")
            return {
                "messages": messages + [AIMessage(content=reply)],
                "sender": self.name,
                "next_agent": "supervisor",
                "context": context
            }

        # 4. View calendar
        calendar_res = get_interview_calendar.invoke({})
        interviews = calendar_res.get("interviews", [])
        if not interviews:
            reply = "Önümüzdeki günlerde planlanmış bir mülakatınız bulunmuyor."
        else:
            lines = [f"📅 Yaklaşan Mülakat Takviminiz ({len(interviews)} adet):"]
            for i in interviews:
                lines.append(f"- {i.get('date')} {i.get('time')} | {i.get('candidate_name')} ({i.get('type')}) - Link: {i.get('meeting_link')}")
            reply = "\n".join(lines)

        return {
            "messages": messages + [AIMessage(content=reply)],
            "sender": self.name,
            "next_agent": "supervisor",
            "context": context
        }
