"""MCP server tests.

Protocol-level tests run the real stdio server in a subprocess, mirroring
how MCP clients actually spawn it. Tool-level tests monkeypatch the AMap
layer and stay offline.
"""

import asyncio
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from mcp import ClientSession  # noqa: E402
from mcp.client.stdio import StdioServerParameters, stdio_client  # noqa: E402

import mcp_server  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TOOLS = ["recommend_meeting_places", "geocode_address", "plan_route"]


def _server_params() -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=[str(PROJECT_ROOT / "mcp_server.py")],
        cwd=str(PROJECT_ROOT),
    )


def _run(coro):
    return asyncio.run(coro)


def test_list_tools_over_stdio():
    async def inner():
        async with stdio_client(_server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return [t.name for t in result.tools]

    names = _run(inner())
    for tool in TOOLS:
        assert tool in names


def test_tool_descriptions_are_chinese_friendly():
    tools = asyncio.run(mcp_server.mcp.list_tools())
    descriptions = {t.name: t.description for t in tools}
    assert "聚会" in descriptions["recommend_meeting_places"]
    assert "经纬度坐标" in descriptions["geocode_address"]


def test_recommend_wrapper_passes_participants(monkeypatch):
    captured = {}

    def fake_recommend(**kwargs):
        captured.update(kwargs)
        return {"places": [{"name": "demo"}]}

    monkeypatch.setattr(mcp_server, "recommend_places", fake_recommend)

    result = mcp_server.recommend_meeting_places(
        participants=[
            mcp_server.Participant(name="A", address="a", mode="driving"),
            mcp_server.Participant(name="B", address="b"),
        ],
        keywords="火锅",
        max_cost=100,
    )

    assert result == {"places": [{"name": "demo"}]}
    assert captured["participants"] == [
        {"name": "A", "address": "a", "mode": "driving"},
        {"name": "B", "address": "b"},
    ]
    assert captured["max_cost"] == 100
    assert captured["keywords"] == "火锅"


def test_plan_route_resolves_place_names(monkeypatch):
    captured = {}

    def fake_geocode(address, city=""):
        assert city == "苏州"
        return {"name": address, "location": f"coord-for-{address}"}

    def fake_route(origin, destination, mode="transit", city="苏州"):
        captured.update(origin=origin, destination=destination, mode=mode)
        return {"duration_min": 25.0, "distance_km": 6.0}

    monkeypatch.setattr(mcp_server, "geocode", fake_geocode)
    monkeypatch.setattr(mcp_server, "route_plan", fake_route)

    result = mcp_server.plan_route(
        origin="苏州站",
        destination="120.585300,31.298900",
        mode="walking",
    )

    assert result == {"duration_min": 25.0, "distance_km": 6.0}
    assert captured == {
        "origin": "coord-for-苏州站",
        "destination": "120.585300,31.298900",
        "mode": "walking",
    }


def test_plan_route_reports_geocode_failure(monkeypatch):
    monkeypatch.setattr(
        mcp_server,
        "geocode",
        lambda address, city="": {"error": f"地理编码失败: {address}"},
    )

    result = mcp_server.plan_route(origin="不存在的地方xyz", destination="120.0,31.0")
    assert "error" in result


@pytest.mark.skipif(
    not (PROJECT_ROOT / ".env").exists(),
    reason="needs a real AMAP_API_KEY in .env",
)
def test_live_geocode_over_stdio():
    async def inner():
        async with stdio_client(_server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "geocode_address",
                    {"address": "苏州大学天赐庄校区", "city": "苏州"},
                )
                return json.loads(result.content[0].text)

    data = _run(inner())
    assert "error" not in data, data
    assert data["location"].count(",") == 1
