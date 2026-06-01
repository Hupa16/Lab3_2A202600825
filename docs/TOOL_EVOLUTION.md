# Tool Design Evolution — Personalized Tour Planning Assistant

Topic: **AI Trợ Lý Lập Kế Hoạch Tour Trọn Gói Cá Nhân Hóa** (international users, English UI).

## v0 (Brainstorm — not implemented)

| Idea | Why rejected |
|------|----------------|
| Single `plan_tour(json)` | Black box — LLM cannot inspect intermediate results; hard to debug traces |
| 10+ micro-tools (weather, flights, hotels) | Scope creep for Day 3 lab; mock data maintenance |

## v1 (Shipped — 3 tools)

| Tool | Inputs | Output |
|------|--------|--------|
| `search_destinations` | `region`, `budget_per_day` (VND), `interests` | Ranked list from catalog + USD hint |
| `estimate_tour_budget` | `destination`, `days`, `travelers`, `tier` | Line-item VND/USD breakdown |
| `build_itinerary` | `destination`, `days`, `travel_style` | Day-by-day activities |

**Design choices**

- Mock catalog in `src/tools/tour_tools.py` — reproducible demos without external APIs.
- VND as source of truth; USD shown via `25,000 VND/USD` for international users.
- `intl_note` per destination for visa/airport context.

## v2 (After failure traces)

| Issue in v1 traces | Tool / agent fix |
|--------------------|------------------|
| `region="Central Vietnam"` no match | `_region_matches()` substring logic |
| `tier="premium"` unknown | `TIER_ALIASES` → `luxury` |
| `travel_style="adventure"` unknown | `STYLE_ALIASES` → `explore` |
| Hallucinated tool `search_destination` | `TOOL_ALIASES` in agent v2 |
| Wrong city in budget after search | Agent prompt: call `search_destinations` before `estimate_tour_budget` |

## v3 (Future production)

- Replace mock catalog with DB + RAG over official tourism pages.
- Add `check_flight_availability` only when real API keys exist.
- JSON Schema tool definitions for native function-calling models.
