"""
Web Application for Smart HR Assistant.
Provides a modern browser-based UI for live chat, multi-agent status visualization,
and taking evaluation screenshots. Uses standard library (no external web framework needed).
"""

import sys
import os
import json
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from agents.supervisor import SupervisorAgent

# Global agent instance & state
supervisor = SupervisorAgent()
conversation_history = []
session_context = {}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart HR Assistant - Agentic AI Kapanış Projesi</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0f172a;
            --sidebar-bg: #1e293b;
            --chat-bg: #0f172a;
            --card-bg: #334155;
            --accent-color: #3b82f6;
            --accent-hover: #2563eb;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border-color: #334155;
            --user-bubble: #2563eb;
            --bot-bubble: #1e293b;
            --success: #10b981;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            height: 100vh;
            display: flex;
            overflow: hidden;
        }

        /* Sidebar */
        .sidebar {
            width: 340px;
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            padding: 20px;
            gap: 16px;
            overflow-y: auto;
            max-height: 100vh;
        }

        .sidebar::-webkit-scrollbar {
            width: 6px;
        }
        .sidebar::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 3px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border-color);
        }

        .brand-icon {
            width: 42px;
            height: 42px;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
        }

        .brand-title {
            font-size: 16px;
            font-weight: 700;
            color: #ffffff;
            line-height: 1.2;
        }

        .brand-sub {
            font-size: 11px;
            color: #38bdf8;
            font-weight: 500;
        }

        .user-card {
            background: rgba(255, 255, 255, 0.05);
            padding: 14px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }

        .user-card-title {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .user-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: #10b981;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 14px;
        }

        .user-details h4 {
            font-size: 14px;
            font-weight: 600;
        }

        .user-details p {
            font-size: 11px;
            color: var(--text-secondary);
        }

        .section-title {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
            margin-top: 4px;
        }

        .agent-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .agent-badge {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(0, 0, 0, 0.2);
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .agent-badge-name {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--success);
        }

        .badge-tag {
            font-size: 10px;
            padding: 2px 6px;
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            border-radius: 4px;
        }

        .quick-prompts {
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-top: auto;
        }

        .prompt-btn {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 11px;
            text-align: left;
            cursor: pointer;
            transition: all 0.2s;
        }

        .prompt-btn:hover {
            background: rgba(59, 130, 246, 0.15);
            border-color: var(--accent-color);
            color: #ffffff;
        }

        /* Main Chat Area */
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        .chat-header {
            padding: 16px 24px;
            background-color: var(--sidebar-bg);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .chat-header-info h2 {
            font-size: 16px;
            font-weight: 600;
        }

        .chat-header-info p {
            font-size: 12px;
            color: var(--text-secondary);
        }

        .chat-messages {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .message {
            display: flex;
            gap: 12px;
            max-width: 80%;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
            align-self: flex-end;
            flex-direction: row-reverse;
        }

        .message-avatar {
            width: 34px;
            height: 34px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
            flex-shrink: 0;
        }

        .message.user .message-avatar {
            background: #2563eb;
        }

        .message.bot .message-avatar {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
        }

        .message-content {
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 13.5px;
            line-height: 1.5;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .message.user .message-content {
            background: var(--user-bubble);
            color: #ffffff;
            border-bottom-right-radius: 2px;
        }

        .message.bot .message-content {
            background: var(--bot-bubble);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            border-bottom-left-radius: 2px;
        }

        /* Chat Input */
        .chat-input-area {
            padding: 18px 24px;
            background-color: var(--sidebar-bg);
            border-top: 1px solid var(--border-color);
        }

        .input-wrapper {
            display: flex;
            gap: 12px;
            background: var(--bg-color);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 6px 8px 6px 16px;
            align-items: center;
            transition: border-color 0.2s;
        }

        .input-wrapper:focus-within {
            border-color: var(--accent-color);
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }

        .chat-input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: var(--text-primary);
            font-size: 14px;
        }

        .send-btn {
            background: var(--accent-color);
            border: none;
            color: #ffffff;
            width: 38px;
            height: 38px;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            transition: background 0.2s;
        }

        .send-btn:hover {
            background: var(--accent-hover);
        }

        .chip-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: #e2e8f0;
            padding: 6px 12px;
            border-radius: 16px;
            font-size: 11.5px;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        .chip-btn:hover {
            background: rgba(168, 85, 247, 0.2);
            border-color: #c084fc;
            color: #ffffff;
            transform: translateY(-1px);
        }
    </style>
</head>
<body>

    <aside class="sidebar">
        <div class="brand">
            <div class="brand-icon">🤖</div>
            <div>
                <div class="brand-title">Smart HR Assistant</div>
                <div class="brand-sub">Agentic AI Kapanış Projesi</div>
            </div>
        </div>

        <div class="user-card">
            <div class="user-card-title">Aktif Çalışan Oturumu</div>
            <div class="user-info">
                <div class="user-avatar">MY</div>
                <div class="user-details">
                    <h4>Mustafa Yılmaz</h4>
                    <p>EMP-001 • Yazılım Geliştirici</p>
                </div>
            </div>
        </div>

        <div class="user-card" style="border-color: #10b981; background: rgba(16, 185, 129, 0.08);">
            <div class="user-card-title" style="color: #34d399;">Yapay Zeka Motoru (Ollama)</div>
            <div style="font-size: 13px; font-weight: 600; color: #f8fafc; display: flex; align-items: center; gap: 6px;">
                <span class="status-dot"></span> qwen2.5-coder:7b
            </div>
            <div style="font-size: 11px; color: #94a3b8; margin-top: 4px;">Gerçek Zamanlı LLM Çıkarımı Aktif</div>
        </div>

        <div class="section-title">Multi-Agent Durumu</div>
        <div class="agent-list">
            <div class="agent-badge">
                <span class="agent-badge-name"><span class="status-dot"></span>Supervisor Agent</span>
                <span class="badge-tag">Router</span>
            </div>
            <div class="agent-badge">
                <span class="agent-badge-name"><span class="status-dot"></span>Onboarding Agent</span>
                <span class="badge-tag">Oryantasyon</span>
            </div>
            <div class="agent-badge">
                <span class="agent-badge-name"><span class="status-dot"></span>Leave Agent</span>
                <span class="badge-tag">İzin Yönetimi</span>
            </div>
            <div class="agent-badge">
                <span class="agent-badge-name"><span class="status-dot"></span>Document Agent</span>
                <span class="badge-tag">RAG / Belge</span>
            </div>
            <div class="agent-badge">
                <span class="agent-badge-name"><span class="status-dot"></span>Interview Agent</span>
                <span class="badge-tag">Takvim</span>
            </div>
        </div>

        <div class="quick-prompts">
            <div class="section-title">Hızlı Test Senaryoları</div>
            <button class="prompt-btn" onclick="sendQuick('Yeni işe başladım, ne yapmam lazım?')">🎯 Onboarding Checklist</button>
            <button class="prompt-btn" onclick="sendQuick('Kaç gün iznim var?')">📅 İzin Bakiyesi Sorgula</button>
            <button class="prompt-btn" onclick="sendQuick('5 gün izin kullanmak istiyorum')">🏖️ İzin Talebi Başlat</button>
            <button class="prompt-btn" onclick="sendQuick('Hizmet dökümü belgesi lazım')">📄 Hizmet Dökümü Al</button>
            <button class="prompt-btn" onclick="sendQuick('Evlilik izni kaç gün?')">📖 RAG Politika Sorgusu</button>
            <button class="prompt-btn" onclick="sendQuick('Yarın saat 14:00\'te mülakatım var, iptal et')">🎤 Mülakat İptali</button>
        </div>
    </aside>

    <main class="chat-container">
        <header class="chat-header">
            <div class="chat-header-info">
                <h2>Akıllı İK Asistanı Canlı Konsol</h2>
                <p>LangGraph Orchestrated • 16 Tool Calling • FAISS Vector RAG</p>
            </div>
            <div style="display: flex; gap: 8px;">
                <button class="prompt-btn" style="border-color:#a855f7; color:#c084fc; background: rgba(168, 85, 247, 0.12); font-weight:600;" onclick="sendQuick('Evlilik izni kaç gün ve şartları neler?')">📖 RAG: Evlilik İzni</button>
                <button class="prompt-btn" style="border-color:#38bdf8; color:#38bdf8; background: rgba(56, 189, 248, 0.12); font-weight:600;" onclick="sendQuick('Haftada kaç gün uzaktan çalışabilirim?')">🏠 RAG: Uzaktan Çalışma</button>
                <button class="prompt-btn" style="border-color:#10b981; color:#34d399;" onclick="resetChat()">🔄 Sohbeti Sıfırla</button>
            </div>
        </header>

        <div class="chat-messages" id="messagesBox">
            <div class="message bot">
                <div class="message-avatar">🤖</div>
                <div class="message-content">Merhaba! Smart HR Assistant'a hoş geldiniz.
Size nasıl yardımcı olabilirim?
(Onboarding, izin, belge veya mülakat işlemleri)</div>
            </div>
        </div>

        <div class="chat-input-area">
            <div style="display: flex; gap: 8px; margin-bottom: 12px; overflow-x: auto; padding-bottom: 2px;">
                <span style="font-size: 11px; color: var(--text-secondary); display: flex; align-items: center; white-space: nowrap;">⚡ Hızlı Testler:</span>
                <button class="chip-btn" onclick="sendQuick('Evlilik izni kaç gün ve şartları neler?')">📖 Evlilik İzni (RAG)</button>
                <button class="chip-btn" onclick="sendQuick('Haftada kaç gün uzaktan çalışabilirim?')">🏠 Uzaktan Çalışma (RAG)</button>
                <button class="chip-btn" onclick="sendQuick('Yıllık eğitim bütçemiz ne kadar?')">🎓 Eğitim Bütçesi (RAG)</button>
                <button class="chip-btn" onclick="sendQuick('Kaç gün iznim var?')">📅 İzin Bakiyem</button>
                <button class="chip-btn" onclick="sendQuick('5 gün izin kullanmak istiyorum')">🏖️ İzin Başvurusu</button>
                <button class="chip-btn" onclick="sendQuick('Hizmet dökümü belgesi lazım')">📄 Hizmet Dökümü</button>
            </div>
            <div class="input-wrapper">
                <input type="text" id="userInput" class="chat-input" placeholder="Bir mesaj yazın (Örn: 'Evlilik izni kaç gün?', 'Kaç gün iznim var?')..." onkeydown="if(event.key==='Enter') sendMessage()">
                <button class="send-btn" onclick="sendMessage()">➔</button>
            </div>
        </div>
    </main>

    <script>
        const messagesBox = document.getElementById('messagesBox');
        const userInput = document.getElementById('userInput');

        function appendMessage(text, isUser) {
            const msgDiv = document.createElement('div');
            msgDiv.className = 'message ' + (isUser ? 'user' : 'bot');
            msgDiv.innerHTML = `
                <div class="message-avatar">${isUser ? '👤' : '🤖'}</div>
                <div class="message-content">${escapeHtml(text)}</div>
            `;
            messagesBox.appendChild(msgDiv);
            messagesBox.scrollTop = messagesBox.scrollHeight;
        }

        function escapeHtml(text) {
            return text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");
        }

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text) return;

            appendMessage(text, true);
            userInput.value = '';

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await response.json();
                appendMessage(data.response, false);
            } catch (err) {
                appendMessage('Bağlantı hatası: ' + err, false);
            }
        }

        function sendQuick(text) {
            userInput.value = text;
            sendMessage();
        }

        async function resetChat() {
            messagesBox.innerHTML = '';
            await fetch('/api/reset', { method: 'POST' });
            appendMessage("Merhaba! Smart HR Assistant'a hoş geldiniz.\\nSize nasıl yardımcı olabilirim?\\n(Onboarding, izin, belge veya mülakat işlemleri)", false);
        }
    </script>
