import json
import re
from typing import Any

import httpx
from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star


GATHERE_API_URL = "http://127.0.0.1:8000/recommend"


class GatherePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("gathere")
    async def gathere(self, event: AstrMessageEvent):
        raw = event.message_str.strip()
        query = self._remove_command(raw)

        if not query:
            yield event.plain_result(self._help_text())
            return

        try:
            payload = self._parse_query(query)
        except ValueError as e:
            yield event.plain_result(f"参数格式不对：{e}\n\n{self._help_text()}")
            return

        yield event.plain_result("正在调用 Gathere 计算推荐地点，稍等一下。")

        try:
            data = await self._call_gathere(payload)
            text = self._format_result(data)
            yield event.plain_result(text)

        except httpx.ConnectError:
            yield event.plain_result(
                "连接不到 Gathere FastAPI。\n"
                "请确认已经启动：python -m uvicorn api:app --host 127.0.0.1 --port 8000"
            )
        except httpx.TimeoutException:
            yield event.plain_result("Gathere 请求超时了，可以稍后再试。")
        except httpx.HTTPStatusError as e:
            logger.exception("Gathere HTTP status error")
            yield event.plain_result(f"Gathere 接口返回错误状态码：{e.response.status_code}")
        except Exception as e:
            logger.exception("Gathere plugin error")
            yield event.plain_result(f"Gathere 调用失败：{type(e).__name__}: {e}")

    def _remove_command(self, raw: str) -> str:
        raw = raw.strip()
        raw = re.sub(r"^/gathere\s*", "", raw)
        raw = re.sub(r"^gathere\s*", "", raw)
        return raw.strip()

    def _parse_query(self, query: str) -> dict[str, Any]:
        """
        输入格式：
        /gathere 我@苏州大学天赐庄校区；小王@园区湖东邻里中心；小李@新区狮山路 | 火锅 | 苏州

        转换为 Gathere /recommend 接口格式：
        {
            "participants": [
                {"name": "我", "address": "苏州大学天赐庄校区"},
                {"name": "小王", "address": "园区湖东邻里中心"}
            ],
            "keywords": "火锅",
            "city": "苏州",
            "mode": "transit",
            "top_k": 3,
            "strategy": "balanced"
        }
        """
        parts = [p.strip() for p in query.split("|")]

        if len(parts) < 2:
            raise ValueError("至少需要写：参与者位置 | 关键词")

        people_text = parts[0]
        keywords = parts[1]
        city = parts[2] if len(parts) >= 3 and parts[2] else "苏州"

        raw_people = [
            p.strip()
            for p in re.split(r"[；;，,\n]", people_text)
            if p.strip()
        ]

        if len(raw_people) < 2:
            raise ValueError("至少需要两个人的位置")

        participants = []

        for i, item in enumerate(raw_people, start=1):
            if "@" in item:
                name, address = item.split("@", 1)
                name = name.strip() or f"用户{i}"
                address = address.strip()
            else:
                name = f"用户{i}"
                address = item.strip()

            if not address:
                raise ValueError("有人缺少地址")

            participants.append(
                {
                    "name": name,
                    "address": address,
                }
            )

        return {
            "participants": participants,
            "keywords": keywords,
            "city": city,
            "mode": "transit",
            "top_k": 3,
            "strategy": "balanced",
        }

    async def _call_gathere(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(GATHERE_API_URL, json=payload)
            response.raise_for_status()
            return response.json()

    def _format_result(self, data: dict[str, Any]) -> str:
        places = data.get("places") or []

        if not places:
            pretty = json.dumps(data, ensure_ascii=False, indent=2)
            if len(pretty) > 1800:
                pretty = pretty[:1800] + "\n……内容过长，已截断。"
            return "Gathere 没有返回可用推荐地点，原始返回如下：\n\n" + pretty

        keywords = data.get("keywords", "聚会地点")
        city = data.get("city", "未知城市")
        candidate_count = data.get("candidate_count", "未知")
        center_location = data.get("center_location", "未知")

        lines = [
            f"📍Gathere 推荐结果：{city} · {keywords}",
            f"候选地点数：{candidate_count}",
            f"计算中心点：{center_location}",
            "",
        ]

        for idx, place in enumerate(places[:3], start=1):
            name = place.get("name", "未知地点")
            address = place.get("address", "地址未知")
            rating = place.get("rating", "暂无")
            score = place.get("score", "未知")
            center_distance = place.get(
                "center_distance_m",
                place.get("distance", "未知"),
            )

            total_duration = place.get(
                "total_duration_min",
                place.get("total_duration", "未知"),
            )
            max_duration = place.get(
                "max_duration_min",
                place.get("max_duration", "未知"),
            )
            fairness_gap = place.get(
                "fairness_gap_min",
                place.get("fairness_gap", "未知"),
            )

            lines.append(f"{idx}. {name}")
            lines.append(f"地址：{address}")
            lines.append(f"评分：{rating}")
            lines.append(f"综合得分：{score}")
            lines.append(f"距中心点：{center_distance} 米")
            lines.append(f"总通勤：{total_duration} 分钟")
            lines.append(f"最长单人通勤：{max_duration} 分钟")
            lines.append(f"公平性差值：{fairness_gap} 分钟")

            routes = place.get("routes") or []
            if routes:
                lines.append("通勤明细：")
                for route in routes:
                    participant = route.get("participant", "未知参与者")
                    duration = route.get("duration_min", "未知")
                    distance = route.get("distance_km", "未知")
                    lines.append(f"- {participant}：{duration} 分钟，约 {distance} km")

            lines.append("")

        return "\n".join(lines).strip()

    def _help_text(self) -> str:
        return (
            "用法：\n"
            "/gathere 人名@位置；人名@位置 | 关键词 | 城市\n\n"
            "示例：\n"
            "/gathere 我@苏州大学天赐庄校区；小王@园区湖东邻里中心；小李@新区狮山路 | 火锅 | 苏州\n\n"
            "不写姓名也可以：\n"
            "/gathere 苏州大学天赐庄校区；园区湖东邻里中心；新区狮山路 | 咖啡 | 苏州"
        )