# Successful Trace — Multi-step Central Vietnam Tour

**Case**: `multi_central_beach`  
**Agent**: v2  
**Expected flow**: search → budget → itinerary → Final Answer

## User input

```
Two travelers, 4 days in Central Vietnam, love beaches and food, max 2,000,000 VND per day,
standard tier. Suggest destinations, total budget for Da Nang, and an explore itinerary.
```

## Trace (abbreviated)

```text
AGENT_START  version=v2

AGENT_STEP 1
Thought: Need catalog matches for Central beaches under 2M VND/day.
Action: search_destinations(region="Central", budget_per_day=2000000, interests="beach,food")

TOOL_CALL search_destinations
Observation: Da Nang, Nha Trang listed with VND/USD rates…

AGENT_STEP 2
Thought: Estimate standard package for Da Nang, 4 days, 2 travelers.
Action: estimate_tour_budget(destination="Da Nang", days=4, travelers=2, tier="standard")

TOOL_CALL estimate_tour_budget
Observation: TOTAL: 14,400,000 VND (~$576)…

AGENT_STEP 3
Thought: Build explore-style day plan.
Action: build_itinerary(destination="Da Nang", days=4, travel_style="explore")

TOOL_CALL build_itinerary
Observation: Day 1–4 activities…

AGENT_STEP 4
Final Answer: Recommended Da Nang — 4 days, 2 travelers, standard tier…

AGENT_END  completed=true  tools=[search_destinations, estimate_tour_budget, build_itinerary]
```

## Why this passes evaluation

- ≥2 tools invoked on a `multi_step` case.
- Prices and schedule grounded in tool output, not invented in Thought lines.
