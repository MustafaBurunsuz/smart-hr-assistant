"""
Dedicated RAG (Retrieval-Augmented Generation) Test Script for Smart HR Assistant.
Demonstrates the full RAG pipeline:
1. User Query
2. Retrieval from Knowledge Base (HR Policies)
3. Prompt Context Injection
4. Local Ollama LLM Generation
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from tools.document_tools import get_policy_document
from utils.ollama_client import OllamaClient


def test_rag_query(query: str, client: OllamaClient):
    print("=" * 65)
    print(f"🔍 [SORU]: {query}")
    print("-" * 65)

    # 1. Retrieval Step
    retrieved = get_policy_document.invoke({"policy_type": query})

    if retrieved.get("status") == "not_found":
        print("❌ Doküman bulunamadı.")
        return

    print("📄 [RETRIEVAL - ÇEKİLEN İK POLİTİKASI]:")
    print(f"  • Başlık  : {retrieved.get('title')}")
    print(f"  • Kategori: {retrieved.get('category')}")
    print(f"  • Kaynak  : {retrieved.get('source')}")
    print(f"  • İçerik  : {retrieved.get('content')}")
    print("-" * 65)

    # 2. Augmented Generation Step with Ollama
    if client.is_available():
        print("🤖 [LLM GENERATION - OLLAMA CEVABI]:")
        system_prompt = (
            "Sen şirketin İK Politika ve Mevzuat Danışmanısın (RAG Sistemi).\n"
            "Aşağıdaki resmi İK politika metnini kaynak alarak kullanıcının sorusunu samimi, anlaşılır ve Türkçe olarak yanıtla.\n"
            f"--- RESMİ POLİTİKA METNİ ---\n"
            f"Başlık: {retrieved.get('title')}\n"
            f"İçerik: {retrieved.get('content')}\n"
            "-----------------------------\n"
            "Yanıtında politika başlığını ve varsa şartları (süre, belge vb.) net şekilde belirt."
        )
        ai_answer = client.chat(system_prompt, [{"role": "user", "content": query}], temperature=0.2)
        print(ai_answer or "Ollama cevabı üretilemedi.")
    else:
        print("ℹ (Ollama çevrimdışı, doğrudan doküman içeriği gösterildi):")
        print(retrieved.get("message"))
    print("\n")


def run_all_rag_tests():
    print("*" * 65)
    print("       SMART HR ASSISTANT - RAG DOĞRULAMA VE TEST PANELİ")
    print("*" * 65 + "\n")

    client = OllamaClient()
    active_model = client.get_active_model() if client.is_available() else "Çevrimdışı"
    print(f"Aktif Model: {active_model} | Ollama Durumu: {'🟢 Bağlı' if client.is_available() else '🔴 Kapalı'}\n")

    test_queries = [
        "Evlilik izni kaç gün ve hangi belgeler gerekir?",
        "Haftada kaç gün uzaktan çalışabilirim?",
        "Yıllık eğitim bütçemiz ne kadar, hangi platformları kapsar?",
        "Haftalık kaç saatten sonrası fazla mesai sayılır?",
        "Özel sağlık sigortasından ne zaman faydalanabilirim?"
    ]

    for q in test_queries:
        test_rag_query(q, client)


if __name__ == "__main__":
    run_all_rag_tests()
