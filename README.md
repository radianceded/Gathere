# 📍 Gathere

**多人聚会地点协商助手** — 基于 LLM + 高德地图 API 的智能 Agent

## 解决什么问题

几个朋友想聚餐，每个人在城市不同位置。去哪吃？谁来的路最远？有没有一个“对大家都公平”的地方？

Gathere 帮你回答这些问题。告诉它每个人在哪，它会：

1. 在大家位置的“中间地带”搜索候选地点
2. 计算每个人到每个候选地点的通勤时间
3. 使用综合评分函数对候选地点排序
4. 推荐更公平、更合适的 Top 3 方案
5. 支持追加约束，例如“要有包间”“想吃火锅”“人均 100 以内”

相比单纯按距离中心点推荐，Gathere 会综合考虑：

- 平均通勤时间
- 最长单人通勤时间
- 通勤公平性差值
- 距离中心点远近
- POI 评分

它的目标不是简单地找一个“离中心点最近”的地方，而是尽量找到一个对所有参与者都更容易接受的聚会地点。

## 项目特色

Gathere 将 LLM Agent、地图工具调用、路线规划和公平性排序结合起来，把“去哪聚会”这个模糊问题拆成了可计算的推荐流程。

项目目前支持三种使用方式：

1. **Streamlit 聊天界面**：适合直接交互和演示
2. **Gathere Skill**：适合被其他 Agent 或业务逻辑复用
3. **FastAPI 接口**：适合作为后端服务，被网页端、QQ Bot、插件或其他系统调用

## 技术架构

```text
用户
 │
 ├── Streamlit 聊天界面
 │
 ├── Gathere Skill
 │
 └── FastAPI /recommend 接口
              │
              ▼
        Agent 核心
        (LLM, tool use)
              │
     ┌────────┼──────────┬──────────┬──────────┐
     ▼        ▼          ▼          ▼
  地理编码   POI 搜索   路线规划   中心点计算
 (高德API)  (高德API)  (高德API)  (本地计算)
              │
              ▼
        综合评分排序
        (ranker.py)
              │
              ▼
        Top 3 推荐结果
```

## 核心模块

```text
Gathere/
├── app.py                  # Streamlit 聊天界面
├── agent.py                # Agent 主逻辑
├── ranker.py               # 二次排序与公平性评分
├── gathere_skill.py        # Gathere Skill 封装
├── api.py                  # FastAPI 服务入口
├── requirements.txt        # 项目依赖
├── .env.example            # 环境变量示例
└── README.md
```

其中：

- `agent.py` 负责理解用户输入，并调用地图相关工具
- `ranker.py` 负责对候选地点进行综合排序
- `gathere_skill.py` 将推荐能力封装为可复用 Skill
- `api.py` 将推荐能力暴露为 HTTP 接口
- `app.py` 提供 Streamlit 可视化聊天入口

## 快速开始

### 1. 准备 API Key

需要准备两个 Key：

