"""
Minimal chatbot baseline — single LLM call, no tools.
Used to compare against the ReAct agent (SCORING: Chatbot Baseline).
"""
from typing import Any, Dict, Optional

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


CHATBOT_SYSTEM_PROMPT = """You are a friendly Vietnam tour planning assistant for international travelers.
Answer in English. You may give general travel advice, but you do NOT have access to live pricing,
destination databases, or itinerary generators. If the user asks for exact budgets, comparisons across
cities, or day-by-day plans based on specific constraints, explain what you would recommend in general
terms and note that figures may be approximate.
"""


class TourChatbot:
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.last_run: Optional[Dict[str, Any]] = None

    def run(self, user_input: str) -> str:
        logger.log_event("CHATBOT_START", {"input": user_input, "model": self.llm.model_name})

        result = self.llm.generate(user_input, system_prompt=CHATBOT_SYSTEM_PROMPT)
        content = (result.get("content") or "").strip()

        usage = result.get("usage") or {}
        tracker.track_request(
            provider=result.get("provider", "unknown"),
            model=self.llm.model_name,
            usage=usage,
            latency_ms=result.get("latency_ms", 0),
        )

        self.last_run = {
            "answer": content,
            "usage": usage,
            "latency_ms": result.get("latency_ms", 0),
            "tools_called": [],
            "steps": 1,
        }

        logger.log_event(
            "CHATBOT_END",
            {"latency_ms": self.last_run["latency_ms"], "tokens": usage.get("total_tokens", 0)},
        )
        return content
