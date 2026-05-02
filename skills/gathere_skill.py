"""Skill wrapper for Gathere's meeting-place recommendation capability."""

from tools import recommend_places


def run_gathere_skill(
    participants: list[dict],
    keywords: str = "餐厅",
    city: str = "苏州",
    mode: str = "transit",
    top_k: int = 3,
    strategy: str = "balanced",
) -> dict:
    """Run the reusable Gathere recommendation skill.

    This function intentionally delegates geocoding, POI search, route
    planning, centroid calculation, and ranking to tools.recommend_places.
    """

    result = recommend_places(
        participants=participants,
        keywords=keywords,
        city=city,
        mode=mode,
        top_k=top_k,
        strategy=strategy,
    )

    if isinstance(result, dict):
        result.setdefault("participants", participants)
        result.setdefault("keywords", keywords)
        result.setdefault("city", city)
        result.setdefault("mode", mode)
        result.setdefault("strategy", strategy)

    return result
