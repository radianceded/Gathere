"""
Gathere - Agent core.
OpenAI-compatible tool-calling loop for DeepSeek, Qwen, GLM, Moonshot, GPT, etc.
"""

import json

from openai import OpenAI

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from tools import TOOL_DEFINITIONS, TOOL_MAP


client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
)


SYSTEM_PROMPT = """你是 Gathere，一个多人聚会地点协商助手。你的任务是帮助一群朋友找到最佳的聚会地点。

## 你的能力
你有以下工具可以使用：
1. **recommend_places**: 根据多人出发位置和聚会类型，自动完成地理编码、中心点计算、POI 搜索、路线规划和综合排序。
2. **geocode**: 将地名转为坐标（如“苏大本部” -> 经纬度）。
3. **search_nearby_pois**: 在某个坐标附近搜索餐厅、KTV 等场所。
4. **route_plan**: 计算某人从起点到目的地的通勤时间和距离。
5. **compute_centroid**: 计算多人位置的地理中心点。

## 工作流程
当用户告诉你参与聚会的人员和他们的位置时，优先调用 recommend_places。信息不完整时先追问，不要编造地址或人数。

如需拆分执行，可以按以下步骤操作：
1. 收集信息：理解有多少人参与，每个人的出发位置在哪里。
2. 地理编码：把每个人的地名转为坐标。
3. 计算中心点：用 compute_centroid 找到大家位置的地理中心。
4. 搜索候选地点：在中心点附近搜索用户想要的场所类型（默认餐厅）。
5. 计算通勤成本：为每个候选地点，计算每个人到达的时间和距离。
6. 排序推荐：综合总通勤时间、最长通勤时间、公平性、中心距离和 POI 评分，给出 Top 推荐。

## 交互风格
- 用中文回复。
- 简洁直接，不要废话。
- 每次推荐给出具体数据，例如每人耗时、总耗时、最长耗时和推荐理由。
- 如果用户追加约束（如“要有包间”、“人均100以内”），根据约束调整搜索。
- 如果用户想换一种场所类型，重新推荐。

## 重要注意事项
- 默认出行方式是公交（transit），除非用户指定。
- 默认城市是苏州，除非用户指定其他城市。
- 搜索半径默认 3km，如果结果太少可以扩大到 5km。
- 多人聚会推荐时优先调用 recommend_places。
"""


def _serialize_tool_calls(tool_calls) -> list[dict]:
    return [
        {
            "id": tool_call.id,
            "type": "function",
            "function": {
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments,
            },
        }
        for tool_call in tool_calls
    ]


def run_agent_turn(
    conversation_history: list[dict],
    max_steps: int = 10,
) -> tuple[str, list[dict]]:
    """Run one agent turn. The loop may execute multiple tool calls."""

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    for _ in range(max_steps):
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )

        message = response.choices[0].message
        assistant_msg = {
            "role": "assistant",
            "content": message.content or "",
        }

        if message.tool_calls:
            assistant_msg["tool_calls"] = _serialize_tool_calls(message.tool_calls)

        messages.append(assistant_msg)

        if not message.tool_calls:
            final_text = message.content or ""
            updated_history = [m for m in messages if m["role"] != "system"]
            return final_text, updated_history

        for tool_call in message.tool_calls:
            func_name = tool_call.function.name

            try:
                func_args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                func_args = {}

            if func_name not in TOOL_MAP:
                result = {"error": f"未知工具: {func_name}"}
            else:
                try:
                    result = TOOL_MAP[func_name](**func_args)
                except Exception as exc:
                    result = {"error": f"工具执行出错: {str(exc)}"}

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

    final_text = "这次推荐过程调用工具次数过多，已自动停止。请补充更明确的位置或聚会类型后再试。"
    updated_history = [m for m in messages if m["role"] != "system"]
    return final_text, updated_history


def chat(
    user_message: str,
    conversation_history: list[dict] | None = None,
) -> tuple[str, list[dict]]:
    """Top-level chat interface."""

    if conversation_history is None:
        conversation_history = []

    conversation_history.append({
        "role": "user",
        "content": user_message,
    })

    return run_agent_turn(conversation_history)


if __name__ == "__main__":
    print("=" * 50)
    print("  Gathere - 多人聚会地点协商助手")
    print(f"  模型: {LLM_MODEL} @ {LLM_BASE_URL}")
    print("  输入 'quit' 退出")
    print("=" * 50)

    history = None
    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            print("再见！")
            break
        if not user_input:
            continue

        try:
            response_text, history = chat(user_input, history)
            print(f"\nGathere: {response_text}")
        except Exception as exc:
            print(f"\n[错误] {exc}")
