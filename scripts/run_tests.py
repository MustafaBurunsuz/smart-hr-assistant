"""
Test runner for Smart HR Assistant.
Executes the 10 evaluation test scenarios defined in the master plan.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from agents.supervisor import SupervisorAgent
from scripts.seed_data import seed_all_data


def run_all_tests():
    """Execute all 10 scenario tests sequentially."""
    print("=" * 60)
    print("🧪 SMART HR ASSISTANT - OTOMATİK TEST SENARYOLARI")
    print("=" * 60)

    # Seed fresh test data before running tests
    seed_all_data()
    print("-" * 60)

    supervisor = SupervisorAgent()
    passed = 0
    total = 10

    # ----------------------------------------------------
    # Test 1: Greeting & Routing
    # ----------------------------------------------------
    print("\n[TEST 1] Greeting & Routing")
    res1 = supervisor.run("Merhaba")
    print(f"Girdi: 'Merhaba'\nYanıt:\n{res1['response']}")
    if "Smart HR Assistant" in res1["response"] or "Hoş geldiniz" in res1["response"]:
        print("✅ TEST 1 BAŞARILI: [SUPERVISOR] -> greeting")
        passed += 1
    else:
        print("❌ TEST 1 BAŞARISIZ")

    # ----------------------------------------------------
    # Test 2: Onboarding Checklist
    # ----------------------------------------------------
    print("\n[TEST 2] Onboarding Checklist")
    res2 = supervisor.run("Yeni işe başladım, ne yapmam lazım?")
    print(f"Girdi: 'Yeni işe başladım, ne yapmam lazım?'\nYanıt:\n{res2['response']}")
    if "Onboarding" in res2["response"] and ("ekipman" in res2["response"].lower() or "checklist" in res2["response"].lower()):
        print("✅ TEST 2 BAŞARILI: [SUPERVISOR] -> onboarding -> check_onboarding_checklist()")
        passed += 1
    else:
        print("❌ TEST 2 BAŞARISIZ")

    # ----------------------------------------------------
    # Test 3: Leave Balance
    # ----------------------------------------------------
    print("\n[TEST 3] Leave Balance")
    res3 = supervisor.run("Kaç gün iznim var?")
    print(f"Girdi: 'Kaç gün iznim var?'\nYanıt:\n{res3['response']}")
    if "Yıllık izin" in res3["response"] or "14 gün" in res3["response"]:
        print("✅ TEST 3 BAŞARILI: [SUPERVISOR] -> leave -> get_leave_balance()")
        passed += 1
    else:
        print("❌ TEST 3 BAŞARISIZ")

    # ----------------------------------------------------
    # Test 4: Leave Request (Multi-Step)
    # ----------------------------------------------------
    print("\n[TEST 4] Leave Request (Multi-Step)")
    res4_step1 = supervisor.run("5 gün izin kullanmak istiyorum")
    print(f"Adım 1: '5 gün izin kullanmak istiyorum'\nYanıt: {res4_step1['response']}")

    # Provide date in next turn using session context
    res4_step2 = supervisor.run(
        "1 Kasım, 5 gün",
        conversation_messages=res4_step1["messages"],
        context=res4_step1["context"]
    )
    print(f"Adım 2: '1 Kasım, 5 gün'\nYanıt:\n{res4_step2['response']}")
    if "oluşturuldu" in res4_step2["response"].lower() and "onay" in res4_step2["response"].lower():
        print("✅ TEST 4 BAŞARILI: [SUPERVISOR] -> leave -> request_leave()")
        passed += 1
    else:
        print("❌ TEST 4 BAŞARISIZ")

    # ----------------------------------------------------
    # Test 5: Document Generation
    # ----------------------------------------------------
    print("\n[TEST 5] Document Generation")
    res5 = supervisor.run("Hizmet dökümü belgesi lazım")
    print(f"Girdi: 'Hizmet dökümü belgesi lazım'\nYanıt:\n{res5['response']}")
    if "Hizmet Dökümü" in res5["response"] and "pdf" in res5["response"].lower():
        print("✅ TEST 5 BAŞARILI: [SUPERVISOR] -> document -> find_document()")
        passed += 1
    else:
        print("❌ TEST 5 BAŞARISIZ")

    # ----------------------------------------------------
    # Test 6: RAG - Policy Query
    # ----------------------------------------------------
    print("\n[TEST 6] RAG - Policy Query")
    res6 = supervisor.run("Evlilik izni kaç gün?")
    print(f"Girdi: 'Evlilik izni kaç gün?'\nYanıt:\n{res6['response']}")
    if "Evlilik İzni" in res6["response"] and "5 gün" in res6["response"]:
        print("✅ TEST 6 BAŞARILI: [SUPERVISOR] -> document -> RAG search -> cevap")
        passed += 1
    else:
        print("❌ TEST 6 BAŞARISIZ")

    # ----------------------------------------------------
    # Test 7: Interview Cancellation
    # ----------------------------------------------------
    print("\n[TEST 7] Interview Cancellation")
    res7 = supervisor.run("Yarın saat 14:00'te mülakatım var, iptal et")
    print(f"Girdi: 'Yarın saat 14:00'te mülakatım var, iptal et'\nYanıt:\n{res7['response']}")
    if "iptal edildi" in res7["response"].lower():
        print("✅ TEST 7 BAŞARILI: [SUPERVISOR] -> interview -> cancel_interview()")
        passed += 1
    else:
        print("❌ TEST 7 BAŞARISIZ")

    # ----------------------------------------------------
    # Test 8: Conversation Memory
    # ----------------------------------------------------
    print("\n[TEST 8] Conversation Memory")
    m1 = supervisor.run("5 gün izin kullanmak istiyorum")
    m2 = supervisor.run("1 Kasım'da", conversation_messages=m1["messages"], context=m1["context"])
    print(f"Turn 1: '5 gün izin kullanmak istiyorum'\nTurn 2: '1 Kasım'da'\nYanıt:\n{m2['response']}")
    if "5 gün" in m2["response"] and ("2026-11-01" in m2["response"] or "1 Kasım" in m2["response"]):
        print("✅ TEST 8 BAŞARILI: Memory'den context başarıyla çekildi")
        passed += 1
    else:
        print("❌ TEST 8 BAŞARISIZ")

    # ----------------------------------------------------
    # Test 9: Error Handling
    # ----------------------------------------------------
    print("\n[TEST 9] Error Handling (Invalid Employee)")
    res9 = supervisor.run("XXX-999 çalışanının izin bakiyesi")
    print(f"Girdi: 'XXX-999 çalışanının izin bakiyesi'\nYanıt:\n{res9['response']}")
    if "bulunamadı" in res9["response"].lower():
        print("✅ TEST 9 BAŞARILI: Graceful error message")
        passed += 1
    else:
        print("❌ TEST 9 BAŞARISIZ")

    # ----------------------------------------------------
    # Test 10: Unknown Query (Fallback)
    # ----------------------------------------------------
    print("\n[TEST 10] Unknown Query (Fallback)")
    res10 = supervisor.run("Yemekhanede bugün ne var?")
    print(f"Girdi: 'Yemekhanede bugün ne var?'\nYanıt:\n{res10['response']}")
    if "yardımcı olamıyorum" in res10["response"].lower():
        print("✅ TEST 10 BAŞARILI: Fallback response")
        passed += 1
    else:
        print("❌ TEST 10 BAŞARISIZ")

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 TEST SONUCU: {passed} / {total} BAŞARILI ({passed/total*100:.0f}%)")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
