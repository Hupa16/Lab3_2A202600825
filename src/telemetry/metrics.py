"""Industry-style LLM metrics (cost, tokens, latency) for lab telemetry."""
from typing import Any, Dict, List

from src.telemetry.logger import logger

# USD per 1K tokens (approximate lab pricing — update for your provider)
MODEL_PRICING_PER_1K = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "local": {"input": 0.0, "output": 0.0},
}


class PerformanceTracker:
    def __init__(self):
        self.session_metrics: List[Dict[str, Any]] = []

    def track_request(
        self,
        provider: str,
        model: str,
        usage: Dict[str, int],
        latency_ms: int,
    ) -> Dict[str, Any]:
        prompt_t = usage.get("prompt_tokens", 0)
        completion_t = usage.get("completion_tokens", 0)
        total_t = usage.get("total_tokens", prompt_t + completion_t)

        cost = self._calculate_cost(model, prompt_t, completion_t)
        ratio = round(completion_t / prompt_t, 3) if prompt_t else 0.0

        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": prompt_t,
            "completion_tokens": completion_t,
            "total_tokens": total_t,
            "completion_to_prompt_ratio": ratio,
            "latency_ms": latency_ms,
            "cost_estimate_usd": cost,
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)
        return metric

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        key = model.lower()
        rates = MODEL_PRICING_PER_1K.get(key)
        if not rates:
            for name, price in MODEL_PRICING_PER_1K.items():
                if name in key:
                    rates = price
                    break
        if not rates:
            rates = {"input": 0.001, "output": 0.002}

        return (prompt_tokens / 1000) * rates["input"] + (completion_tokens / 1000) * rates["output"]

    def summary(self) -> Dict[str, Any]:
        if not self.session_metrics:
            return {"count": 0}

        latencies = [m["latency_ms"] for m in self.session_metrics]
        tokens = [m["total_tokens"] for m in self.session_metrics]
        costs = [m["cost_estimate_usd"] for m in self.session_metrics]
        sorted_lat = sorted(latencies)

        def percentile(data: List[int], p: float) -> int:
            if not data:
                return 0
            idx = min(len(data) - 1, int(len(data) * p))
            return data[idx]

        return {
            "request_count": len(self.session_metrics),
            "total_tokens": sum(tokens),
            "total_cost_usd": round(sum(costs), 6),
            "avg_latency_ms": round(sum(latencies) / len(latencies)),
            "p50_latency_ms": percentile(sorted_lat, 0.5),
            "p99_latency_ms": percentile(sorted_lat, 0.99),
            "avg_completion_to_prompt_ratio": round(
                sum(m.get("completion_to_prompt_ratio", 0) for m in self.session_metrics)
                / len(self.session_metrics),
                3,
            ),
        }


tracker = PerformanceTracker()
