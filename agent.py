"""
Gathere - Agent 核心
基于 OpenAI 兼容 API 的 tool-calling 循环
支持 DeepSeek / 通义千问 / 智谱 / Moonshot / GPT 等任何兼容模型
"""

import json
from openai import OpenAI
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from tools import TOOL_DEFINITIONS, TOOL_MAP

# 客户端
client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
)

# Agent 的系统提示词
SYSTEM_PROMPT = """你是 Gathere，一个多人聚会地点协商助手。你的任务是帮助一群朋友找到最佳的聚会地点。

## 你的能力
你有以下工具可以使用：
1. **geocode**: 将地名转为坐标（如"苏大本部" → 经纬度）
2. **search_nearby_pois**: 在某个坐标附近搜索餐厅、KTV等场所
3. **route_plan**: 计算某人从起点到目的地的通勤时间和距离
4. **compute_centroid**: 计算多人位置的地理中心点

## 工作流程
当用户告诉你参与聚会的人员和他们的位置时，按以下步骤操作：

1. **收集信息**: 理解有多少人参与，每个人的出发位置在哪里。如果信息不完整，主动追问。
2. **地理编码**: 把每个人的地名转为坐标。
3. **计算中心点**: 用 compute_centroid 找到大家位置的地理中心。
4. **搜索候选地点**: 在中心点附近搜索用户想要的场所类型（默认餐厅）。
5. **计算通勤成本**: 为每个候选地点，计算每个人到达的时间和距离。
<<<<<<< HEAD
6. **排序推荐**: 按照总通勤时间或最大通勤时间排序，给出 Top 3 推荐。
=======
6. 排序推荐: 按照总通勤时间或最大通勤时间排序，给出 Top 3 推荐。
>>>>>>> 784ba4a (feat: add ranker for fair place recommendation)

## 交互风格
- 用中文回复
- 简洁直接，不要废话
- 每次推荐给出具体的数据（每人耗时、总耗时）
- 如果用户追加约束（如"要有包间"、"人均100以内"），根据约束调整搜索
- 如果用户想换一种场所类型，重新搜索

## 重要注意事项
- 默认出行方式是公交（transit），除非用户指定
<<<<<<< HEAD
- 默认城市是苏州，除非用户指定其他城市
=======
>>>>>>> 784ba4a (feat: add ranker for fair place recommendation)
- 搜索半径默认3km，如果结果太少可以扩大到5km
- 推荐时要说明理由
"""


def run_agent_turn(conversation_history: list[dict]) -> tuple[str, list[dict]]:
    """
    执行一轮 Agent 交互（可能包含多次 tool calling）
<<<<<<< HEAD
    
    参数:
        conversation_history: 对话历史
    
    返回:
        (agent_response_text, updated_conversation_history)
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    while True:
=======
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    max_steps = 10

    for _ in range(max_steps):
>>>>>>> 784ba4a (feat: add ranker for fair place recommendation)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )

        choice = response.choices[0]
        message = choice.message

<<<<<<< HEAD
        # 将 assistant 消息加入历史
        # 构建可序列化的 assistant 消息
=======
>>>>>>> 784ba4a (feat: add ranker for fair place recommendation)
        assistant_msg = {
            "role": "assistant",
            "content": message.content or "",
        }
<<<<<<< HEAD
=======

>>>>>>> 784ba4a (feat: add ranker for fair place recommendation)
        if message.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in message.tool_calls
            ]
<<<<<<< HEAD
        messages.append(assistant_msg)

        # 如果有 tool calls，执行工具
        if message.tool_calls:
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
=======

        messages.append(assistant_msg)

        if message.tool_calls:
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name

>>>>>>> 784ba4a (feat: add ranker for fair place recommendation)
                try:
                    func_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    func_args = {}

                if func_name in TOOL_MAP:
                    try:
                        result = TOOL_MAP[func_name](**func_args)
                    except Exception as e:
                        result = {"error": f"工具执行出错: {str(e)}"}
                else:
                    result = {"error": f"未知工具: {func_name}"}

<<<<<<< HEAD
                # 工具结果作为 tool message 加入
=======
>>>>>>> 784ba4a (feat: add ranker for fair place recommendation)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })

        else:
<<<<<<< HEAD
            # 没有 tool calls，Agent 完成回复
            final_text = message.content or ""
            # 从 messages 中去掉 system prompt，返回纯对话历史
            updated_history = [m for m in messages if m["role"] != "system"]
            return final_text, updated_history

=======
            final_text = message.content or ""
            updated_history = [m for m in messages if m["role"] != "system"]
            return final_text, updated_history

    final_text = "这次推荐过程调用工具次数过多，已自动停止。请你补充更明确的位置或聚会类型后再试。"
    updated_history = [m for m in messages if m["role"] != "system"]
    return final_text, updated_history
>>>>>>> 784ba4a (feat: add ranker for fair place recommendation)

def chat(user_message: str, conversation_history: list[dict] = None) -> tuple[str, list[dict]]:
    """
    顶层聊天接口
    """
    if conversation_history is None:
        conversation_history = []

    conversation_history.append({
        "role": "user",
        "content": user_message,
    })

    response_text, updated_history = run_agent_turn(conversation_history)
    return response_text, updated_history


# 命令行测试入口
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
            response, history = chat(user_input, history)
            print(f"\nGathere: {response}")
        except Exception as e:
            print(f"\n[错误] {e}")
