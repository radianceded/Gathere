# ranker.py

def calculate_score(candidate: dict) -> float:
    routes = candidate.get("routes", [])

    durations = [
        route.get("duration")
        for route in routes
        if route.get("duration") is not None
    ]

    if not durations:
        return float("inf")

    total_duration = sum(durations)
    max_duration = max(durations)
    min_duration = min(durations)
    fairness_gap = max_duration - min_duration

    rating = candidate.get("rating", 0) or 0

    score = (
        total_duration * 0.45
        + max_duration * 0.30
        + fairness_gap * 0.20
        - rating * 2
    )

    return round(score, 2)


def rank_candidates(candidates: list[dict], top_k: int = 3) -> list[dict]:
    ranked = []

    for candidate in candidates:
        score = calculate_score(candidate)

        routes = candidate.get("routes", [])
        durations = [
            route.get("duration")
            for route in routes
            if route.get("duration") is not None
        ]

        if not durations:
            continue

        candidate["score"] = score
        candidate["total_duration"] = sum(durations)
        candidate["max_duration"] = max(durations)
        candidate["fairness_gap"] = max(durations) - min(durations)

        ranked.append(candidate)

    ranked.sort(key=lambda x: x["score"])
    return ranked[:top_k]