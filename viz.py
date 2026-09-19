"""Helpers that turn a recommend_places result into map-ready data."""

import json

# st.map reads RGB colors from a per-row "color" column.
COLORS = {
    "participant": [14, 105, 246],  # blue
    "center": [255, 140, 0],        # orange
    "place": [214, 39, 40],         # red
}

KIND_LABELS = {
    "participant": "参与者",
    "center": "中心点",
    "place": "推荐地点",
}


def extract_last_recommendation(history: list[dict] | None) -> dict | None:
    """Return the most recent recommend_places tool result in agent history.

    Tool results are stored as JSON strings; recommendation results are the
    ones containing both "places" and "participants".
    """

    for message in reversed(history or []):
        if message.get("role") != "tool":
            continue
        try:
            data = json.loads(message.get("content") or "")
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, dict) and "places" in data and "participants" in data:
            return data
    return None


def _lnglat(value) -> tuple[float, float] | None:
    if not isinstance(value, str) or "," not in value:
        return None
    try:
        lng, lat = value.split(",", 1)
        return float(lat), float(lng)
    except ValueError:
        return None


def build_map_points(result: dict) -> list[dict]:
    """Build one row per mappable point: participants, center, and places."""

    rows: list[dict] = []

    def add_row(kind: str, name: str, lnglat: tuple | None):
        if lnglat is None:
            return
        lat, lng = lnglat
        rows.append({
            "name": name,
            "kind": KIND_LABELS[kind],
            "lat": lat,
            "lon": lng,
            "color": COLORS[kind],
        })

    for person in result.get("participants", []):
        add_row("participant", person.get("name", "参与者"), _lnglat(person.get("location")))

    center = result.get("center") or {}
    if center.get("lng") and center.get("lat"):
        add_row("center", "中心点", (float(center["lat"]), float(center["lng"])))

    for place in result.get("places", []):
        add_row("place", place.get("name", "推荐地点"), _lnglat(place.get("location")))

    return rows
