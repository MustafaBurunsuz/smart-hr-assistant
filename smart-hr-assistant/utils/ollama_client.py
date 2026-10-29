"""
Ollama AI Client.
Provides direct HTTP integration with the local Ollama LLM service
for real neural network inference across all agents.
"""

import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional


class OllamaClient:
    """Client for local Ollama LLM REST API."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.preferred_model = model or os.getenv("LLM_MODEL", "qwen2.5-coder:7b")
        self._cached_model = None

    def get_active_model(self) -> str:
        """Find the best available model in the local Ollama service."""
        if self._cached_model:
            return self._cached_model

        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                
                # Check preferred first
                for m in models:
                    if self.preferred_model in m:
                        self._cached_model = m
                        return m

                # Check known high quality models
                for candidate in ["qwen2.5-coder", "qwen3", "qwen2.5", "gemma3", "llama3"]:
                    for m in models:
                        if candidate in m:
                            self._cached_model = m
                            return m

                if models:
                    self._cached_model = models[0]
                    return models[0]
        except Exception:
            pass

        return self.preferred_model

    def is_available(self) -> bool:
        """Check if Ollama local service is up and responsive."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200
        except Exception:
            return False

    def chat(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: Optional[int] = None
    ) -> Optional[str]:
        """Send chat completion request to Ollama and return assistant message content.

        Args:
            system_prompt: Guiding instructions and live context for the AI agent.
            messages: Conversation history list of {'role': 'user'|'assistant', 'content': '...'}.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated response string, or None if Ollama is unreachable.
        """
        model = self.get_active_model()
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        payload = {
            "model": model,
            "messages": full_messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    return data.get("message", {}).get("content", "").strip()
        except Exception as e:
            # Fallback will handle when Ollama is offline
            pass

        return None
