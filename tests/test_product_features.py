"""Tests for max_cost budget filtering and per-participant travel modes."""

import tools
from tools import recommend_places


COORDS = {
    "a": "120.00,31.00",
    "b": "120.10,31.00",
    "c": "120.05,31.05",
}


def fake_geocode(address, city=""):
    return {
        "name": address,
        "location": COORDS[address],
        "formatted_address": address,
        "city": city,
        "district": "",
    }


def make_search(cost_for):
    def fake_search(location, keywords="餐厅", radius=3000, page_size=10):
        lng, lat = map(float, location.split(","))
        pois = []
        for i in range(15):
            pois.append({
                "name": f"poi-{location}-{i}",
                "address": "somewhere",
                "location": f"{lng + 0.001 * i:.6f},{lat:.6f}",
                "distance": i * 100,
                "rating": "4.0",
                # Route the raw AMap-style cost through the real parser,
                # mirroring what search_nearby_pois does.
                "cost": tools._parse_cost(cost_for(i)),
            })
        return {"count": len(pois), "pois": pois}

    return fake_search

    return fake_search


def fake_route(origin, destination, mode="transit", city="苏州"):
    return {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "distance_km": 5.0,
        "duration_min": 20.0,
    }


def test_max_cost_filters_over_budget_pois(monkeypatch):
    monkeypatch.setattr(tools, "geocode", fake_geocode)
    monkeypatch.setattr(tools, "search_nearby_pois", make_search(
        lambda i: "50" if i % 2 == 0 else "200"
    ))
    monkeypatch.setattr(tools, "route_plan", fake_route)

    result = recommend_places(
        participants=[{"name": "A", "address": "a"}, {"name": "B", "address": "b"}],
        max_cost=100,
    )

    assert "error" not in result, result.get("error")
    assert result["max_cost"] == 100
    # 3 search centers (centroid + 2 participants) x 15 POIs = 45 pooled
    # (no location overlap); the 7 odd-indexed ones per center cost 200.
    assert result["budget_filtered_count"] == 21
    assert result["candidate_count"] == 10
    for place in result["places"]:
        assert place.get("cost") is None or place["cost"] <= 100


def test_unknown_cost_is_kept_under_budget_filter(monkeypatch):
    monkeypatch.setattr(tools, "geocode", fake_geocode)
    monkeypatch.setattr(tools, "search_nearby_pois", make_search(lambda i: None))
    monkeypatch.setattr(tools, "route_plan", fake_route)

    result = recommend_places(
        participants=[{"name": "A", "address": "a"}, {"name": "B", "address": "b"}],
        max_cost=50,
    )

    assert "error" not in result, result.get("error")
    assert result["budget_filtered_count"] == 0
    assert result["candidate_count"] == 10


def test_everything_over_budget_reports_budget_error(monkeypatch):
    monkeypatch.setattr(tools, "geocode", fake_geocode)
    monkeypatch.setattr(tools, "search_nearby_pois", make_search(lambda i: "300"))
    monkeypatch.setattr(tools, "route_plan", fake_route)

    result = recommend_places(
        participants=[{"name": "A", "address": "a"}, {"name": "B", "address": "b"}],
        max_cost=100,
    )

    assert "error" in result
    assert "预算" in result["error"]


def test_per_participant_mode_reaches_route_plan(monkeypatch):
    monkeypatch.setattr(tools, "geocode", fake_geocode)
    monkeypatch.setattr(tools, "search_nearby_pois", make_search(lambda i: None))

    route_modes = []

    def recording_route(origin, destination, mode="transit", city="苏州"):
        route_modes.append(mode)
        return fake_route(origin, destination, mode, city)

    monkeypatch.setattr(tools, "route_plan", recording_route)

    result = recommend_places(
        participants=[
            {"name": "A", "address": "a", "mode": "driving"},
            {"name": "B", "address": "b"},
            {"name": "C", "address": "c", "mode": "walking"},
        ],
    )

    assert "error" not in result, result.get("error")
    assert route_modes.count("driving") == result["candidate_count"]
    assert route_modes.count("walking") == result["candidate_count"]
    assert route_modes.count("transit") == result["candidate_count"]

    for place in result["places"]:
        mode_by_person = {r["participant"]: r["mode"] for r in place["routes"]}
        assert mode_by_person == {"A": "driving", "B": "transit", "C": "walking"}


def test_invalid_participant_mode_rejected(monkeypatch):
    monkeypatch.setattr(tools, "geocode", fake_geocode)

    result = recommend_places(
        participants=[
            {"name": "A", "address": "a"},
            {"name": "B", "address": "b", "mode": "rocket"},
        ],
    )

    assert "error" in result
    assert "B" in result["error"]
