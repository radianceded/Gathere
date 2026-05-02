"""Ranking utilities for Gathere place recommendations."""


def _safe_float(value, default=0.0):
    try:
        if value in ("", None, []):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _duration_values(routes: list[dict]) -> list[float]:
    durations = []
    for route in routes:
        duration = route.get("duration_min")
        if duration is None:
            continue
        duration_value = _safe_float(duration, default=None)
        if duration_value is None:
            continue
        durations.append(duration_value)
    return durations


def _strategy_weights(strategy: str) -> dict[str, float]:
    weights = {
        "balanced": {
            "total": 0.45,
            "max": 0.30,
            "fairness": 0.20,
            "center_distance": 1.00,
            "rating": 2.00,
        },
        "fair": {
            "total": 0.35,
            "max": 0.35,
            "fairness": 0.25,
            "center_distance": 1.00,
            "rating": 2.00,
        },
        "fast": {
            "total": 0.60,
            "max": 0.25,
            "fairness": 0.10,
            "center_distance": 1.00,
            "rating": 2.00,
        },
    }
    return weights.get(strategy, weights["balanced"])


def calculate_score(candidate: dict, strategy: str = "balanced") -> float:
    routes = candidate.get("routes", [])
    durations = _duration_values(routes)

    if not durations:
        return float("inf")

    total_duration = sum(durations)
    max_duration = max(durations)
    min_duration = min(durations)
    fairness_gap = max_duration - min_duration

    # AMap POI distance is the distance from the search center, usually meters.
    center_distance_m = _safe_float(candidate.get("distance"), 0.0)
    center_distance_km = center_distance_m / 1000

    rating = _safe_float(candidate.get("rating"), 0.0)
    weights = _strategy_weights(strategy)

    score = (
        total_duration * weights["total"]
        + max_duration * weights["max"]
        + fairness_gap * weights["fairness"]
        + center_distance_km * weights["center_distance"]
        - rating * weights["rating"]
    )

    return round(score, 2)


def rank_candidates(
    candidates: list[dict],
    top_k: int = 3,
    strategy: str = "balanced",
) -> list[dict]:
    ranked = []

    for candidate in candidates:
        routes = candidate.get("routes", [])
        durations = _duration_values(routes)

        if not durations:
            continue

        score = calculate_score(candidate, strategy=strategy)
        total_duration = round(sum(durations), 1)
        max_duration = round(max(durations), 1)
        min_duration = round(min(durations), 1)
        fairness_gap = round(max_duration - min_duration, 1)
        center_distance_m = _safe_float(candidate.get("distance"), 0.0)
        rating = _safe_float(candidate.get("rating"), 0.0)

        enriched_candidate = dict(candidate)
        enriched_candidate.update({
            "score": score,
            "total_duration_min": total_duration,
            "max_duration_min": max_duration,
            "min_duration_min": min_duration,
            "fairness_gap_min": fairness_gap,
            "total_duration": total_duration,
            "max_duration": max_duration,
            "fairness_gap": fairness_gap,
            "center_distance_m": center_distance_m,
            "rating": rating,
        })

        ranked.append(enriched_candidate)

    ranked.sort(key=lambda x: x["score"])
    return ranked[:top_k]
