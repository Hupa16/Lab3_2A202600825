"""
Data-driven Chatbot vs ReAct Agent evaluation (SCORING: Evaluation & Analysis).
"""
import json
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from src.agent.agent import ReActAgentV1, ReActAgentV2
from src.chatbot.baseline import TourChatbot
from src.core.llm_provider import LLMProvider
from src.telemetry.metrics import tracker
from src.tools.tour_tools import get_tour_tools


@dataclass
class CaseResult:
    case_id: str
    case_type: str
    mode: str
    success: bool
    reason: str
    tools_called: List[str]
    steps: int
    completed: bool
    latency_ms: int
    tokens: int


def load_cases(path: str) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _score_agent(case: Dict[str, Any], run) -> tuple[bool, str]:
    if case["type"] == "simple":
        ok = bool(run.answer and len(run.answer) > 20)
        return ok, "non-empty answer" if ok else "answer too short"

    min_tools = case.get("min_tools", 2)
    if len(run.tools_called) < min_tools:
        return False, f"expected >={min_tools} tools, got {len(run.tools_called)}"

    for req in case.get("required_tools", []):
        if req not in run.tools_called:
            return False, f"missing required tool {req}"

    if not run.completed:
        return False, "agent did not reach Final Answer"

    return True, "multi-step criteria met"


def _score_chatbot(case: Dict[str, Any], answer: str) -> tuple[bool, str]:
    if not answer or len(answer) < 15:
        return False, "empty or too short"

    if case["type"] == "multi_step":
        # Chatbot has no tools — flag likely hallucinated precision
        has_fake_precision = any(
            x in answer.lower()
            for x in ("total:", "day 1:", "vnd", "itinerary", "14,400,000")
        ) and "approximate" not in answer.lower()
        if has_fake_precision:
            return False, "multi-step: precise figures without tools (expected weakness)"
        return True, "multi-step: answered without tool grounding (baseline)"

    return True, "simple question answered"


def run_evaluation(
    llm: LLMProvider,
    cases_path: str,
    agent_version: str = "v2",
    modes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    modes = modes or ["chatbot", "agent"]
    cases = load_cases(cases_path)
    tracker.session_metrics.clear()

    agent_cls = ReActAgentV2 if agent_version == "v2" else ReActAgentV1
    tools = get_tour_tools()
    results: List[CaseResult] = []

    for case in cases:
        if "chatbot" in modes:
            bot = TourChatbot(llm)
            ans = bot.run(case["query"])
            ok, reason = _score_chatbot(case, ans)
            lr = bot.last_run or {}
            results.append(
                CaseResult(
                    case_id=case["id"],
                    case_type=case["type"],
                    mode="chatbot",
                    success=ok,
                    reason=reason,
                    tools_called=[],
                    steps=1,
                    completed=True,
                    latency_ms=lr.get("latency_ms", 0),
                    tokens=(lr.get("usage") or {}).get("total_tokens", 0),
                )
            )

        if "agent" in modes:
            agent = agent_cls(llm, tools)
            ans = agent.run(case["query"])
            run = agent.last_run
            ok, reason = _score_agent(case, run) if run else (False, "no run metadata")
            results.append(
                CaseResult(
                    case_id=case["id"],
                    case_type=case["type"],
                    mode=f"agent_{agent_version}",
                    success=ok,
                    reason=reason,
                    tools_called=run.tools_called if run else [],
                    steps=run.steps if run else 0,
                    completed=run.completed if run else False,
                    latency_ms=run.total_latency_ms if run else 0,
                    tokens=run.total_tokens if run else 0,
                )
            )

    return _aggregate(results, agent_version)


def _aggregate(results: List[CaseResult], agent_version: str) -> Dict[str, Any]:
    by_mode: Dict[str, List[CaseResult]] = {}
    for r in results:
        by_mode.setdefault(r.mode, []).append(r)

    summary = {"agent_version": agent_version, "modes": {}, "comparison": []}
    for mode, rows in by_mode.items():
        wins = sum(1 for r in rows if r.success)
        summary["modes"][mode] = {
            "success_rate": round(wins / len(rows), 2) if rows else 0,
            "passed": wins,
            "total": len(rows),
            "results": [asdict(r) for r in rows],
        }

    # Pairwise by case_id
    chatbot_mode = "chatbot"
    agent_mode = f"agent_{agent_version}"
    if chatbot_mode in by_mode and agent_mode in by_mode:
        chat_map = {r.case_id: r for r in by_mode[chatbot_mode]}
        agent_map = {r.case_id: r for r in by_mode[agent_mode]}
        for cid in chat_map:
            if cid not in agent_map:
                continue
            c, a = chat_map[cid], agent_map[cid]
            if c.success and a.success:
                winner = "draw"
            elif a.success and not c.success:
                winner = "agent"
            elif c.success and not a.success:
                winner = "chatbot"
            else:
                winner = "none"
            summary["comparison"].append(
                {
                    "case_id": cid,
                    "type": c.case_type,
                    "chatbot_success": c.success,
                    "agent_success": a.success,
                    "winner": winner,
                }
            )

    summary["metrics"] = tracker.summary()
    return summary