</body>
</html>
"""


class HRRequestHandler(BaseHTTPRequestHandler):
    """Custom request handler serving UI and handling chat API."""

    def log_message(self, format, *args):
        # Clean logging
        return

    def do_GET(self):
        if self.path in ["/", "/index.html"]:
            body_bytes = HTML_TEMPLATE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body_bytes)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body_bytes)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global conversation_history, session_context

        if self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)
            user_msg = data.get("message", "")

            # Execute via LangGraph Supervisor
            res = supervisor.run(
                user_input=user_msg,
                conversation_messages=conversation_history,
                context=session_context
            )

            conversation_history = res["messages"]
            session_context = res["context"]

            resp_bytes = json.dumps({"response": res["response"]}, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(resp_bytes)

        elif self.path == "/api/reset":
            conversation_history = []
            session_context = {}
            resp_bytes = b'{"status":"ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(resp_bytes)

        else:
            self.send_response(404)
            self.end_headers()


def start_server(port=8080):
    server = HTTPServer(("127.0.0.1", port), HRRequestHandler)
    print("=" * 60)
    print("🚀 SMART HR ASSISTANT - WEB SUNUCUSU BAŞLATILDI")
    print(f"🔗 Tarayıcıdan açın: http://localhost:{port}")
    print("=" * 60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSunucu kapatıldı.")


if __name__ == "__main__":
    start_server()
