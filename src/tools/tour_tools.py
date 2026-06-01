"""
Mock tools for Personalized Package Tour Planning AI Assistant.
Mock data for ReAct lab — no external API calls.
"""
from typing import Any, Dict, List

VND_PER_USD = 25_000

DESTINATION_CATALOG: List[Dict[str, Any]] = [
    {
        "name": "Da Nang",
        "region": "Central",
        "highlights": ["beach", "food", "culture"],
        "budget_per_day_vnd": 1_800_000,
        "best_season": "March–August",
        "intl_note": "International airport; English widely spoken in hotels/tours",
    },
    {
        "name": "Phu Quoc",
        "region": "South",
        "highlights": ["beach", "resort", "diving"],
        "budget_per_day_vnd": 2_500_000,
        "best_season": "November–April",
        "intl_note": "Resort island; visa on arrival at Phu Quoc airport for many nationalities",
    },
    {
        "name": "Sa Pa",
        "region": "North",
        "highlights": ["trekking", "culture", "food"],
        "budget_per_day_vnd": 1_500_000,
        "best_season": "September–November",
        "intl_note": "Cool mountain climate; book guided treks; limited English in remote villages",
    },
    {
        "name": "Hoi An",
        "region": "Central",
        "highlights": ["culture", "food", "ancient town"],
        "budget_per_day_vnd": 1_600_000,
        "best_season": "February–April",
        "intl_note": "UNESCO old town; easy day trips from Da Nang airport",
    },
    {
        "name": "Nha Trang",
        "region": "Central",
        "highlights": ["beach", "island", "food"],
        "budget_per_day_vnd": 2_000_000,
        "best_season": "January–August",
        "intl_note": "Beach hub; many Russian/Korean tour operators; card payments common",
    },
]


def _region_matches(query: str, dest_region: str) -> bool:
    q, r = query.lower().strip(), dest_region.lower()
    if not q:
        return True
    return q in r or r in q


def _vnd_to_usd(vnd: int) -> int:
    return max(1, round(vnd / VND_PER_USD))

TIER_MULTIPLIER = {
    "budget": 0.85,
    "standard": 1.0,
    "luxury": 1.35,
}

ITINERARY_TEMPLATES: Dict[str, List[str]] = {
    "relax": [
        "Check-in resort, beach and spa",
        "Morning island tour / snorkeling, free afternoon",
        "Local food, night market shopping",
    ],
    "explore": [
        "City tour & cultural highlights",
        "Outdoor activities (trekking / boat / craft village)",
        "Guided street-food experience",
    ],
    "family": [
        "Kid-friendly park / beach",
        "Light activities: aquarium / cultural village",
        "Family buffet / restaurant, early rest",
    ],
}


def search_destinations(region: str = "", budget_per_day: int = 0, interests: str = "") -> str:
    """
    Find suitable destinations in the internal catalog.
    region: North | Central | South (leave blank = all)
    budget_per_day: maximum budget in VND/day (0 = no filter)
    interests: comma-separated keywords, e.g.: beach,food
    """
    interest_tokens = [t.strip().lower() for t in interests.split(",") if t.strip()]
    matches = []

    for dest in DESTINATION_CATALOG:
        if region and not _region_matches(region, dest["region"]):
            continue
        if budget_per_day and dest["budget_per_day_vnd"] > budget_per_day:
            continue
        if interest_tokens:
            hl = " ".join(dest["highlights"]).lower()
            if not any(tok in hl for tok in interest_tokens):
                continue
        matches.append(dest)

    if not matches:
        return "No suitable destination found. Try expanding the budget or changing the region/interests."

    lines = ["Suggested destinations (budgets in VND; ~USD at 25,000 VND/USD):"]
    for d in matches:
        usd = _vnd_to_usd(d["budget_per_day_vnd"])
        lines.append(
            f"- {d['name']} ({d['region']}): ~{d['budget_per_day_vnd']:,} VND/day (~${usd}/day); "
            f"highlights: {', '.join(d['highlights'])}; best season: {d['best_season']}; "
            f"tip: {d.get('intl_note', '')}"
        )
    return "\n".join(lines)


def estimate_tour_budget(
    destination: str,
    days: int = 3,
    travelers: int = 2,
    tier: str = "standard",
) -> str:
    """
    Estimate package tour cost (VND) for a destination.
    tier: budget | standard | luxury
    """
    dest = next(
        (d for d in DESTINATION_CATALOG if d["name"].lower() in destination.lower()),
        None,
    )
    if not dest:
        return f"No budget data for '{destination}'. Use search_destinations first."

    mult = TIER_MULTIPLIER.get(tier.lower().strip(), 1.0)
    base = dest["budget_per_day_vnd"] * mult
    hotel = int(base * 0.45 * days * travelers)
    food = int(base * 0.25 * days * travelers)
    transport = int(base * 0.15 * days * travelers)
    activities = int(base * 0.15 * days * travelers)
    total = hotel + food + transport + activities

    total_usd = _vnd_to_usd(total)
    per_traveler_usd = _vnd_to_usd(total // travelers)
    return (
        f"Tour estimate for {destination} — {days} days, {travelers} travelers, '{tier}' tier:\n"
        f"- Accommodation: {hotel:,} VND (~${_vnd_to_usd(hotel)})\n"
        f"- Food: {food:,} VND (~${_vnd_to_usd(food)})\n"
        f"- Local transport: {transport:,} VND (~${_vnd_to_usd(transport)})\n"
        f"- Activities: {activities:,} VND (~${_vnd_to_usd(activities)})\n"
        f"TOTAL: {total:,} VND (~${total_usd}) — ~{total // travelers:,} VND/traveler (~${per_traveler_usd})"
    )


def build_itinerary(destination: str, days: int = 3, travel_style: str = "explore") -> str:
    """
    Create a daily itinerary (mock).
    travel_style: relax | explore | family
    """
    style_key = travel_style.lower().strip()
    template = ITINERARY_TEMPLATES.get(style_key)
    if not template:
        template = ITINERARY_TEMPLATES["explore"]

    lines = [f"Suggested itinerary — {destination} ({days} days, style: {travel_style}):"]
    for i in range(days):
        activity = template[i % len(template)]
        lines.append(f"Day {i + 1}: {activity}")
    lines.append("Note: Can be adjusted based on weather and personal preferences.")
    return "\n".join(lines)


def get_tour_tools() -> List[Dict[str, Any]]:
    """Register 3 tools for the ReAct agent."""
    return [
        {
            "name": "search_destinations",
            "description": (
                "Search Vietnam destinations for international visitors. "
                "Parameters: region (North|Central|South), budget_per_day (integer VND per day), "
                "interests (comma-separated, e.g. 'beach,food'). Returns USD approximations."
            ),
            "func": search_destinations,
        },
        {
            "name": "estimate_tour_budget",
            "description": (
                "Estimate tour cost. Parameters: destination (city name), "
                "days (number of days), travelers (number of guests), tier (budget|standard|luxury)."
            ),
            "func": estimate_tour_budget,
        },
        {
            "name": "build_itinerary",
            "description": (
                "Create a daily itinerary. Parameters: destination, days, "
                "travel_style (relax|explore|family)."
            ),
            "func": build_itinerary,
        },
    ]