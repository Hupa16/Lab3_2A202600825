<<<<<<< HEAD
# Lab 3: Chatbot vs ReAct Agent — Personalized Vietnam Tour Planning

**Topic**: AI Trợ Lý Lập Kế Hoạch Tour Trọn Gói Cá Nhân Hóa (international travelers, English).

This repo implements the full **group score** checklist from [SCORING.md](SCORING.md): chatbot baseline, ReAct agent v1/v2, **3 tools**, telemetry, evaluation, traces, and group report.

## Quick start

```bash
cp .env.example .env          # add OPENAI_API_KEY or GEMINI_API_KEY
pip install -r requirements.txt

python run_chatbot.py         # baseline (no tools)
python run_agent.py           # ReAct v2 (default)
python run_agent.py --version v1
python run_evaluation.py      # Chatbot vs Agent comparison
pytest tests/test_tour_tools.py -q
```

## Project layout

| Path | Purpose |
|------|---------|
| `src/chatbot/baseline.py` | Chatbot baseline (2 pts) |
| `src/agent/agent.py` | ReAct v1 + v2 (7 + 7 pts) |
| `src/tools/tour_tools.py` | 3 tour planning tools |
| `src/telemetry/metrics.py` | Cost, tokens, latency (+bonus monitoring) |
| `src/evaluation/runner.py` | Automated comparison (7 pts) |
| `data/evaluation_cases.json` | Test cases |
| `docs/TOOL_EVOLUTION.md` | Tool spec progression (4 pts) |
| `report/traces/` | Success + failure traces (9 pts) |
| `report/group_report/GROUP_REPORT.md` | Group submission template (filled) |

## Three tools

1. **`search_destinations`** — filter Vietnam catalog by region, VND/day budget, interests  
2. **`estimate_tour_budget`** — line-item package cost (budget / standard / luxury)  
3. **`build_itinerary`** — day-by-day plan (relax / explore / family)

## Agent versions

- **v1** (`ReActAgentV1`): minimal ReAct loop  
- **v2** (`ReActAgentV2`): markdown strip, tool aliases, parse retry, duplicate guard, few-shot prompt  

## Local models

See `.env.example` — set `DEFAULT_PROVIDER=local` and download Phi-3 GGUF into `models/`.

## Grading

- Group report: edit team name in `report/group_report/GROUP_REPORT.md`, run evaluation, paste metrics.  
- Individual: `report/individual_reports/TEMPLATE_INDIVIDUAL_REPORT.md` → `individual_report.md`.

---

*Happy Coding! Read the logs — traces are the truth.*
=======
