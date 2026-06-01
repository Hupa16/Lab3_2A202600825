"""Offline tests for tour tools and agent parsing (no API key required)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent import ReActAgentV1, ReActAgentV2
from src.core.llm_provider import LLMProvider
from src.tools.tour_tools import (
    build_itinerary,
    estimate_tour_budget,
    get_tour_tools,
    search_destinations,
)


class MockLLM(LLMProvider):
    def __init__(self, responses):
        super().__init__("mock")
        self._responses = list(responses)
        self._i = 0

    def generate(self, prompt, system_prompt=None):
        content = self._responses[min(self._i, len(self._responses) - 1)]
        self._i += 1
        return {"content": content, "usage": {"total_tokens": 10}, "latency_ms": 1, "provider": "mock"}

    def stream(self, prompt, system_prompt=None):
        yield self.generate(prompt)["content"]


def test_search_central_beach():
    out = search_destinations(region="Central Vietnam", budget_per_day=2_500_000, interests="beach")
    assert "Da Nang" in out
    assert "VND" in out


def test_budget_da_nang():
    out = estimate_tour_budget(destination="Da Nang", days=4, travelers=2, tier="standard")
    assert "TOTAL" in out
    assert "VND" in out


def test_itinerary_explore():
    out = build_itinerary(destination="Da Nang", days=3, travel_style="explore")
    assert "Day 1" in out
    assert "Day 3" in out


def test_three_tools_registered():
    names = {t["name"] for t in get_tour_tools()}
    assert names == {"search_destinations", "estimate_tour_budget", "build_itinerary"}


def test_react_v1_full_loop():
    responses = [
        'Thought: search.\nAction: search_destinations(region="Central", budget_per_day=2000000, interests="beach")',
        'Thought: budget.\nAction: estimate_tour_budget(destination="Da Nang", days=4, travelers=2, tier="standard")',
        'Thought: plan.\nAction: build_itinerary(destination="Da Nang", days=4, travel_style="explore")',
        "Final Answer: Da Nang 4-day package ready.",
    ]
    agent = ReActAgentV1(MockLLM(responses), get_tour_tools(), max_steps=6)
    answer = agent.run("plan a trip")
    assert "Da Nang" in answer or "ready" in answer.lower()
    assert agent.last_run
    assert len(agent.last_run.tools_called) == 3
    assert agent.last_run.completed


def test_react_v2_strips_markdown():
    responses = [
        '```python\nThought: x\nAction: search_destinations(region="North", budget_per_day=0, interests="trekking")\n```',
        "Final Answer: Done.",
    ]
    agent = ReActAgentV2(MockLLM(responses), get_tour_tools(), max_steps=4)
    agent.run("trek north")
    assert "search_destinations" in agent.last_run.tools_called
