"""
ReAct agents for Personalized All-Inclusive Tour Planning (international / English).

- ReActAgentV1: minimal Thought → Action → Observation loop.
- ReActAgentV2: v1 + guardrails (markdown strip, arg normalize, parse retry, duplicate detection).
"""
import ast
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

TOOL_ALIASES = {
    "search_destination": "search_destinations",
    "search": "search_destinations",
    "estimate_budget": "estimate_tour_budget",
    "budget": "estimate_tour_budget",
    "itinerary": "build_itinerary",
    "build_schedule": "build_itinerary",
}

REGION_ALIASES = {
    "north vietnam": "North",
    "northern": "North",
    "central vietnam": "Central",
    "south vietnam": "South",
    "southern": "South",
}

TIER_ALIASES = {
    "economy": "budget",
    "basic": "budget",
    "mid": "standard",
    "premium": "luxury",
    "deluxe": "luxury",
}

STYLE_ALIASES = {
    "adventure": "explore",
    "sightseeing": "explore",
    "chill": "relax",
    "kids": "family",
}


@dataclass
class AgentRunResult:
    answer: str
    completed: bool
    steps: int
    tools_called: List[str] = field(default_factory=list)
    parse_warnings: int = 0
    total_latency_ms: int = 0
    total_tokens: int = 0