- **LLM API Key**：任意 OpenAI 兼容服务，例如 DeepSeek、通义千问、智谱、Moonshot 等
- **高德地图 Key**：[高德开放平台](https://console.amap.com/dev/key/app)，选择 Web 服务

### 2. 安装依赖

```bash
git clone https://github.com/radianceded/Gathere.git
cd Gathere
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

`.env` 示例：

```env
LLM_API_KEY=your_llm_api_key_here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

AMAP_API_KEY=your_amap_api_key_here
```

## 使用方式一：Streamlit 聊天界面

推荐用于本地演示和交互测试。

```bash
streamlit run app.py
```

启动后，在浏览器中输入类似问题：

```text
我们四个人周六想聚餐。
我在苏大本部，小王在园区湖东邻里中心，
小李在新区狮山路，小张在吴中区宝带西路。
想吃火锅，人均 100 左右。
```

Gathere 会自动执行：

1. 将 4 个地名转为坐标
2. 计算多人位置的地理中心点
3. 在中心点附近搜索火锅店
4. 计算每个人到每家店的通勤时间
5. 使用 `ranker.py` 进行综合评分排序
6. 返回 Top 3 推荐方案，并附带每个人的通勤数据

## 使用方式二：命令行模式

适合快速调试 Agent 主流程。

```bash
python agent.py
```

## 使用方式三：Gathere Skill 调用

`Gathere Skill` 将地点检索、路线规划、二次排序流程封装成一个可复用能力，方便被其他 Agent、脚本或后端服务直接调用。

示例代码：

```python
from gathere_skill import GathereSkill

skill = GathereSkill()

result = skill.recommend(
    people=[
        {"name": "我", "location": "苏大本部"},
        {"name": "小王", "location": "园区湖东邻里中心"},
        {"name": "小李", "location": "新区狮山路"},
        {"name": "小张", "location": "吴中区宝带西路"},
    ],
    target="火锅",
    city="苏州",
    top_k=3,
    constraints=["人均100以内", "适合聚餐"]
)

print(result)
```

返回结果通常包含：

```python
{
    "center": {
        "lng": 120.62,
        "lat": 31.30
    },
    "recommendations": [
        {
            "name": "示例火锅店",
            "address": "苏州市某某路",
            "score": 87.5,
            "avg_duration": 28,
            "max_duration": 42,
            "fairness_gap": 18,
            "routes": [
                {
                    "person": "我",
                    "duration": 25,
                    "distance": 6200
                }
            ]
        }
    ]
}
```

Skill 适合用于：

- 被其他 Agent 作为工具调用
- 接入聊天机器人
- 接入网页应用后端
- 作为推荐模块嵌入其他项目
- 单独测试 Gathere 的核心推荐能力

## 使用方式四：FastAPI 接口调用

Gathere 也提供 FastAPI 服务，可以通过 HTTP 请求调用推荐能力。

### 1. 启动 FastAPI 服务

```bash
uvicorn api:app --reload
```

默认服务地址：

```text
http://127.0.0.1:8000
```

接口文档地址：

```text
http://127.0.0.1:8000/docs
```

### 2. `/recommend` 接口说明

请求方式：

```text
POST /recommend
```

请求参数示例：

```json
{
  "people": [
    {
      "name": "我",
      "location": "苏大本部"
    },
    {
      "name": "小王",
      "location": "园区湖东邻里中心"
    },
    {
      "name": "小李",
      "location": "新区狮山路"
    },
    {
      "name": "小张",
      "location": "吴中区宝带西路"
    }
  ],
  "target": "火锅",
  "city": "苏州",
  "top_k": 3,
  "constraints": [
    "人均100以内",
    "适合朋友聚餐"
  ]
}
```

字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `people` | list | 参与聚会的人，每个人包含姓名和位置 |
| `name` | string | 参与者姓名 |
| `location` | string | 参与者所在位置，可以是地名、商圈或详细地址 |
| `target` | string | 目标地点类型，例如火锅、咖啡、烧烤、商场 |
| `city` | string | 搜索城市 |
| `top_k` | int | 返回推荐数量 |
| `constraints` | list | 额外约束，例如预算、包间、停车、营业时间等 |

### 3. 使用 curl 调用

```bash
curl -X POST "http://127.0.0.1:8000/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "people": [
      {"name": "我", "location": "苏大本部"},
      {"name": "小王", "location": "园区湖东邻里中心"},
      {"name": "小李", "location": "新区狮山路"},
      {"name": "小张", "location": "吴中区宝带西路"}
    ],
    "target": "火锅",
    "city": "苏州",
    "top_k": 3,
    "constraints": ["人均100以内", "适合朋友聚餐"]
  }'
```

### 4. 使用 Python requests 调用

```python
import requests

url = "http://127.0.0.1:8000/recommend"

payload = {
    "people": [
        {"name": "我", "location": "苏大本部"},
        {"name": "小王", "location": "园区湖东邻里中心"},
        {"name": "小李", "location": "新区狮山路"},
        {"name": "小张", "location": "吴中区宝带西路"},
    ],
    "target": "火锅",
    "city": "苏州",
    "top_k": 3,
    "constraints": ["人均100以内", "适合朋友聚餐"]
}

