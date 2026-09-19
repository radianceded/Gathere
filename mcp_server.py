"""Gathere MCP Server.

Expose Gathere's meeting-place recommendation capability as MCP tools, so
any MCP-compatible client (ZCode, Claude Desktop, Cursor, AstrBot, ...) can
call it directly. The tools wrap tools.recommend_places and reuse the whole
pipeline: geocoding, geometric-median center, multi-center candidate search,
route planning, and normalized fairness ranking.

Run with stdio transport (the usual client-spawned mode):

    python mcp_server.py
"""

from typing import Literal, Optional

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel

from config import DEFAULT_CITY
from tools import _looks_like_coord, geocode, recommend_places, route_plan

mcp = MCPServer(
    "gathere",
    instructions=(
        "Gathere：多人聚会地点协商助手。核心工具是 recommend_meeting_places，"
        "输入每位参与者的出发位置，返回综合通勤时间、公平性和 POI 质量的 Top 推荐。"
        "geocode_address 与 plan_route 是配套的地点解析和路线计算工具。"
    ),
)


class Participant(BaseModel):
    name: str
    address: str
    # Per-participant travel mode; falls back to the tool-level mode.
    mode: Optional[Literal["driving", "walking", "transit"]] = None


@mcp.tool()
def recommend_meeting_places(
    participants: list[Participant],
    keywords: str = "餐厅",
    city: str = DEFAULT_CITY,
    mode: Literal["driving", "walking", "transit"] = "transit",
    max_cost: Optional[float] = None,
    top_k: int = 3,
    strategy: Literal["balanced", "fair", "fast"] = "balanced",
) -> dict:
    """Recommend fair meeting places for a group of people.

    多人聚会地点推荐：综合每个人的通勤时间、通勤公平性、距中心点距离和
    POI 评分，返回 Top_k 个推荐及每人通勤明细。每位参与者可指定自己的
    出行方式（例如有人开车、其他人坐地铁）；max_cost 为人均消费预算上限（元）。
    """
    return recommend_places(
        participants=[p.model_dump(exclude_none=True) for p in participants],
        keywords=keywords,
        city=city,
        mode=mode,
        max_cost=max_cost,
        top_k=top_k,
        strategy=strategy,
    )


@mcp.tool()
def geocode_address(address: str, city: str = "") -> dict:
    """Convert a place name or address to an AMap coordinate.

    将地址或地名转换为高德经纬度坐标，例如"苏州大学本部"、"观前街"。
    """
    return geocode(address, city=city)


def _resolve(location: str, city: str) -> str | dict:
    """Return a coordinate string, geocoding plain place names on the way."""
    if _looks_like_coord(location):
        return location

    geo = geocode(location, city=city)
    if geo.get("error") or not geo.get("location"):
        return geo if geo.get("error") else {"error": f"无法解析位置: {location}"}
    return geo["location"]


@mcp.tool()
def plan_route(
    origin: str,
    destination: str,
    mode: Literal["driving", "walking", "transit"] = "transit",
    city: str = DEFAULT_CITY,
) -> dict:
    """Calculate route duration and distance between two points.

    计算两点之间的路线耗时与距离。起终点可以直接给坐标（"经度,纬度"），
    也可以给地名（会自动地理编码）。公交/地铁用 transit，开车用 driving。
    """
    origin_loc = _resolve(origin, city)
    if isinstance(origin_loc, dict):
        return origin_loc

    destination_loc = _resolve(destination, city)
    if isinstance(destination_loc, dict):
        return destination_loc

    return route_plan(
        origin=origin_loc,
        destination=destination_loc,
        mode=mode,
        city=city,
    )


if __name__ == "__main__":
    mcp.run()
