import math

from tools import (
    _coarse_filter,
    _haversine_km,
    _merge_pois,
    compute_centroid,
)


def test_two_points_converge_to_midpoint():
    result = compute_centroid(["120.0,31.0", "120.2,31.0"])
    assert abs(result["lng"] - 120.1) < 1e-4
    assert abs(result["lat"] - 31.0) < 1e-4


def test_geometric_median_resists_outlier():
    # Three participants clustered in Suzhou, one 200 km east. The arithmetic
    # mean would land near 120.55; the geometric median stays in the cluster.
    locations = [
        "120.00,31.00",
        "120.10,31.00",
        "120.20,31.00",
        "121.90,31.00",
    ]
    result = compute_centroid(locations)
    assert result["method"] == "geometric_median"
    assert 120.0 < result["lng"] < 120.3
    assert abs(result["lat"] - 31.0) < 1e-4


def test_single_point_and_bad_format():
    single = compute_centroid(["120.5,31.3"])
    assert single["lng"] == 120.5
    assert compute_centroid([]) == {"error": "缺少坐标列表"}
    assert "error" in compute_centroid(["120.5", "not-a-coord"])


def test_haversine_suzhou_to_shanghai():
    # Roughly 85 km between downtown Suzhou and downtown Shanghai.
    distance = _haversine_km(120.5853, 31.2989, 121.4737, 31.2304)
    assert 75 < distance < 95


def test_merge_pois_dedupes_and_recomputes_distance():
    poi_x = {"name": "X", "location": "120.01,31.0"}
    poi_y = {"name": "Y", "location": "120.05,31.0"}
    poi_z = {"name": "Z", "location": "120.02,31.0"}

    merged = _merge_pois(
        [[poi_x, poi_y], [dict(poi_x), poi_z]],
        center_location="120.0,31.0",
    )

    assert len(merged) == 3
    by_name = {p["name"]: p for p in merged}
    # 0.01 deg of longitude at lat 31 is roughly 950 m from the center,
    # and Y sits 5x farther along the same meridian.
    assert 900 < by_name["X"]["distance"] < 1000
    assert abs(by_name["Y"]["distance"] / by_name["X"]["distance"] - 5) < 0.01


def test_merge_pois_drops_unparseable_locations():
    merged = _merge_pois(
        [[{"name": "bad", "address": "no coord"}, {"name": "ok", "location": "120.01,31.0"}]],
        center_location="120.0,31.0",
    )
    assert [p["name"] for p in merged] == ["ok"]


def test_coarse_filter_keeps_nearest_candidates():
    participants = ["120.0,31.0"]
    candidates = [
        {"name": "near_a", "location": "120.01,31.0"},
        {"name": "far", "location": "121.00,31.00"},
        {"name": "near_b", "location": "120.02,31.0"},
    ]

    kept, removed = _coarse_filter(candidates, participants, limit=2)

    assert removed == 1
    assert {p["name"] for p in kept} == {"near_a", "near_b"}


def test_coarse_filter_noop_below_limit():
    candidates = [{"name": "a", "location": "120.01,31.0"}]
    kept, removed = _coarse_filter(candidates, ["120.0,31.0"], limit=10)
    assert kept == candidates
    assert removed == 0


def test_compute_centroid_local_km_frame():
    # At latitude 31, longitude degrees are ~15% shorter than latitude degrees;
    # a symmetric cross must still produce a center at its middle.
    result = compute_centroid([
        "120.00,31.00",
        "120.10,31.00",
        "120.05,31.05",
        "120.05,30.95",
    ])
    assert abs(result["lng"] - 120.05) < 0.01
    assert abs(result["lat"] - 31.0) < 0.01
