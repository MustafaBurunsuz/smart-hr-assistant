"""
Tools for Leave Agent.
Handles querying leave balances, requesting leave, canceling requests, and fetching leave history.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

try:
    from langchain_core.tools import tool
except ImportError:
    def tool(fn):
        fn.invoke = lambda args: fn(**args) if isinstance(args, dict) else fn(args)
        return fn

from utils.helpers import load_json, save_json, get_current_employee_id
from utils.validators import validate_employee_id, validate_date_string, validate_positive_integer


@tool
def get_leave_balance(employee_id: str = "") -> Dict[str, Any]:
    """Çalışanın kalan yıllık, hastalık ve mazeret izin bakiyelerini sorgular.

    Args:
        employee_id: Çalışan ID'si (Örn: 'EMP-001'). Boşsa varsayılan çalışan sorgulanır.

    Returns:
        İzin bakiyeleri tablosu veya çalışan bulunamadı hatası.
    """
    if not employee_id:
        employee_id = get_current_employee_id()

    employees = load_json("employees.json", default=[])
    emp = next((e for e in employees if e.get("employee_id") == employee_id), None)

    if not emp:
        return {
            "status": "error",
            "message": f"'{employee_id}' kimlikli çalışan sistemde bulunamadı."
        }

    balance = emp.get("leave_balance", {})
    return {
        "status": "success",
        "employee_id": employee_id,
        "employee_name": emp.get("name"),
        "annual_leave": balance.get("annual", 0),
        "sick_leave": balance.get("sick", 0),
        "sick_used": balance.get("sick_used", 0),
        "excuse_leave": balance.get("excuse", 0),
        "marriage_leave": balance.get("marriage", 5),
        "summary": (
            f"2026 yılı için izin bakiyeleriniz:\n"
            f"📅 Yıllık izin: {balance.get('annual', 0)} gün\n"
            f"🏥 Hastalık: {balance.get('sick', 0)} gün (kullanılan: {balance.get('sick_used', 0)})\n"
            f"💔 Mazeret: {balance.get('excuse', 0)} gün"
        )
    }


@tool
def request_leave(
    leave_type: str = "annual",
    start_date: str = "",
    days: int = 1,
    reason: str = "Şahsi izin",
    employee_id: str = ""
) -> Dict[str, Any]:
    """Yeni bir izin talebi oluşturur ve yöneticinin onayına gönderir.

    Args:
        leave_type: İzin türü ('annual' / yıllık, 'sick' / hastalık, 'excuse' / mazeret, 'marriage' / evlilik).
        start_date: İzin başlangıç tarihi (YYYY-MM-DD veya DD.MM.YYYY formatında).
        days: Kullanılacak izin gün sayısı (tam sayı).
        reason: İzin gerekçesi veya açıklaması.
        employee_id: Çalışan ID'si. Boş bırakılırsa varsayılan çalışan kullanılır.

    Returns:
        Oluşturulan izin talebinin detayları ve onaylayıcı yönetici bilgisi.
    """
    if not employee_id:
        employee_id = get_current_employee_id()

    employees = load_json("employees.json", default=[])
    emp = next((e for e in employees if e.get("employee_id") == employee_id), None)
    if not emp:
        return {"status": "error", "message": f"'{employee_id}' kimlikli çalışan bulunamadı."}

    # Normalize leave type
    type_map = {
        "yıllık": "annual", "annual": "annual",
        "hastalık": "sick", "sick": "sick",
        "mazeret": "excuse", "excuse": "excuse",
        "evlilik": "marriage", "marriage": "marriage"
    }
    normalized_type = type_map.get(leave_type.lower().strip(), "annual")

    # Validate days
    valid_int, num_days = validate_positive_integer(days)
    if not valid_int:
        return {"status": "error", "message": "İzin süresi pozitif bir tam sayı olmalıdır."}

    # Balance check for annual leave
    current_balance = emp.get("leave_balance", {}).get(normalized_type, 0)
    if normalized_type == "annual" and num_days > current_balance:
        return {
            "status": "error",
            "message": f"Yetersiz yıllık izin bakiyesi. Mevcut bakiyeniz {current_balance} gündür."
        }

    # Validate date
    is_valid_date, norm_start_date = validate_date_string(start_date)
    if not is_valid_date:
        # Default to tomorrow if not given
        norm_start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Calculate end date
    start_dt = datetime.strptime(norm_start_date, "%Y-%m-%d")
    end_dt = start_dt + timedelta(days=num_days - 1)
    end_date_str = end_dt.strftime("%Y-%m-%d")

    leave_requests = load_json("leave_requests.json", default=[])
    new_request_id = f"REQ-{len(leave_requests) + 1001}"

    new_request = {
        "request_id": new_request_id,
        "employee_id": employee_id,
        "leave_type": normalized_type,
        "start_date": norm_start_date,
        "end_date": end_date_str,
        "days": num_days,
        "reason": reason,
        "status": "pending_approval",
        "approved_by": emp.get("manager_name", "Yönetici"),
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }

    leave_requests.append(new_request)
    save_json("leave_requests.json", leave_requests)

    # Deduct balance preview
    if normalized_type in emp.get("leave_balance", {}):
        emp["leave_balance"][normalized_type] = max(0, emp["leave_balance"][normalized_type] - num_days)
        save_json("employees.json", employees)

    type_tr = {
        "annual": "Yıllık İzin",
        "sick": "Hastalık İzni",
        "excuse": "Mazeret İzni",
        "marriage": "Evlilik İzni"
    }.get(normalized_type, "İzin")

    return {
        "status": "success",
        "request_id": new_request_id,
        "leave_type": type_tr,
        "start_date": norm_start_date,
        "end_date": end_date_str,
        "days": num_days,
        "approval_status": "pending_approval",
        "manager": emp.get("manager_name", "Ahmet Yılmaz"),
        "message": (
            f"İzin talebiniz oluşturuldu!\n\n"
            f"📋 Talep Detayları:\n"
            f"- Tür: {type_tr}\n"
            f"- Tarih: {norm_start_date} - {end_date_str} ({num_days} gün)\n"
            f"- Durum: Onay Bekliyor\n"
            f"- Onaylayıcı: {emp.get('manager_name', 'Ahmet Yılmaz')} (Yöneticiniz)"
        )
    }


@tool
def cancel_leave_request(request_id: str) -> Dict[str, Any]:
    """Daha önce oluşturulmuş bir izin talebini iptal eder.

    Args:
        request_id: İptal edilecek izin talep kodu (Örn: 'REQ-1001').

    Returns:
        İptal işlem sonucu.
    """
    leave_requests = load_json("leave_requests.json", default=[])
    target = next((r for r in leave_requests if r.get("request_id") == request_id), None)

    if not target:
        return {"status": "error", "message": f"'{request_id}' nolu izin talebi bulunamadı."}

    if target.get("status") == "cancelled":
        return {"status": "warning", "message": f"{request_id} nolu talep zaten iptal edilmiş."}

    target["status"] = "cancelled"
    save_json("leave_requests.json", leave_requests)

    # Return balance
    employees = load_json("employees.json", default=[])
    emp = next((e for e in employees if e.get("employee_id") == target.get("employee_id")), None)
    if emp and target.get("leave_type") in emp.get("leave_balance", {}):
        emp["leave_balance"][target.get("leave_type")] += target.get("days", 0)
        save_json("employees.json", employees)

    return {
        "status": "success",
        "request_id": request_id,
        "message": f"{request_id} numaralı izin talebi başarıyla iptal edildi ve izin bakiyeniz iade edildi."
    }


@tool
def get_leave_history(employee_id: str = "") -> Dict[str, Any]:
    """Çalışanın geçmiş ve bekleyen tüm izin taleplerini listeler.

    Args:
        employee_id: Çalışan ID'si. Boşsa aktif çalışan kullanılır.

    Returns:
        İzin geçmişi kayıtları.
    """
    if not employee_id:
        employee_id = get_current_employee_id()

    leave_requests = load_json("leave_requests.json", default=[])
    user_requests = [r for r in leave_requests if r.get("employee_id") == employee_id]

    return {
        "status": "success",
        "employee_id": employee_id,
        "total_requests": len(user_requests),
        "requests": user_requests
    }
