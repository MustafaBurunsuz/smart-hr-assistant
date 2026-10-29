"""
Live Conversation Demo Runner for Smart HR Assistant.
Runs the complete multi-turn master plan conversation flow with realistic formatting,
ideal for recording terminal screen recordings or taking screenshots.
"""

import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from agents.supervisor import SupervisorAgent
from main import print_banner
from scripts.seed_data import seed_all_data


def run_demo():
    seed_all_data()
    print("\n" * 2)
    print_banner()

    supervisor = SupervisorAgent()
    history = []
    context = {}

    conversation = [
        "Merhaba",
        "Yeni işe başladım, ne yapmam lazım?",
        "Kaç gün iznim var?",
        "5 gün yıllık izin kullanmak istiyorum",
        "1 Kasım, 5 gün",
        "Hizmet dökümü belgesi lazım",
        "Evlilik izni kaç gün?",
        "help",
        "exit"
    ]

    for user_input in conversation:
        print(f"Sen: {user_input}")
        time.sleep(0.5)

        if user_input.lower() in ["exit", "çıkış"]:
            print("Asistan: Görüşmek üzere! İyi çalışmalar! 👋\n")
            break

        res = supervisor.run(
            user_input=user_input,
            conversation_messages=history,
            context=context
        )

        history = res["messages"]
        context = res["context"]

        print(f"Asistan: {res['response']}\n")
        time.sleep(0.5)


if __name__ == "__main__":
    run_demo()
