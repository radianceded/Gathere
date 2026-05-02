"""
Gathere - AMap API tools.
Provides geocoding, POI search, route planning, centroid calculation, and
multi-person place recommendation.
"""

import requests

from config import AMAP_API_KEY
from ranker import rank_candidates


def _safe_float(value, default=0.0):
    try:
        if value in ("", None, []):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _looks_like_coord(value: str) -> bool:
    """Return whether a value looks like an AMap 'lng,lat' coordinate."""

    if not isinstance(value, str) or "," not in value:
        return False

    try:
        lng, lat = value.split(",", 1)
        float(lng)
        float(lat)
        return True
    except ValueError:
        return False


def _normalize_route_result(route_result: dict) -> dict:
    """Normalize route_plan output into duration_min and distance_km fields."""

    if not isinstance(route_result, dict):
        return {
            "duration_min": None,
            "distance_km": None,
            "error": "路线结果格式异常",
            "raw": route_result,
        }

    if route_result.get("error"):
        return {
            "duration_min": None,
            "distance_km": None,
            "error": route_result.get("error"),
            "raw": route_result,
        }

    if "duration_min" in route_result or "distance_km" in route_result:
        return {
            "duration_min": _safe_float(route_result.get("duration_min"), default=None),
            "distance_km": _safe_float(route_result.get("distance_km"), default=None),
            "raw": route_result,
        }

    # Compatibility for raw AMap fields: duration is seconds, distance is meters.
    duration = _safe_float(route_result.get("duration"), default=0.0)
    distance = _safe_float(route_result.get("distance"), default=0.0)

    return {
        "duration_min": round(duration / 60, 1),
        "distance_km": round(distance / 1000, 2),
        "raw": route_result,
    }


def geocode(address: str, city: str = "") -> dict:
    """Convert an address/place name to an AMap coordinate."""

    if not AMAP_API_KEY:
        return {"error": "缺少 AMAP_API_KEY，请检查 .env 配置"}

    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": AMAP_API_KEY,
        "address": address,
        "output": "JSON",
    }

    if city:
        params["city"] = city

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
    except Exception as exc:
        return {"error": f"地理编码请求失败: {str(exc)}，地址: {address}"}

    if data.get("status") != "1" or not data.get("geocodes"):
        return {"error": f"地理编码失败: {data.get('info', '未知错误')}，地址: {address}"}

    geo = data["geocodes"][0]
    return {
        "name": address,
        "location": geo.get("location", ""),
        "formatted_address": geo.get("formatted_address", ""),
        "city": geo.get("city", ""),
        "district": geo.get("district", ""),
    }


