# Failed Trace (v1) — Parser & Hallucination

**Case**: Agent v1 before v2 guardrails  
**Failure types**: `AGENT_PARSE_WARN`, hallucinated tool name

## Symptom 1 — Markdown-wrapped Action

**LLM output**

```text
```json
Action: search_destinations(region="Central", budget_per_day=2000000)
```
```

**v1 behavior**: Regex did not match → `AGENT_PARSE_WARN`, wasted step.

**v2 fix**: `_clean_llm_text()` strips ``` fences; optional parse-retry Observation.

## Symptom 2 — Wrong tool name

**LLM output**

```text
Action: search_destination(region="Central", budget_per_day=2000000)
```

**v1 behavior**: `Unknown tool 'search_destination'`.

**v2 fix**: `TOOL_ALIASES["search_destination"] → search_destinations`.

## Symptom 3 — Duplicate loop

**LLM output** (step 4 repeats step 2)

```text
Action: estimate_tour_budget(destination="Da Nang", days=4, travelers=2, tier="standard")
```

**v2 behavior**: `AGENT_GUARD duplicate_action` → system Observation → forces new Thought or Final Answer.

## Chatbot baseline failure (same user query)

Chatbot returns plausible prose with specific VND totals **without** calling tools — fails multi-step scoring heuristic (`precise figures without tools`).

**Lesson**: ReAct wins when grounding matters; chatbot wins on simple FAQ (`simple_visa`).
