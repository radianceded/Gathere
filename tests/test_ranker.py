from ranker import rank_candidates


def make_candidate(name, durations, rating=None, distance=1000.0):
    """durations may contain None to simulate a failed route plan."""
    routes = [
        {"participant": f"p{i}", "duration_min": d}
        for i, d in enumerate(durations)
    ]
    return {
        "name": name,
        "routes": routes,
        "rating": rating,
        "distance": distance,
    }


def test_higher_rating_wins_when_travel_equal():
    candidates = [
        make_candidate("A", [30, 30, 30], rating=3.0),
        make_candidate("B", [30, 30, 30], rating=4.8),
    ]
    ranked = rank_candidates(candidates, top_k=2)
    assert ranked[0]["name"] == "B"


def test_missing_rating_is_neutral_not_punished():
    # A has no rating, B is mediocre, C is good: missing data must sit
    # between them instead of ranking below a true 2.5-rated place.
    candidates = [
        make_candidate("A", [30, 30], rating=None),
        make_candidate("B", [30, 30], rating=2.5),
        make_candidate("C", [30, 30], rating=4.5),
    ]
    ranked = rank_candidates(candidates, top_k=3)
    order = [c["name"] for c in ranked]
    assert order.index("C") < order.index("A") < order.index("B")


def test_fair_strategy_prefers_balanced_group():
    unbalanced = make_candidate("unbalanced", [20, 20, 20, 60])
    balanced = make_candidate("balanced", [35, 35, 35, 35])

    ranked = rank_candidates([unbalanced, balanced], top_k=2, strategy="fair")
    assert ranked[0]["name"] == "balanced"

    # Under the fast strategy the shorter total wins despite the outlier.
    ranked = rank_candidates([unbalanced, balanced], top_k=2, strategy="fast")
    assert ranked[0]["name"] == "unbalanced"


def test_incomplete_data_penalized():
    complete = make_candidate("complete", [30, 30], distance=1000.0)
    # Same usable durations, but one participant's route plan failed.
    incomplete = make_candidate("incomplete", [30, 30, None], distance=1000.0)

    ranked = rank_candidates([complete, incomplete], top_k=2)
    scores = {c["name"]: c["score"] for c in ranked}
    assert scores["complete"] < scores["incomplete"]
    assert "incomplete" in incomplete_keys(ranked)


def incomplete_keys(ranked):
    return [
        c["name"] for c in ranked
        if c.get("score_breakdown", {}).get("incomplete_data", 0) > 0
    ]


def test_identical_candidates_get_equal_scores():
    a = make_candidate("A", [30, 31], rating=4.0, distance=800)
    b = make_candidate("B", [30, 31], rating=4.0, distance=800)
    ranked = rank_candidates([a, b], top_k=2)
    assert ranked[0]["score"] == ranked[1]["score"]


def test_top_k_limits_output():
    candidates = [make_candidate(f"p{i}", [10 + i, 10 + i]) for i in range(5)]
    ranked = rank_candidates(candidates, top_k=2)
    assert len(ranked) == 2


def test_score_breakdown_present():
    ranked = rank_candidates([make_candidate("A", [30, 40], rating=4.0)], top_k=1)
    breakdown = ranked[0]["score_breakdown"]
    assert set(breakdown) == {
        "total", "max", "fairness", "center_distance", "rating", "incomplete_data",
    }
