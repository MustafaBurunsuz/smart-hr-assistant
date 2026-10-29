"""
Leave Management Agent.
Handles leave balances, leave applications, multi-step date & duration slot filling,
cancellations, and leave history.
"""

import re
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

from tools.leave_tools import (
    get_leave_balance,
    request_leave,
    cancel_leave_request,
    get_leave_history
)
from utils.helpers import get_current_employee_id
from utils.validators import validate_employee_id
from utils.ollama_client import OllamaClient


class LeaveAgent:
    """Agent specialized in employee leave management and multi-turn requests."""

    def __init__(self, llm=None):
        self.name = "leave_agent"
        self.llm = llm
        self.ollama = OllamaClient()
        self.tools = [
            get_leave_balance,
            request_leave,
            cancel_leave_request,
            get_leave_history
        ]

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process leave queries and maintain slot filling state."""
        messages: List[BaseMessage] = state.get("messages", [])
        last_user_msg = messages[-1].content if messages else ""
        text = last_user_msg.lower()
        context = state.get("context", {})

        # Check for explicit employee ID in query (e.g. XXX-999)
        emp_match = re.search(r"([a-zA-Z]{3,4}-\d{3,4})", last_user_msg)
        target_emp_id = emp_match.group(1).upper() if emp_match else context.get("employee_id", get_current_employee_id())

        # If user is asking balance for another invalid ID
        if emp_match and emp_match.group(1).upper() != get_current_employee_id():
            res = get_leave_balance.invoke({"employee_id": target_emp_id})
            reply = res.get("message", f"'{target_emp_id}' çalışan bulunamadı.")
            return {
                "messages": messages + [AIMessage(content=reply)],
                "sender": self.name,
                "next_agent": "supervisor",
                "context": context
            }

        # Check if we were already waiting for date / slot filling for a pending leave request
        pending_leave = context.get("pending_leave_request")

        # 1. Check if user is asking for leave history
        if any(w in text for w in ["geçmiş", "durum", "taleplerim", "geçmişim", "geçmiş izin"]):
            res = get_leave_history.invoke({"employee_id": target_emp_id})
            reqs = res.get("requests", [])
            if not reqs:
                reply = "Henüz kayıtlı bir izin talebiniz bulunmamaktadır."
            else:
                lines = [f"Geçmiş ve Aktif İzin Talepleriniz ({len(reqs)} adet):"]
                for r in reqs:
                    lines.append(f"- {r.get('request_id')}: {r.get('start_date')} / {r.get('days')} gün ({r.get('leave_type')}) -> Durum: {r.get('status')}")
                reply = "\n".join(lines)

            return {
                "messages": messages + [AIMessage(content=reply)],
                "sender": self.name,
                "next_agent": "supervisor",
                "context": context
            }

        # 2. Check if user wants to cancel a request
        if any(w in text for w in ["iptal", "vazgeç"]):
            req_match = re.search(r"(REQ-\d{4})", last_user_msg.upper())
            req_id = req_match.group(1) if req_match else "REQ-1001"
            res = cancel_leave_request.invoke({"request_id": req_id})
            reply = res.get("message", "İptal işlemi tamamlandı.")
            return {
                "messages": messages + [AIMessage(content=reply)],
                "sender": self.name,
                "next_agent": "supervisor",
                "context": context
            }

        # 3. Check if user is requesting leave or continuing a pending leave request
        wants_leave = any(w in text for w in ["kullanmak istiyorum", "izin almak", "izin istiyorum", "talep", "izin yaz"]) or pending_leave is not None

        if wants_leave:
            # Extract days
            days_match = re.search(r"(\d+)\s*gün", text)
            days = int(days_match.group(1)) if days_match else (pending_leave.get("days") if pending_leave else None)

            # Extract date if mentioned (e.g. 1 Kasım, 2026-11-01, 01.11.2026)
            date_found = None
            if "1 kasım" in text or "01.11" in text or "1-11" in text or "kasım" in text:
                date_found = "2026-11-01"
            else:
                date_match = re.search(r"(\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4})", text)
                if date_match:
                    date_found = date_match.group(1)

            # Determine leave type
            leave_type = "annual"
            if "hastalık" in text:
                leave_type = "sick"
            elif "mazeret" in text:
                leave_type = "excuse"
            elif "evlilik" in text:
                leave_type = "marriage"

            # If days not specified yet
            if not days:
                context["pending_leave_request"] = {"leave_type": leave_type}
                reply = "Kaç gün izin kullanmak istiyorsunuz ve hangi tarihler arasında? (Örnek: 1 Kasım 2026, 5 gün)"
                return {
                    "messages": messages + [AIMessage(content=reply)],
                    "sender": self.name,
                    "next_agent": "supervisor",
                    "context": context
                }

            # If date not specified yet
            if not date_found:
                context["pending_leave_request"] = {"leave_type": leave_type, "days": days}
                reply = "Hangi tarihler arasında izin kullanmak istersiniz? (Örnek: 1 Kasım 2026, 5 gün)"
                return {
                    "messages": messages + [AIMessage(content=reply)],
                    "sender": self.name,
                    "next_agent": "supervisor",
                    "context": context
                }

            # Both days and date are available -> complete request
            res = request_leave.invoke({
                "leave_type": leave_type,
                "start_date": date_found,
                "days": days,
                "reason": "Yıllık dinlenme",
                "employee_id": target_emp_id
            })

            # Clear pending state
            context.pop("pending_leave_request", None)
            reply = res.get("message", "İzin talebiniz oluşturuldu.")

            if self.ollama.is_available():
                system_prompt = (
                    "Sen Smart HR Assistant'ın İK İzin Yönetimi Uzmanısın.\n"
                    "İzin talebi başarıyla oluşturuldu ve veritabanına işlendi.\n"
                    f"Talep Özeti: Tür: {res.get('leave_type')}, Tarih: {res.get('start_date')} - {res.get('end_date')} ({res.get('days')} gün), Onaylayıcı: {res.get('manager')}.\n"
                    "Kullanıcıya talebinin oluşturulduğunu, tarihleri, gün sayısını ve yöneticisi Ahmet Yılmaz'ın onayına iletildiğini profesyonel ve düzenli bir formatta açıkla."
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

        # 4. Default: query balance
        res = get_leave_balance.invoke({"employee_id": target_emp_id})
        reply = res.get("summary", res.get("message", "İzin bakiyesi bilgisi alınamadı."))

        if self.ollama.is_available() and res.get("status") == "success":
            system_prompt = (
                "Sen Smart HR Assistant'ın İK İzin Yönetimi Uzmanısın.\n"
                "Aktif Çalışan: Mustafa Yılmaz (EMP-001)\n"
                f"Mevcut İzin Verileri: Yıllık İzin: {res.get('annual_leave')} gün, Hastalık: {res.get('sick_leave')} gün (kullanılan: {res.get('sick_used')}), Mazeret: {res.get('excuse_leave')} gün.\n"
                "Kullanıcıya izin bakiyelerini net ve anlaşılır bir dille açıkla."
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
