"""
Main entry point for Smart HR Assistant.
Interactive CLI with Multi-Agent LangGraph coordination.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

load_dotenv()

from agents.supervisor import SupervisorAgent
from utils.helpers import load_json


def print_banner():
    """Print the startup banner."""
    print("╔══════════════════════════════════════════╗")
    print("║   SMART HR ASSISTANT - Hoş Geldiniz     ║")
    print("║   Agentic AI Bootcamp - Kapanış Projesi ║")
    print("╚══════════════════════════════════════════╝\n")

    print("Agent başlatılıyor...")
    print("✓ Supervisor Agent hazır")
    print("✓ Onboarding Agent hazır")
    print("✓ Leave Agent hazır")
    print("✓ Document Agent hazır")
    print("✓ Interview Agent hazır")

    policies = load_json("hr_policies.json", default=[])
    print(f"✓ Vector DB yüklendi ({len(policies)} politika)")

    from utils.ollama_client import OllamaClient
    client = OllamaClient()
    if client.is_available():
        print(f"✓ Ollama LLM Motoru: {client.get_active_model()} Aktif 🟢 (Gerçek AI)")
    else:
        print("ℹ Ollama bağlantısı yok (Çevrimdışı Kural Modu)")

    print("\nHazır! Yardım için 'help' yaz.")
    print("═══════════════════════════════════════════\n")


def run_cli():
    """Run the main interactive CLI loop."""
    print_banner()

    supervisor = SupervisorAgent()
    conversation_history = []
    session_context = {}

    while True:
        try:
            user_input = input("Sen: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "çıkış", "q", "quit"]:
                print("Asistan: Görüşmek üzere! İyi çalışmalar! 👋")
                break

            result = supervisor.run(
                user_input=user_input,
                conversation_messages=conversation_history,
                context=session_context
            )

            # Update history and session memory
            conversation_history = result["messages"]
            session_context = result["context"]

            print(f"Asistan: {result['response']}\n")

        except (KeyboardInterrupt, EOFError):
            print("\nAsistan: Oturum sonlandırıldı. İyi çalışmalar!")
            break
        except Exception as e:
            print(f"[Hata] Bir sorun oluştu: {e}")


if __name__ == "__main__":
    run_cli()