def search_nearby_pois(
    location: str,
    keywords: str = "餐厅",
    radius: int = 3000,
    page_size: int = 10,
) -> dict:
    """Search POIs around a coordinate."""

    if not AMAP_API_KEY:
        return {"error": "缺少 AMAP_API_KEY，请检查 .env 配置"}

    url = "https://restapi.amap.com/v5/place/around"
    params = {
        "key": AMAP_API_KEY,
        "location": location,
        "keywords": keywords,
        "radius": radius,
        "page_size": page_size,
        "show_fields": "business",
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
    except Exception as exc:
        return {"error": f"POI 搜索请求失败: {str(exc)}"}

    if data.get("status") != "1":
        return {"error": f"POI 搜索失败: {data.get('info', '未知错误')}"}

    pois = []
    for poi in data.get("pois", []):
        business = poi.get("business", {})
        if not isinstance(business, dict):
            business = {}

        pois.append({
            "name": poi.get("name", ""),
            "address": poi.get("address", ""),
            "location": poi.get("location", ""),
            "distance": _safe_float(poi.get("distance"), default=0.0),
            "tel": business.get("tel", ""),
            "type": poi.get("type", ""),
            "rating": _safe_float(business.get("rating"), default=0.0),
        })

    return {
        "count": len(pois),
        "pois": pois,
    }


def route_plan(
    origin: str,
    destination: str,
    mode: str = "transit",
    city: str = "苏州",
) -> dict:
    """Calculate route distance and duration between two coordinates."""

    if not AMAP_API_KEY:
        return {"error": "缺少 AMAP_API_KEY，请检查 .env 配置"}

    base_urls = {
        "driving": "https://restapi.amap.com/v3/direction/driving",
        "walking": "https://restapi.amap.com/v3/direction/walking",
        "transit": "https://restapi.amap.com/v3/direction/transit/integrated",
    }

    if mode not in base_urls:
        return {"error": f"不支持的出行方式: {mode}，请选择 driving/walking/transit"}

    params = {
        "key": AMAP_API_KEY,
        "origin": origin,
        "destination": destination,
        "output": "JSON",
    }

    if mode == "transit":
        params["city"] = city
        params["strategy"] = 0

    if mode == "driving":
        params["strategy"] = 2

    try:
        resp = requests.get(base_urls[mode], params=params, timeout=10)
        data = resp.json()
    except Exception as exc:
        return {"error": f"路线规划请求失败: {str(exc)}"}

    if data.get("status") != "1":
        return {"error": f"路线规划失败: {data.get('info', '未知错误')}"}

    route = data.get("route", {})

    if mode in ("driving", "walking"):
        paths = route.get("paths", [])
        if not paths:
            return {"error": f"未找到 {mode} 路线"}

        path = paths[0]
        distance = int(float(path.get("distance", 0) or 0))
        duration = int(float(path.get("duration", 0) or 0))

    else:
        transits = route.get("transits", [])
        if not transits:
            return {"error": "未找到公交路线"}

        transit = transits[0]
        distance = int(float(route.get("distance", 0) or 0))
        duration = int(float(transit.get("duration", 0) or 0))

    return {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "distance_km": round(distance / 1000, 1),
        "duration_min": round(duration / 60, 1),
    }


def compute_centroid(locations: list[str]) -> dict:
    """Calculate the geographic centroid of multiple coordinates."""

    if not locations:
        return {"error": "缺少坐标列表"}

    lngs = []
    lats = []

    try:
        for loc in locations:
            parts = loc.split(",")
            if len(parts) != 2:
                return {"error": f"坐标格式错误: {loc}"}

            lngs.append(float(parts[0]))
            lats.append(float(parts[1]))

        avg_lng = sum(lngs) / len(lngs)
        avg_lat = sum(lats) / len(lats)

    except Exception as exc:
        return {"error": f"中心点计算失败: {str(exc)}"}

    return {
        "location": f"{avg_lng:.6f},{avg_lat:.6f}",
        "lng": round(avg_lng, 6),
        "lat": round(avg_lat, 6),
    }


def recommend_places(
    participants: list[dict],
    keywords: str = "餐厅",
    radius: int = 3000,
    page_size: int = 15,
    top_k: int = 3,
    mode: str = "transit",
    city: str = "苏州",
    strategy: str = "balanced",
) -> dict:
    """
    Recommend top meeting places from multiple participant locations.

    Internally calls geocode, compute_centroid, search_nearby_pois,
    route_plan, and rank_candidates.
    """

    if not participants:
        return {"error": "缺少参与者信息"}

    geocoded_participants = []

    for idx, person in enumerate(participants):
        name = person.get("name") or f"参与者{idx + 1}"
        address = person.get("address") or person.get("location") or ""

        if not address:
            return {"error": f"{name} 缺少出发位置"}

        if _looks_like_coord(address):
            geocoded_participants.append({
                "name": name,
                "address": address,
                "location": address,
                "geo": {
                    "name": address,
                    "location": address,
                    "formatted_address": address,
                    "city": city,
                    "district": "",
                },
            })
            continue

        geo_result = geocode(address, city=city)
        if geo_result.get("error"):
            return {
                "error": f"{name} 的位置解析失败：{geo_result.get('error')}",
                "participant": name,
                "address": address,
            }

        location = geo_result.get("location")
        if not location:
            return {
                "error": f"{name} 的位置没有返回有效坐标",
                "participant": name,
                "address": address,
                "raw": geo_result,
            }

        geocoded_participants.append({
            "name": name,
            "address": address,
            "location": location,
            "geo": geo_result,
        })

    locations = [p["location"] for p in geocoded_participants]
    centroid_result = compute_centroid(locations)
    if centroid_result.get("error"):
        return {"error": f"中心点计算失败：{centroid_result.get('error')}"}

    center_location = centroid_result.get("location")
    if not center_location:
        return {
            "error": "中心点计算没有返回有效坐标",
            "raw": centroid_result,
        }

    poi_result = search_nearby_pois(
        location=center_location,
        keywords=keywords,
        radius=radius,
        page_size=page_size,
    )
    if poi_result.get("error"):
        return {"error": poi_result.get("error")}

    pois = poi_result.get("pois", [])
    if not pois:
        return {
            "error": "没有搜索到合适的候选地点",
            "center_location": center_location,
            "keywords": keywords,
        }

    candidates = []
    skipped_candidates = []

    for poi in pois:
        poi_location = poi.get("location")
        if not poi_location:
            skipped_candidates.append({
                "name": poi.get("name", ""),
                "reason": "缺少 POI 坐标",
            })
            continue

        routes = []
        has_route_error = False

        for person in geocoded_participants:
            route_result = route_plan(
                origin=person["location"],
                destination=poi_location,
                mode=mode,
                city=city,
            )
            normalized_route = _normalize_route_result(route_result)

            if normalized_route.get("duration_min") is None:
                has_route_error = True

            routes.append({
                "participant": person["name"],
                "origin_address": person["address"],
                "duration_min": normalized_route.get("duration_min"),
                "distance_km": normalized_route.get("distance_km"),
                "error": normalized_route.get("error"),
                "raw": normalized_route.get("raw"),
            })

        if has_route_error:
            skipped_candidates.append({
                "name": poi.get("name", ""),
                "reason": "部分参与者路线规划失败",
                "routes": routes,
            })
            continue

        candidate = dict(poi)
        candidate["routes"] = routes
        candidates.append(candidate)

    if not candidates:
        return {
            "error": "所有候选地点的路线规划都失败了，无法排序",
            "participants": geocoded_participants,
            "center_location": center_location,
            "keywords": keywords,
            "skipped_candidates": skipped_candidates,
        }

    ranked_places = rank_candidates(
        candidates,
        top_k=top_k,
        strategy=strategy,
    )

    return {
        "participants": geocoded_participants,
        "center": centroid_result,
        "center_location": center_location,
        "keywords": keywords,
        "mode": mode,
        "city": city,
        "strategy": strategy,
        "candidate_count": len(candidates),
        "skipped_count": len(skipped_candidates),
        "count": len(ranked_places),
        "places": ranked_places,
    }


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "geocode",
            "description": "将地址或地名转换为经纬度坐标。当用户提到一个地点名称时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "地址或地名，如“苏州大学本部”、“观前街”",
                    },
                    "city": {
                        "type": "string",
                        "description": "城市名，可选，用于提高准确性",
                    },
                },
                "required": ["address"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_nearby_pois",
            "description": "在指定坐标附近搜索餐厅、KTV、咖啡厅等聚会场所。通常应在所有人位置的地理中心点附近搜索。",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "搜索中心点坐标，格式“经度,纬度”",
                    },
                    "keywords": {
                        "type": "string",
                        "description": "搜索关键词，如“火锅”、“咖啡厅”、“KTV”、“餐厅”",
                    },
                    "radius": {
                        "type": "integer",
                        "description": "搜索半径，单位米，默认 3000",
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "返回结果数量，默认 10",
                    },
                },
                "required": ["location", "keywords"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "route_plan",
            "description": "计算从起点到终点的路线距离和耗时。用于计算每个人到候选聚会地点的通勤成本。",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "起点坐标，格式“经度,纬度”",
                    },
                    "destination": {
                        "type": "string",
                        "description": "终点坐标，格式“经度,纬度”",
                    },
                    "mode": {
                        "type": "string",
                        "description": "出行方式: driving(驾车), walking(步行), transit(公交)",
                        "enum": ["driving", "walking", "transit"],
                    },
                    "city": {
                        "type": "string",
                        "description": "城市名，公交模式下必填",
                    },
                },
                "required": ["origin", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_centroid",
            "description": "计算多个坐标点的地理中心。当需要确定多人位置的“中间地带”时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "locations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "坐标列表，每个格式“经度,纬度”",
                    },
                },
                "required": ["locations"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_places",
            "description": "根据多人出发位置和聚会类型，综合考虑通勤时间、公平性、中心距离和 POI 评分，推荐 Top 聚会地点。多人聚会推荐时应优先使用这个工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "participants": {
                        "type": "array",
                        "description": "参与者列表，每个人包含姓名和出发位置",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "参与者姓名或代称",
                                },
                                "address": {
                                    "type": "string",
                                    "description": "参与者出发位置，例如苏州大学独墅湖校区",
                                },
                            },
                            "required": ["name", "address"],
                        },
                    },
                    "keywords": {
                        "type": "string",
                        "description": "想搜索的地点类型，例如餐厅、火锅、咖啡、KTV",
                        "default": "餐厅",
                    },
                    "radius": {
                        "type": "integer",
                        "description": "搜索半径，单位米，默认 3000",
                        "default": 3000,
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "候选地点数量，默认 15",
                        "default": 15,
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回推荐数量，默认 3",
                        "default": 3,
                    },
                    "mode": {
                        "type": "string",
                        "description": "出行方式：driving 驾车，walking 步行，transit 公交",
                        "enum": ["driving", "walking", "transit"],
                        "default": "transit",
                    },
                    "city": {
                        "type": "string",
                        "description": "城市名，默认苏州",
                        "default": "苏州",
                    },
                    "strategy": {
                        "type": "string",
                        "description": "推荐策略，balanced 表示综合平衡，fair 表示更重视公平，fast 表示更重视总通勤时间",
                        "enum": ["balanced", "fair", "fast"],
                        "default": "balanced",
                    },
                },
                "required": ["participants"],
            },
        },
    },
]


TOOL_MAP = {
    "geocode": geocode,
    "search_nearby_pois": search_nearby_pois,
    "route_plan": route_plan,
    "compute_centroid": compute_centroid,
    "recommend_places": recommend_places,
}
