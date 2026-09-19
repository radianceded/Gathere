from viz import build_map_points, extract_last_recommendation


RECOMMEND_RESULT = {
    "participants": [
        {"name": "A", "location": "120.00,31.00"},
        {"name": "B", "location": "120.10,31.00"},
    ],
    "center": {"lng": 120.05, "lat": 31.0},
    "places": [
        {"name": "店A", "location": "120.05,31.01"},
        {"name": "店B", "location": "120.06,31.02"},
    ],
}


def tool_message(payload) -> dict:
    import json
    return {"role": "tool", "content": json.dumps(payload, ensure_ascii=False)}


def test_extract_returns_last_recommendation():
    history = [
        {"role": "user", "content": "hi"},
        tool_message({"count": 3, "pois": []}),  # search_nearby_pois result
        tool_message(RECOMMEND_RESULT),
        {"role": "assistant", "content": "推荐如下"},
        tool_message({**RECOMMEND_RESULT, "keywords": "KTV"}),  # newer call
    ]

    result = extract_last_recommendation(history)
    assert result["keywords"] == "KTV"


def test_extract_handles_empty_and_malformed():
    assert extract_last_recommendation([]) is None
    assert extract_last_recommendation(None) is None
    assert extract_last_recommendation([
        {"role": "tool", "content": "not json{"},
        {"role": "assistant", "content": "text"},
    ]) is None


def test_build_map_points_rows():
    rows = build_map_points(RECOMMEND_RESULT)

    kinds = [row["kind"] for row in rows]
    assert kinds.count("参与者") == 2
    assert kinds.count("中心点") == 1
    assert kinds.count("推荐地点") == 2

    center_row = next(row for row in rows if row["kind"] == "中心点")
    assert center_row["lat"] == 31.0
    assert center_row["lon"] == 120.05

    # Every row carries a color for st.map.
    assert all(len(row["color"]) == 3 for row in rows)


def test_build_map_points_skips_bad_locations():
    result = {
        "participants": [{"name": "X", "location": "no-coord"}],
        "center": {},
        "places": [],
    }
    assert build_map_points(result) == []