response = requests.post(url, json=payload)
print(response.json())
```

### 5. 返回结果示例

```json
{
  "query": "火锅",
  "city": "苏州",
  "center": {
    "lng": 120.62,
    "lat": 31.30
  },
  "recommendations": [
    {
      "rank": 1,
      "name": "示例火锅店",
      "address": "苏州市某某路",
      "location": {
        "lng": 120.61,
        "lat": 31.29
      },
      "score": 87.5,
      "avg_duration": 28,
      "max_duration": 42,
      "fairness_gap": 18,
      "routes": [
        {
          "person": "我",
          "duration": 25,
          "distance": 6200
        },
        {
          "person": "小王",
          "duration": 30,
          "distance": 8100
        },
        {
          "person": "小李",
          "duration": 42,
          "distance": 12000
        },
        {
          "person": "小张",
          "duration": 15,
          "distance": 4300
        }
      ]
    }
  ]
}
```

FastAPI 接口适合用于：

- 接入网页前端
- 接入 QQ Bot / AstrBot
- 接入微信机器人或其他聊天入口
- 接入 ChatGPT Actions
- 部署到服务器后作为独立推荐服务使用

## 推荐排序逻辑

Gathere 的排序不是只看中心点距离，而是通过 `ranker.py` 对候选 POI 进行二次评分。

综合评分会考虑：

```text
综合得分 =
  平均通勤时间评分
+ 最长单人通勤时间评分
+ 公平性评分
+ 距离中心点评分
+ POI 质量评分
```

其中：

- **平均通勤时间**：整体路程越短越好
- **最长单人通勤时间**：避免某一个人特别远
- **公平性差值**：不同参与者之间的通勤时间差距越小越好
- **距离中心点远近**：候选地点不要过度偏离大家的中间区域
- **POI 评分**：尽量选择质量更高的地点

这种设计让推荐结果更偏向“多人协商公平性”，而不是简单选择几何中心附近的地点。

## 使用示例

```text
你: 我们四个人周六想聚餐。我在苏大本部，小王在园区湖东邻里中心，
    小李在新区狮山路，小张在吴中区宝带西路。想吃火锅。

Gathere: 推荐 3 个相对公平的火锅聚餐地点：

1. 示例火锅店 A
   - 平均通勤时间：28 分钟
   - 最长单人通勤时间：42 分钟
   - 公平性差值：18 分钟
   - 推荐理由：整体通勤时间较短，没有人需要明显绕远

2. 示例火锅店 B
   - 平均通勤时间：31 分钟
   - 最长单人通勤时间：39 分钟
   - 公平性差值：14 分钟
   - 推荐理由：虽然平均时间略高，但几个人通勤更均衡

3. 示例火锅店 C
   - 平均通勤时间：35 分钟
   - 最长单人通勤时间：45 分钟
   - 公平性差值：20 分钟
   - 推荐理由：POI 质量较高，适合对环境有要求的聚餐
```

## 版本迭代说明

### v0.1：核心功能实现

- 支持基于 LLM 的 Agent 对话
- 支持地理编码、POI 搜索、路线规划和中心点计算
- 支持根据多人位置推荐聚会地点

### v0.2：增加二次排序

- 新增 `ranker.py`
- 不再只根据中心点距离推荐
- 综合考虑平均通勤时间、最长单人通勤时间、公平性差值、距离中心点远近和 POI 评分
- 推荐结果更偏向“多人协商公平性”

### v0.3：封装 Skill 与 FastAPI 接口

- 新增 `Gathere Skill` 封装
- 将地点检索、路线规划、二次排序流程整理为可复用能力
- 新增 FastAPI 本地接口 `/recommend`
- 支持通过 HTTP 请求传入多人位置、目标类型和推荐参数
- 推荐结果以结构化 JSON 返回，便于网页端、QQ Bot 或其他 Agent 调用
- 项目从本地脚本 Demo 进一步升级为可集成的后端服务模块

## 后续计划

- 接入 QQ Bot / AstrBot，实现群聊内直接推荐聚会地点
- 增加更多筛选条件，例如营业时间、人均价格、评分、是否有包间
- 支持用户对推荐结果继续追问和调整
 
- 支持更多城市和更多出行方式

## License

MIT
