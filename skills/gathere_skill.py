"""Skill wrapper for Gathere's meeting-place recommendation capability."""

from config import DEFAULT_CITY
from tools import recommend_places


def run_gathere_skill(
    participants: list[dict],
    keywords: str = "餐厅",
    city: str = DEFAULT_CITY,
    mode: str = "transit",
    top_k: int = 3,
    strategy: str = "balanced",
    max_cost: float | None = None,
) -> dict:
    """Run the reusable Gathere recommendation skill.

    This function intentionally delegates geocoding, POI search, route
    planning, centroid calculation, and ranking to tools.recommend_places.
    Participants may carry their own `mode` (driving/walking/transit) to
    override the global one.
    """

    result = recommend_places(
        participants=participants,
        keywords=keywords,
        city=city,
        mode=mode,
        top_k=top_k,
        strategy=strategy,
        max_cost=max_cost,
    )

    if isinstance(result, dict):
        result.setdefault("participants", participants)
        result.setdefault("keywords", keywords)
        result.setdefault("city", city)
        result.setdefault("mode", mode)
        result.setdefault("strategy", strategy)
        result.setdefault("max_cost", max_cost)

    return result