class ReActAgentV1:
    """Agent v1 — working ReAct loop with 3 tools (lab baseline)."""

    PROMPT_VERSION = "v1"

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 6):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history: List[str] = []
        self.last_run: Optional[AgentRunResult] = None
        self._tools_called: List[str] = []
        self._parse_warnings = 0
        self._total_latency_ms = 0
        self._total_tokens = 0

    def get_system_prompt(self) -> str:
        tool_lines = [f"- {t['name']}: {t['description']}" for t in self.tools]
        return f"""You are an AI assistant for **Personalized All-Inclusive Tour Planning in Vietnam** (international travelers). Respond in **English**.

Tools:
{chr(10).join(tool_lines)}

Rules:
1. Multi-step planning: search_destinations → estimate_tour_budget → build_itinerary when needed.
2. Budget parameters are in **VND** (1 USD ≈ 25,000 VND).
3. One Action per turn. Format: Action: tool_name(param=value)
4. Finish with a line starting: Final Answer:

Each step:
Thought: brief reasoning.
Action: tool_name(...)
(or Final Answer: ...)
"""

    def run(self, user_input: str) -> str:
        logger.log_event(
            "AGENT_START",
            {"version": self.PROMPT_VERSION, "input": user_input, "model": self.llm.model_name},
        )

        self.history = [f"User request: {user_input}"]
        self._tools_called = []
        self._parse_warnings = 0
        self._total_latency_ms = 0
        self._total_tokens = 0

        steps = 0
        final_answer: Optional[str] = None

        while steps < self.max_steps:
            prompt = self._build_prompt(steps)
            content = self._llm_step(prompt)

            self.history.append(content)
            final_answer = self._extract_final_answer(content)
            if final_answer is not None:
                break

            action = self._extract_action(content)
            if action is None:
                self._parse_warnings += 1
                logger.log_event(
                    "AGENT_PARSE_WARN",
                    {"version": self.PROMPT_VERSION, "step": steps + 1, "reason": "no_action_or_final"},
                )
                steps += 1
                continue

            tool_name, kwargs = action
            observation = self._execute_tool(tool_name, kwargs)
            self._tools_called.append(tool_name)
            self.history.append(f"Observation: {observation}")
            logger.log_event(
                "TOOL_CALL",
                {"version": self.PROMPT_VERSION, "tool": tool_name, "args": kwargs},
            )
            steps += 1

        completed = final_answer is not None
        answer = final_answer or (
            "The agent did not finish within the step limit. Check logs/ or use Agent v2."
        )

        self.last_run = AgentRunResult(
            answer=answer,
            completed=completed,
            steps=steps,
            tools_called=list(self._tools_called),
            parse_warnings=self._parse_warnings,
            total_latency_ms=self._total_latency_ms,
            total_tokens=self._total_tokens,
        )
        logger.log_event(
            "AGENT_END",
            {
                "version": self.PROMPT_VERSION,
                "steps": steps,
                "completed": completed,
                "tools_called": self._tools_called,
            },
        )
        return answer

    def _build_prompt(self, step: int) -> str:
        return (
            "Continue planning the tour. Context:\n\n"
            + "\n\n".join(self.history)
            + "\n\nNext (Thought + Action, or Final Answer):"
        )

    def _llm_step(self, prompt: str) -> str:
        result = self.llm.generate(prompt, system_prompt=self.get_system_prompt())
        content = self._clean_llm_text((result.get("content") or "").strip())
        usage = result.get("usage") or {}
        latency = result.get("latency_ms", 0)
        self._total_latency_ms += latency
        self._total_tokens += usage.get("total_tokens", 0)
        tracker.track_request(
            provider=result.get("provider", "unknown"),
            model=self.llm.model_name,
            usage=usage,
            latency_ms=latency,
        )
        logger.log_event(
            "AGENT_STEP",
            {
                "version": self.PROMPT_VERSION,
                "llm_output": content,
                "usage": usage,
                "latency_ms": latency,
            },
        )
        return content

    def _clean_llm_text(self, text: str) -> str:
        return text.strip()

    def _normalize_tool_name(self, name: str) -> str:
        key = name.strip().lower()
        return TOOL_ALIASES.get(key, name.strip())

    def _normalize_kwargs(self, tool_name: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(kwargs)
        if tool_name == "search_destinations" and "region" in out:
            r = str(out["region"]).lower().strip()
            out["region"] = REGION_ALIASES.get(r, out["region"])
        if tool_name == "estimate_tour_budget" and "tier" in out:
            t = str(out["tier"]).lower().strip()
            out["tier"] = TIER_ALIASES.get(t, out["tier"])
        if tool_name == "build_itinerary" and "travel_style" in out:
            s = str(out["travel_style"]).lower().strip()
            out["travel_style"] = STYLE_ALIASES.get(s, out["travel_style"])
        return out

    def _extract_final_answer(self, text: str) -> Optional[str]:
        match = re.search(r"Final\s+Answer:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None

    def _extract_action(self, text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        match = re.search(
            r"Action:\s*(\w+)\s*\((.*)\)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return None
        tool_name = self._normalize_tool_name(match.group(1))
        kwargs = self._normalize_kwargs(tool_name, self._parse_tool_args(match.group(2).strip()))
        return tool_name, kwargs

    def _parse_tool_args(self, args_str: str) -> Dict[str, Any]:
        if not args_str:
            return {}
        try:
            node = ast.parse(f"f({args_str})", mode="eval").body
            if isinstance(node, ast.Call):
                return {kw.arg: ast.literal_eval(kw.value) for kw in node.keywords if kw.arg}
        except (SyntaxError, ValueError):
            pass
        kwargs: Dict[str, Any] = {}
        for part in re.split(r",\s*(?=\w+\s*=)", args_str):
            if "=" not in part:
                continue
            key, _, val = part.partition("=")
            val = val.strip().strip("\"'")
            try:
                kwargs[key.strip()] = ast.literal_eval(val)
            except (SyntaxError, ValueError):
                kwargs[key.strip()] = val
        return kwargs

    def _execute_tool(self, tool_name: str, kwargs: Dict[str, Any]) -> str:
        for tool in self.tools:
            if tool["name"] == tool_name:
                func = tool.get("func")
                if callable(func):
                    try:
                        return str(func(**kwargs))
                    except TypeError as e:
                        return f"Invalid arguments for {tool_name}: {e}"
                return f"Tool {tool_name} has no implementation."
        valid = ", ".join(t["name"] for t in self.tools)
        return f"Unknown tool '{tool_name}'. Valid: {valid}."


class ReActAgentV2(ReActAgentV1):
    """
    Agent v2 — improvements over v1 (addresses common failure traces):
    - Strip markdown fences from LLM output
    - Parse-retry hints after failed Action parse
    - Block duplicate identical tool calls
    - Force Final Answer nudge near step limit
    - Stricter prompt with few-shot and argument checklist
    """

    PROMPT_VERSION = "v2"
    MAX_PARSE_RETRIES = 2

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 8):
        super().__init__(llm, tools, max_steps=max_steps)
        self._parse_retries = 0
        self._last_action_signature: Optional[str] = None

    def get_system_prompt(self) -> str:
        tool_lines = [f"- {t['name']}: {t['description']}" for t in self.tools]
        return f"""You are an AI assistant for **Personalized All-Inclusive Tour Planning in Vietnam** (international travelers). English only.

Tools (exact names):
{chr(10).join(tool_lines)}

Critical rules:
1. NEVER invent VND/USD prices or daily schedules — call tools first.
2. Convert USD to VND (×25,000) before search_destinations / estimate_tour_budget.
3. tier must be: budget | standard | luxury. travel_style: relax | explore | family.
4. region must be: North | Central | South (or substring like "Central Vietnam").
5. Exactly ONE Action per message. No markdown code blocks around Action lines.
6. End with: Final Answer: <concise package summary citing tool results>

Few-shot:
Thought: User wants Central beaches under $80/day → 2,000,000 VND/day.
Action: search_destinations(region="Central", budget_per_day=2000000, interests="beach,food")

Thought: Pick Da Nang, 4 days, 2 travelers, standard tier.
Action: estimate_tour_budget(destination="Da Nang", days=4, travelers=2, tier="standard")

Thought: Build explore itinerary.
Action: build_itinerary(destination="Da Nang", days=4, travel_style="explore")

Final Answer: ...
"""

    def run(self, user_input: str) -> str:
        self._parse_retries = 0
        self._last_action_signature = None
        return super().run(user_input)

    def _clean_llm_text(self, text: str) -> str:
        text = super()._clean_llm_text(text)
        text = re.sub(r"```(?:json|python)?\s*", "", text)
        text = text.replace("```", "")
        return text.strip()

    def _build_prompt(self, step: int) -> str:
        base = super()._build_prompt(step)
        if step >= self.max_steps - 2:
            base += (
                "\n\n[System] You are near the step limit. "
                "If you have tool observations, output Final Answer now (no more Actions)."
            )
        if self._parse_retries > 0:
            base += (
                f"\n\n[System] Your last reply had no valid Action line. "
                f"Use exactly: Action: tool_name(key=value). "
                f"Valid tools: {', '.join(t['name'] for t in self.tools)}."
            )
        return base

    def _extract_action(self, text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        action = super()._extract_action(text)
        if action is None:
            if self._parse_retries < self.MAX_PARSE_RETRIES:
                self._parse_retries += 1
                self.history.append(
                    "Observation: [System] Parse failed. Output Thought then "
                    "Action: tool_name(arg=value) with exact tool name, or Final Answer."
                )
            return None

        tool_name, kwargs = action
        signature = f"{tool_name}:{sorted(kwargs.items())}"
        if signature == self._last_action_signature:
            self.history.append(
                "Observation: [System] Duplicate tool call blocked. "
                "Use a different tool or provide Final Answer."
            )
            logger.log_event(
                "AGENT_GUARD",
                {"version": self.PROMPT_VERSION, "reason": "duplicate_action", "tool": tool_name},
            )
            return None

        self._last_action_signature = signature
        self._parse_retries = 0
        return action


# Default export for run_agent.py
ReActAgent = ReActAgentV2
