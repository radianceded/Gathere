"""End-to-end pipeline test with all AMap network calls faked."""

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


def fake_search(location, keywords="餐厅", radius=3000, page_size=10):
    lng, lat = map(float, location.split(","))
    pois = []
    for i in range(15):
        pois.append({
            "name": f"poi-{location}-{i}",
            "address": "somewhere",
            "location": f"{lng + 0.001 * i:.6f},{lat:.6f}",
            "distance": i * 100,
            "type": "餐厅",
            "rating": "4.0" if i % 3 else "",
        })
    return {"count": len(pois), "pois": pois}


def fake_route(origin, destination, mode="transit", city="苏州"):
    return {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "distance_km": 5.0,
        "duration_min": 20.0,
    }


def test_recommend_pipeline_offline(monkeypatch):
    monkeypatch.setattr(tools, "geocode", fake_geocode)
    monkeypatch.setattr(tools, "search_nearby_pois", fake_search)
    monkeypatch.setattr(tools, "route_plan", fake_route)

    result = recommend_places(
        participants=[
            {"name": "A", "address": "a"},
            {"name": "B", "address": "b"},
            {"name": "C", "address": "c"},
        ],
        keywords="火锅",
    )

    assert "error" not in result, result.get("error")
    assert result["center"]["method"] == "geometric_median"

    # 4 search centers x 15 POIs = 60 pooled candidates, coarse-filtered to 10.
    assert result["candidate_count"] == 10
    assert result["filtered_count"] == 50
    assert len(result["places"]) == 3

    for place in result["places"]:
        assert "score" in place and "score_breakdown" in place
        assert len(place["routes"]) == 3
        assert all(r["duration_min"] == 20.0 for r in place["routes"])


def test_recommend_pipeline_search_failure(monkeypatch):
    monkeypatch.setattr(tools, "geocode", fake_geocode)

    def broken_search(location, keywords="餐厅", radius=3000, page_size=10):
        return {"error": "POI 搜索请求失败: boom"}

    monkeypatch.setattr(tools, "search_nearby_pois", broken_search)
    monkeypatch.setattr(tools, "route_plan", fake_route)

    result = recommend_places(
        participants=[{"name": "A", "address": "a"}, {"name": "B", "address": "b"}],
    )
    assert "error" in result


def test_recommend_pipeline_tolerates_partial_route_failure(monkeypatch):
    monkeypatch.setattr(tools, "geocode", fake_geocode)
    monkeypatch.setattr(tools, "search_nearby_pois", fake_search)

    def flaky_route(origin, destination, mode="transit", city="苏州"):
        # Person "C" (location c) never gets a route; everyone else does.
        if origin == COORDS["c"]:
            return {"error": "未找到公交路线"}
        return fake_route(origin, destination, mode, city)

    monkeypatch.setattr(tools, "route_plan", flaky_route)

    result = recommend_places(
        participants=[
            {"name": "A", "address": "a"},
            {"name": "B", "address": "b"},
            {"name": "C", "address": "c"},
        ],
    )

    assert "error" not in result, result.get("error")
    assert result["candidate_count"] > 0
    for place in result["places"]:
        durations = [r["duration_min"] for r in place["routes"]]
        assert durations.count(None) == 1
        assert place["score_breakdown"]["incomplete_data"] > 0
