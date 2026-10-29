"""
Tools for Onboarding Agent.
Handles checklist checking, onboarding kickoff, progress calculation, and mentor assignment.
"""

from typing import Dict, Any, List
from datetime import datetime

try:
    from langchain_core.tools import tool
except ImportError:
    def tool(fn):
        fn.invoke = lambda args: fn(**args) if isinstance(args, dict) else fn(args)
        return fn

from utils.helpers import load_json, save_json, get_current_employee_id
from utils.validators import validate_employee_id


@tool
def check_onboarding_checklist(employee_id: str = "") -> Dict[str, Any]:
    """Yeni başlayan çalışanın ilk gün ve ilk ay onboarding kontrol listesini sorgular.

    Args:
        employee_id: Çalışan kimlik numarası (Örn: 'EMP-001'). Boş bırakılırsa varsayılan çalışan kullanılır.

    Returns:
        Kontrol listesi maddeleri, tamamlanma durumları ve mentor bilgisi.
    """
    if not employee_id:
        employee_id = get_current_employee_id()

    checklists = load_json("onboarding_checklist.json", default=[])
    user_record = next((c for c in checklists if c.get("employee_id") == employee_id), None)

    if not user_record:
        return {
            "status": "error",
            "message": f"{employee_id} numaralı çalışan için onboarding kaydı bulunamadı."
        }

    items = user_record.get("checklist", [])
    total = len(items)
    completed = sum(1 for item in items if item.get("status") == "completed")

    return {
        "status": "success",
        "employee_id": employee_id,
        "buddy": {
            "id": user_record.get("buddy_id"),
            "name": user_record.get("buddy_name"),
            "email": user_record.get("buddy_email")
        },
        "total_tasks": total,
        "completed_tasks": completed,
        "progress_percentage": round((completed / total * 100), 1) if total > 0 else 0,
        "checklist": items
    }


@tool
def start_onboarding(employee_id: str = "") -> Dict[str, Any]:
    """Yeni işe başlayan çalışanın resmi onboarding sürecini başlatır ve adımları listeler.

    Args:
        employee_id: Çalışan kimlik numarası (Örn: 'EMP-001').

    Returns:
        Başlatılan sürecin durumu ve başlangıç maddeleri.
    """
    if not employee_id:
        employee_id = get_current_employee_id()

    employees = load_json("employees.json", default=[])
    emp = next((e for e in employees if e.get("employee_id") == employee_id), None)
    if not emp:
        return {"status": "error", "message": f"{employee_id} numaralı çalışan sistemde bulunamadı."}

    checklists = load_json("onboarding_checklist.json", default=[])
    user_record = next((c for c in checklists if c.get("employee_id") == employee_id), None)

    now_str = datetime.now().strftime("%Y-%m-%d")
    if not user_record:
        user_record = {
            "employee_id": employee_id,
            "onboarding_started": True,
            "started_at": now_str,
            "buddy_id": emp.get("buddy_id"),
            "buddy_name": emp.get("buddy_name"),
            "buddy_email": emp.get("buddy_email"),
            "checklist": [
                {"id": "CHK-01", "task": "IT ekipman teslimi (Laptop, şarj aleti, şirket kartı)", "status": "completed", "completed_at": now_str},
                {"id": "CHK-02", "task": "İK oryantasyon ve evrak imza süreci", "status": "pending", "completed_at": None},
                {"id": "CHK-03", "task": "Departman tanışma toplantısı ve takım buddy buluşması", "status": "pending", "completed_at": None},
                {"id": "CHK-04", "task": "Eğitim portalı erişimi ve zorunlu siber güvenlik eğitimleri", "status": "pending", "completed_at": None},
                {"id": "CHK-05", "task": "İlk ay hedef belirleme görüşmesi", "status": "pending", "completed_at": None}
            ]
        }
        checklists.append(user_record)
        save_json("onboarding_checklist.json", checklists)

    return {
        "status": "success",
        "message": f"{emp.get('name')} için onboarding süreci başarıyla başlatıldı.",
        "employee_name": emp.get("name"),
        "buddy_name": user_record.get("buddy_name"),
        "buddy_email": user_record.get("buddy_email"),
        "initial_checklist": user_record.get("checklist")
    }


@tool
def get_onboarding_progress(employee_id: str = "") -> Dict[str, Any]:
    """Çalışanın onboarding ilerleme oranını ve kalan maddeleri hesaplar.

    Args:
        employee_id: Çalışan kimlik numarası (Örn: 'EMP-001').

    Returns:
        İlerleme yüzdesi, tamamlanan ve bekleyen maddelerin özeti.
    """
    if not employee_id:
        employee_id = get_current_employee_id()

    checklists = load_json("onboarding_checklist.json", default=[])
    user_record = next((c for c in checklists if c.get("employee_id") == employee_id), None)

    if not user_record:
        return {"status": "error", "message": f"{employee_id} için onboarding süreci bulunamadı."}

    items = user_record.get("checklist", [])
    total = len(items)
    completed_items = [i for i in items if i.get("status") == "completed"]
    pending_items = [i for i in items if i.get("status") == "pending"]

    percentage = round((len(completed_items) / total * 100), 1) if total > 0 else 0

    return {
        "status": "success",
        "employee_id": employee_id,
        "progress_percentage": percentage,
        "completed_count": len(completed_items),
        "pending_count": len(pending_items),
        "pending_tasks": [p.get("task") for p in pending_items]
    }


@tool
def assign_buddy(employee_id: str = "", buddy_id: str = "") -> Dict[str, Any]:
    """Çalışana bir onboarding mentoru (buddy) atar veya değiştirir.

    Args:
        employee_id: Yeni çalışanın kimlik numarası (Örn: 'EMP-001').
        buddy_id: Mentor olarak atanacak çalışanın kimlik numarası (Örn: 'EMP-002').

    Returns:
        Atama onay mesajı ve mentor iletişim detayları.
    """
    if not employee_id:
        employee_id = get_current_employee_id()

    employees = load_json("employees.json", default=[])
    emp = next((e for e in employees if e.get("employee_id") == employee_id), None)
    buddy = next((e for e in employees if e.get("employee_id") == buddy_id), None)

    if not emp:
        return {"status": "error", "message": f"Çalışan ({employee_id}) bulunamadı."}
    if not buddy:
        return {"status": "error", "message": f"Mentor ({buddy_id}) bulunamadı."}

    emp["buddy_id"] = buddy_id
    emp["buddy_name"] = buddy.get("name")
    emp["buddy_email"] = buddy.get("email")
    save_json("employees.json", employees)

    # Update checklist
    checklists = load_json("onboarding_checklist.json", default=[])
    for c in checklists:
        if c.get("employee_id") == employee_id:
            c["buddy_id"] = buddy_id
            c["buddy_name"] = buddy.get("name")
            c["buddy_email"] = buddy.get("email")
            break
    save_json("onboarding_checklist.json", checklists)

    return {
        "status": "success",
        "message": f"{buddy.get('name')}, {emp.get('name')} için başarıyla mentor olarak atandı.",
        "buddy_name": buddy.get("name"),
        "buddy_email": buddy.get("email")
    }
