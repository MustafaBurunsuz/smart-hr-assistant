"""
Script to seed and restore initial sample data for Smart HR Assistant.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from utils.helpers import save_json


def seed_all_data():
    """Populate default records into data directory."""
    print("Test verileri oluşturuluyor...")

    employees = [
        {
            "employee_id": "EMP-001",
            "name": "Mustafa Yılmaz",
            "email": "mustafa.yilmaz@sirket.com",
            "department": "Yazılım Geliştirme",
            "position": "Yazılım Geliştirici",
            "start_date": "2026-10-15",
            "manager_id": "EMP-003",
            "manager_name": "Ahmet Yılmaz",
            "buddy_id": "EMP-002",
            "buddy_name": "Ayşe Demir",
            "buddy_email": "ayse.demir@sirket.com",
            "status": "active",
            "leave_balance": {
                "annual": 14,
                "sick": 3,
                "sick_used": 1,
                "excuse": 2,
                "marriage": 5,
                "maternity": 112,
                "paternity": 5
            }
        },
        {
            "employee_id": "EMP-002",
            "name": "Ayşe Demir",
            "email": "ayse.demir@sirket.com",
            "department": "Yazılım Geliştirme",
            "position": "Kıdemli Yazılım Mimarı",
            "start_date": "2023-03-01",
            "manager_id": "EMP-003",
            "manager_name": "Ahmet Yılmaz",
            "buddy_id": None,
            "buddy_name": None,
            "buddy_email": None,
            "status": "active",
            "leave_balance": {
                "annual": 20,
                "sick": 5,
                "sick_used": 0,
                "excuse": 3,
                "marriage": 5,
                "maternity": 112,
                "paternity": 5
            }
        },
        {
            "employee_id": "EMP-003",
            "name": "Ahmet Yılmaz",
            "email": "ahmet.yilmaz@sirket.com",
            "department": "Mühendislik",
            "position": "Mühendislik Direktörü",
            "start_date": "2020-01-10",
            "manager_id": None,
            "manager_name": None,
            "buddy_id": None,
            "buddy_name": None,
            "buddy_email": None,
            "status": "active",
            "leave_balance": {
                "annual": 24,
                "sick": 10,
                "sick_used": 2,
                "excuse": 5,
                "marriage": 5,
                "maternity": 112,
                "paternity": 5
            }
        }
    ]
    save_json("employees.json", employees)
    print("✓ employees.json güncellendi")

    leave_requests = [
        {
            "request_id": "REQ-1001",
            "employee_id": "EMP-001",
            "leave_type": "annual",
            "start_date": "2026-08-10",
            "end_date": "2026-08-12",
            "days": 3,
            "reason": "Yaz tatili",
            "status": "approved",
            "approved_by": "Ahmet Yılmaz",
            "created_at": "2026-08-01"
        }
    ]
    save_json("leave_requests.json", leave_requests)
    print("✓ leave_requests.json güncellendi")

    interviews = [
        {
            "interview_id": "INT-123",
            "candidate_id": "CAND-501",
            "candidate_name": "Mehmet Can",
            "interviewer_id": "EMP-001",
            "interviewer_name": "Mustafa Yılmaz",
            "date": "2026-10-30",
            "time": "14:00",
            "type": "Teknik Mülakat - Python & AI",
            "status": "scheduled",
            "meeting_link": "https://meet.google.com/abc-defg-hij"
        }
    ]
    save_json("interviews.json", interviews)
    print("✓ interviews.json güncellendi")

    onboarding_checklist = [
        {
            "employee_id": "EMP-001",
            "onboarding_started": True,
            "started_at": "2026-10-15",
            "buddy_id": "EMP-002",
            "buddy_name": "Ayşe Demir",
            "buddy_email": "ayse.demir@sirket.com",
            "checklist": [
                {"id": "CHK-01", "task": "IT ekipman teslimi (Laptop, aksesuarlar)", "status": "completed", "completed_at": "2026-10-15"},
                {"id": "CHK-02", "task": "IK oryantasyon (Bekleniyor)", "status": "pending", "completed_at": None},
                {"id": "CHK-03", "task": "Departman tanışması (Bekleniyor)", "status": "pending", "completed_at": None},
                {"id": "CHK-04", "task": "Eğitim portalı erişimi (Bekleniyor)", "status": "pending", "completed_at": None}
            ]
        }
    ]
    save_json("onboarding_checklist.json", onboarding_checklist)
    print("✓ onboarding_checklist.json güncellendi")

    print("🎉 Tüm test verileri başarıyla oluşturuldu!")


if __name__ == "__main__":
    seed_all_data()
