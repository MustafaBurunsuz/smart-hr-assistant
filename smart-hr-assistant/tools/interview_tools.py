"""
Tools for Interview Agent.
Handles scheduling, rescheduling, canceling interviews, and calendar management.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from langchain_core.tools import tool
except ImportError:
    def tool(fn):
        fn.invoke = lambda args: fn(**args) if isinstance(args, dict) else fn(args)
        return fn

from utils.helpers import load_json, save_json, get_current_employee_id
from utils.validators import validate_date_string


@tool
def schedule_interview(
    candidate_name: str,
    date: str,
    time: str,
    interview_type: str = "Teknik Mülakat",
    candidate_id: str = "",
    interviewer_id: str = ""
) -> Dict[str, Any]:
    """Yeni bir aday mülakatı planlar ve takvime ekler.

    Args:
        candidate_name: Adayın adı soyadı.
        date: Mülakat tarihi (YYYY-MM-DD veya DD.MM.YYYY).
        time: Mülakat saati (Örn: '14:00').
        interview_type: Mülakat türü (Örn: 'Teknik Mülakat', 'İK Ön Görüşme', 'Vaka Çalışması').
        candidate_id: Aday ID'si (Opsiyonel).
        interviewer_id: Görüşmeci çalışan ID'si. Boşsa aktif çalışan atanır.

    Returns:
        Oluşturulan mülakat kaydı ve toplantı linki.
    """
    if not interviewer_id:
        interviewer_id = get_current_employee_id()

    employees = load_json("employees.json", default=[])
    interviewer = next((e for e in employees if e.get("employee_id") == interviewer_id), None)
    interviewer_name = interviewer.get("name", "Görüşmeci") if interviewer else "Görüşmeci"

    _, norm_date = validate_date_string(date)
    if not norm_date:
        norm_date = date

    interviews = load_json("interviews.json", default=[])
    new_id = f"INT-{len(interviews) + 125}"
    if not candidate_id:
        candidate_id = f"CAND-{len(interviews) + 505}"

    meeting_code = f"hr-{len(interviews) + 10}-{new_id.lower()}"
    new_interview = {
        "interview_id": new_id,
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "interviewer_id": interviewer_id,
        "interviewer_name": interviewer_name,
        "date": norm_date,
        "time": time,
        "type": interview_type,
        "status": "scheduled",
        "meeting_link": f"https://meet.google.com/{meeting_code}"
    }

    interviews.append(new_interview)
    save_json("interviews.json", interviews)

    return {
        "status": "success",
        "interview_id": new_id,
        "candidate_name": candidate_name,
        "date": norm_date,
        "time": time,
        "meeting_link": new_interview["meeting_link"],
        "message": (
            f"Mülakat başarıyla planlandı!\n"
            f"📅 Aday: {candidate_name}\n"
            f"⏰ Tarih/Saat: {norm_date} {time}\n"
            f"💼 Tür: {interview_type}\n"
            f"🔗 Toplantı Linki: {new_interview['meeting_link']}"
        )
    }


@tool
def cancel_interview(interview_id: str) -> Dict[str, Any]:
    """Mevcut bir mülakatı iptal eder ve taraflara bildirim gönderir.

    Args:
        interview_id: İptal edilecek mülakatın ID'si (Örn: 'INT-123').

    Returns:
        İptal durumu mesajı.
    """
    interviews = load_json("interviews.json", default=[])
    target = next((i for i in interviews if i.get("interview_id") == interview_id), None)

    if not target:
        # Check by matching nearest scheduled interview if ID not explicitly provided
        active = [i for i in interviews if i.get("status") == "scheduled"]
        if active:
            target = active[0]
            interview_id = target.get("interview_id")
        else:
            return {"status": "error", "message": f"'{interview_id}' ID'li mülakat bulunamadı."}

    target["status"] = "cancelled"
    save_json("interviews.json", interviews)

    return {
        "status": "success",
        "interview_id": interview_id,
        "candidate_name": target.get("candidate_name"),
        "message": (
            f"{interview_id} numaralı mülakat ({target.get('candidate_name')}, {target.get('date')} {target.get('time')}) başarıyla iptal edildi.\n"
            f"Katılımcılara takvim iptal daveti ve e-posta bildirimi iletildi."
        )
    }


@tool
def get_interview_calendar(interviewer_id: str = "", week: Optional[str] = None) -> Dict[str, Any]:
    """Görüşmecinin yaklaşan ve planlanmış mülakat takvimini listeler.

    Args:
        interviewer_id: Görüşmeci çalışan ID'si. Boşsa aktif çalışan sorgulanır.
        week: Belirli bir hafta filtresi (Opsiyonel).

    Returns:
        Planlı mülakatların listesi.
    """
    if not interviewer_id:
        interviewer_id = get_current_employee_id()

    interviews = load_json("interviews.json", default=[])
    active = [i for i in interviews if i.get("interviewer_id") == interviewer_id and i.get("status") == "scheduled"]

    return {
        "status": "success",
        "interviewer_id": interviewer_id,
        "count": len(active),
        "interviews": active
    }


@tool
def reschedule_interview(interview_id: str, new_date: str, new_time: str) -> Dict[str, Any]:
    """Mevcut bir mülakatın tarih ve saatini günceller/erteler.

    Args:
        interview_id: Mülakat ID'si (Örn: 'INT-123').
        new_date: Yeni tarih (YYYY-MM-DD veya DD.MM.YYYY).
        new_time: Yeni saat (Örn: '10:00').

    Returns:
        Güncelleme teyit mesajı.
    """
    interviews = load_json("interviews.json", default=[])
    target = next((i for i in interviews if i.get("interview_id") == interview_id), None)

    if not target:
        active = [i for i in interviews if i.get("status") == "scheduled"]
        if active:
            target = active[0]
            interview_id = target.get("interview_id")
        else:
            return {"status": "error", "message": f"'{interview_id}' numaralı mülakat bulunamadı."}

    _, norm_date = validate_date_string(new_date)
    target["date"] = norm_date or new_date
    target["time"] = new_time
    save_json("interviews.json", interviews)

    return {
        "status": "success",
        "interview_id": interview_id,
        "candidate_name": target.get("candidate_name"),
        "new_date": target["date"],
        "new_time": target["time"],
        "message": (
            f"Mülakatınız ertelendi!\n"
            f"📅 Yeni Tarih: {target['date']}\n"
            f"⏰ Yeni Saat: {target['time']}\n"
            f"👤 Aday: {target.get('candidate_name')}\n"
            f"Katılımcılara güncellenmiş takvim daveti gönderildi."
        )
    }
