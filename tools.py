"""
Gathere - 高德地图 API 工具集
提供地理编码、POI周边搜索、路线规划三个核心能力
"""

import requests
from config import AMAP_API_KEY

# ============================================================
# Tool 1: 地理编码 - 地名 → 经纬度
# ============================================================

def geocode(address: str, city: str = "") -> dict:
    """将地址/地名转换为经纬度坐标"""
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": AMAP_API_KEY,
        "address": address,
        "output": "JSON",
    }
    if city:
        params["city"] = city

    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()

    if data.get("status") != "1" or not data.get("geocodes"):
        return {"error": f"地理编码失败: {data.get('info', '未知错误')}，地址: {address}"}

    geo = data["geocodes"][0]
    return {
        "name": address,
        "location": geo["location"],
        "formatted_address": geo.get("formatted_address", ""),
        "city": geo.get("city", ""),
        "district": geo.get("district", ""),
    }


# ============================================================
# Tool 2: POI 周边搜索
# ============================================================

def search_nearby_pois(
    location: str,
    keywords: str = "餐厅",
    radius: int = 3000,
    page_size: int = 10,
) -> dict:
    """在指定坐标附近搜索POI"""
    url = "https://restapi.amap.com/v5/place/around"
    params = {
        "key": AMAP_API_KEY,
        "location": location,
        "keywords": keywords,
        "radius": radius,
        "page_size": page_size,
        "show_fields": "business",
    }

    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()

    if data.get("status") != "1":
        return {"error": f"POI搜索失败: {data.get('info', '未知错误')}"}

    pois = []
    for poi in data.get("pois", []):
        pois.append({
            "name": poi.get("name", ""),
            "address": poi.get("address", ""),
            "location": poi.get("location", ""),
            "distance": poi.get("distance", ""),
            "tel": poi.get("business", {}).get("tel", "") if isinstance(poi.get("business"), dict) else "",
            "type": poi.get("type", ""),
            "rating": poi.get("business", {}).get("rating", "") if isinstance(poi.get("business"), dict) else "",
        })

    return {"count": len(pois), "pois": pois}


# ============================================================
# Tool 3: 路线规划
# ============================================================

def route_plan(
    origin: str,
    destination: str,
    mode: str = "transit",
    city: str = "苏州",
) -> dict:
    """计算从起点到终点的路线距离和耗时"""
    base_urls = {
        "driving": "https://restapi.amap.com/v3/direction/driving",
        "walking": "https://restapi.amap.com/v3/direction/walking",
        "transit": "https://restapi.amap.com/v3/direction/transit/integrated",
    }

    if mode not in base_urls:
        return {"error": f"不支持的出行方式: {mode}，请选择 driving/walking/transit"}

    url = base_urls[mode]
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

    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()

    if data.get("status") != "1":
        return {"error": f"路线规划失败: {data.get('info', '未知错误')}"}

    route = data.get("route", {})

    if mode in ("driving", "walking"):
        paths = route.get("paths", [])
        if not paths:
            return {"error": f"未找到{mode}路线"}
        path = paths[0]
        distance = int(path.get("distance", 0))
        duration = int(path.get("duration", 0))
    elif mode == "transit":
        transits = route.get("transits", [])
        if not transits:
            return {"error": "未找到公交路线"}
        transit = transits[0]
        distance = int(route.get("distance", 0))
        duration = int(transit.get("duration", 0))

    return {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "distance_km": round(distance / 1000, 1),
        "duration_min": round(duration / 60, 0),
    }


# ============================================================
# Tool 4: 计算地理中心点
# ============================================================

def compute_centroid(locations: list[str]) -> str:
    """计算多个坐标点的地理中心"""
    lngs, lats = [], []
    for loc in locations:
        parts = loc.split(",")
        lngs.append(float(parts[0]))
        lats.append(float(parts[1]))

    avg_lng = sum(lngs) / len(lngs)
    avg_lat = sum(lats) / len(lats)
    return f"{avg_lng:.6f},{avg_lat:.6f}"


# ============================================================
# OpenAI 格式的 function 定义（兼容 DeepSeek / 通义 / GPT 等）
# ============================================================

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
                        "description": "地址或地名，如'苏州大学本部'、'观前街'"
                    },
                    "city": {
                        "type": "string",
                        "description": "城市名，可选，用于提高准确性"
                    }
                },
                "required": ["address"]
            }
        }
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
                        "description": "搜索中心点坐标，格式'经度,纬度'"
                    },
                    "keywords": {
                        "type": "string",
                        "description": "搜索关键词，如'火锅'、'咖啡厅'、'KTV'、'餐厅'"
                    },
                    "radius": {
                        "type": "integer",
                        "description": "搜索半径（米），默认3000"
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "返回结果数量，默认10"
                    }
                },
                "required": ["location", "keywords"]
            }
        }
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
                        "description": "起点坐标，格式'经度,纬度'"
                    },
                    "destination": {
                        "type": "string",
                        "description": "终点坐标，格式'经度,纬度'"
                    },
                    "mode": {
                        "type": "string",
                        "description": "出行方式: driving(驾车), walking(步行), transit(公交)",
                        "enum": ["driving", "walking", "transit"]
                    },
                    "city": {
                        "type": "string",
                        "description": "城市名，公交模式下必填"
                    }
                },
                "required": ["origin", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compute_centroid",
            "description": "计算多个坐标点的地理中心。当需要确定多人位置的'中间地带'时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "locations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "坐标列表，每个格式'经度,纬度'"
                    }
                },
                "required": ["locations"]
            }
        }
    }
]

# Tool 名称到函数的映射
TOOL_MAP = {
    "geocode": geocode,
    "search_nearby_pois": search_nearby_pois,
    "route_plan": route_plan,
    "compute_centroid": compute_centroid,
}
