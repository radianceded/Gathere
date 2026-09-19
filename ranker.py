"""Ranking utilities for Gathere place recommendations.

All factors (total travel time, worst single trip, fairness gap, distance to
the center, POI rating) are min-max normalized within the current candidate
set before weighting, so metrics with different units contribute on a
comparable 0-1 scale. A lower score is better.
"""

WEIGHTS = {
    "balanced": {"total": 0.40, "max": 0.25, "fairness": 0.20, "center": 0.10, "rating": 0.05},
    "fair": {"total": 0.25, "max": 0.30, "fairness": 0.30, "center": 0.10, "rating": 0.05},
    "fast": {"total": 0.55, "max": 0.25, "fairness": 0.10, "center": 0.05, "rating": 0.05},
}

# Extra score per candidate, scaled by the ratio of participants whose route
# could not be planned. Prevents candidates with only 2 of 4 usable routes
# from looking artificially good.
INCOMPLETE_DATA_PENALTY = 0.10

# Neutral normalized value used for missing data (e.g. a POI without rating).
NEUTRAL_SCORE = 0.5


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


def _rating_value(candidate: dict) -> float | None:
    """AMap returns an empty rating when a POI has none; treat 0 as missing too."""
    rating = candidate.get("rating")
    if rating in ("", None, [], 0, "0"):
        return None
    value = _safe_float(rating, default=None)
    return value if value and value > 0 else None


def _minmax(values: list[float | None]) -> list[float]:
    """Scale raw values into [0, 1]; missing values get the neutral score."""
    known = [v for v in values if v is not None]
    if not known:
        return [NEUTRAL_SCORE] * len(values)

    lo, hi = min(known), max(known)
    if hi - lo < 1e-9:
        return [NEUTRAL_SCORE] * len(values)

    span = hi - lo
    return [NEUTRAL_SCORE if v is None else (v - lo) / span for v in values]


def _strategy_weights(strategy: str) -> dict[str, float]:
    return WEIGHTS.get(strategy, WEIGHTS["balanced"])


def score_candidates(candidates: list[dict], strategy: str = "balanced") -> list[dict]:
    """Attach a normalized score and score_breakdown to every candidate."""
    if not candidates:
        return []

    totals, maxes, gaps, centers, ratings = [], [], [], [], []
    for candidate in candidates:
        durations = _duration_values(candidate.get("routes", []))
        totals.append(sum(durations))
        maxes.append(max(durations))
        gaps.append(max(durations) - min(durations))
        centers.append(_safe_float(candidate.get("distance"), 0.0))
        ratings.append(_rating_value(candidate))

    weights = _strategy_weights(strategy)
    norm_totals = _minmax(totals)
    norm_maxes = _minmax(maxes)
    norm_gaps = _minmax(gaps)
    norm_centers = _minmax([c / 1000 for c in centers])
    norm_ratings = _minmax(ratings)

    scored = []
    for idx, candidate in enumerate(candidates):
        routes = candidate.get("routes", [])
        missing_ratio = (
            sum(1 for r in routes if r.get("duration_min") is None) / len(routes)
            if routes
            else 0.0
        )

        breakdown = {
            "total": norm_totals[idx] * weights["total"],
            "max": norm_maxes[idx] * weights["max"],
            "fairness": norm_gaps[idx] * weights["fairness"],
            "center_distance": norm_centers[idx] * weights["center"],
            "rating": norm_ratings[idx] * weights["rating"],
            "incomplete_data": INCOMPLETE_DATA_PENALTY * missing_ratio,
        }
        score = round(
            breakdown["total"]
            + breakdown["max"]
            + breakdown["fairness"]
            + breakdown["center_distance"]
            - breakdown["rating"]
            + breakdown["incomplete_data"],
            4,
        )

        durations = _duration_values(routes)
        enriched = dict(candidate)
        enriched.update({
            "score": score,
            "total_duration_min": round(sum(durations), 1),
            "max_duration_min": round(max(durations), 1),
            "min_duration_min": round(min(durations), 1),
            "fairness_gap_min": round(max(durations) - min(durations), 1),
            "center_distance_m": centers[idx],
            "rating": _safe_float(ratings[idx], 0.0),
            "score_breakdown": {k: round(v, 4) for k, v in breakdown.items()},
            # legacy aliases kept for older callers
            "total_duration": round(sum(durations), 1),
            "max_duration": round(max(durations), 1),
            "fairness_gap": round(max(durations) - min(durations), 1),
        })
        scored.append(enriched)

    return scored


def rank_candidates(
    candidates: list[dict],
    top_k: int = 3,
    strategy: str = "balanced",
) -> list[dict]:
    usable = [c for c in candidates if _duration_values(c.get("routes", []))]
    scored = score_candidates(usable, strategy=strategy)
    scored.sort(key=lambda x: (x["score"], x["total_duration_min"]))
    return scored[:top_k]
