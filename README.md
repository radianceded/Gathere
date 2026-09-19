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

项目目前支持五种使用方式：

1. **Streamlit 聊天界面**：适合直接交互和演示
2. **Gathere Skill**：适合被其他 Agent 或业务逻辑复用
3. **FastAPI 接口**：适合作为后端服务，被网页端、QQ Bot、插件或其他系统调用
4. **AstrBot 插件**：适合在 AstrBot Chat 中通过 `/gathere` 命令调用推荐服务
5. **MCP Server**：让 ZCode、Claude Desktop、Cursor 等任何支持 MCP 的客户端直接调用推荐能力

## 技术架构

```text
用户 / MCP 客户端
 │
 ├── Streamlit 聊天界面
 │
 ├── Gathere Skill
 │
 ├── MCP Server (stdio)
 │
 └── FastAPI /recommend 接口
              │
              ▼
        Agent 核心
        (LLM, tool use)
              │
     ┌────────┼──────────┬──────────┬──────────┐
     ▼        ▼          ▼          ▼          ▼
  地理编码   POI 搜索   路线规划   中心点计算  归一化排序
 (高德API)  (高德API)  (高德API)  (本地计算)  (ranker.py)
              │
              ▼
        Top 3 推荐结果
```

## 核心模块

```text
Gathere/
├── app.py                  # Streamlit 聊天界面
├── agent.py                # Agent 主逻辑
├── ranker.py               # 归一化公平性评分
├── viz.py                  # 推荐结果地图数据构建
├── mcp_server.py           # MCP Server 入口
├── skills/                 # Gathere Skill 封装
├── integrations/           # 外部系统接入示例
│   └── astrbot_plugin_gathere/
├── api.py                  # FastAPI 服务入口
├── tests/                  # 离线 pytest 测试套件
├── requirements.txt        # 项目依赖
├── .env.example            # 环境变量示例
└── README.md
```

其中：

- `agent.py` 负责理解用户输入，并调用地图相关工具
- `ranker.py` 负责对候选地点进行综合排序
- `skills/` 将推荐能力封装为可复用 Skill
- `integrations/astrbot_plugin_gathere/` 提供 AstrBot 插件接入源码
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

# 可选：设置后 FastAPI /recommend 要求请求头 X-API-Key，留空则不鉴权
GATHERE_API_KEY=
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
    participants=[
        {"name": "我", "address": "苏大本部"},
        {"name": "小王", "address": "园区湖东邻里中心"},
        {"name": "小李", "address": "新区狮山路"},
        {"name": "小张", "address": "吴中区宝带西路"},
    ],
    keywords="火锅",
    city="苏州",
    mode="transit",
    top_k=3,
    strategy="balanced",
)

print(result)
```

返回结果通常包含：

```python
{
    "participants": [
        {
            "name": "我",
            "address": "苏大本部",
            "location": "120.63,31.30"
        }
    ],
    "center": {
        "lng": 120.62,
        "lat": 31.30
    },
    "center_location": "120.62,31.30",
    "candidate_count": 20,
    "places": [
        {
            "name": "示例火锅店",
            "address": "苏州市某某路",
            "location": "120.61,31.29",
            "rating": "4.7",
            "score": 0.31,
            "total_duration_min": 95,
            "max_duration_min": 42,
            "fairness_gap_min": 18,
            "center_distance_m": 820,
            "routes": [
                {
                    "participant": "我",
                    "duration_min": 25,
                    "distance_km": 6.2
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
  "participants": [
    {
      "name": "我",
      "address": "苏州大学天赐庄校区"
    },
    {
      "name": "小王",
      "address": "园区湖东邻里中心",
      "mode": "driving"
    },
    {
      "name": "小李",
      "address": "新区狮山路"
    }
  ],
  "keywords": "火锅",
  "city": "苏州",
  "mode": "transit",
  "top_k": 3,
  "strategy": "balanced",
  "max_cost": 100
}
```

字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `participants` | list | 参与聚会的人，每个人包含姓名和地址 |
| `name` | string | 参与者姓名 |
| `address` | string | 参与者所在位置，可以是地名、商圈或详细地址 |
| `mode` | string | 可选，该参与者自己的出行方式 `driving`/`walking`/`transit`，不填则用全局 `mode` |
| `keywords` | string | 搜索关键词，例如火锅、咖啡、餐厅 |
| `city` | string | 搜索城市 |
| `mode` | string | 全局默认出行方式，例如 `transit` |
| `top_k` | int | 返回推荐数量 |
| `strategy` | string | 排序策略 `balanced`/`fair`/`fast` |
| `max_cost` | number | 可选，人均消费预算上限（元），高德有人均数据的候选会被过滤 |

如果 `.env` 里设置了 `GATHERE_API_KEY`，请求必须携带请求头 `X-API-Key: <key>`，否则返回 401。

返回结果重点字段：

| 字段 | 说明 |
| --- | --- |
| `participants` | 参与者地理编码结果 |
| `center` / `center_location` | 多人中心点 |
| `candidate_count` | 候选地点数量 |
| `places` | 最终推荐地点列表 |

`places` 中每个地点通常包含 `name`、`address`、`location`、`rating`、`routes`、`score`、`total_duration_min`、`max_duration_min`、`fairness_gap_min`、`center_distance_m`。

### 3. 使用 curl 调用

```bash
curl -X POST "http://127.0.0.1:8000/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "participants": [
      {"name": "我", "address": "苏州大学天赐庄校区"},
      {"name": "小王", "address": "园区湖东邻里中心"},
      {"name": "小李", "address": "新区狮山路"}
    ],
    "keywords": "火锅",
    "city": "苏州",
    "mode": "transit",
    "top_k": 3,
    "strategy": "balanced"
  }'
```

### 4. 使用 Python requests 调用

```python
import requests

url = "http://127.0.0.1:8000/recommend"

payload = {
    "participants": [
        {"name": "我", "address": "苏州大学天赐庄校区"},
        {"name": "小王", "address": "园区湖东邻里中心"},
        {"name": "小李", "address": "新区狮山路"},
    ],
    "keywords": "火锅",
    "city": "苏州",
    "mode": "transit",
    "top_k": 3,
    "strategy": "balanced",
}

response = requests.post(url, json=payload)
print(response.json())
```

### 5. 返回结果示例

```json
{
  "keywords": "火锅",
  "city": "苏州",
  "participants": [
    {
      "name": "我",
      "address": "苏州大学天赐庄校区",
      "location": "120.64,31.31"
    }
  ],
  "center": {
    "lng": 120.62,
    "lat": 31.30
  },
  "center_location": "120.62,31.30",
  "candidate_count": 20,
  "places": [
    {
      "rank": 1,
      "name": "示例火锅店",
      "address": "苏州市某某路",
      "location": "120.61,31.29",
      "rating": "4.7",
      "score": 0.31,
      "total_duration_min": 97,
      "max_duration_min": 42,
      "fairness_gap_min": 18,
      "center_distance_m": 820,
      "routes": [
        {
          "participant": "我",
          "duration_min": 25,
          "distance_km": 6.2
        },
        {
          "participant": "小王",
          "duration_min": 30,
          "distance_km": 8.1
        },
        {
          "participant": "小李",
          "duration_min": 42,
          "distance_km": 12.0
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

## AstrBot 插件接入

插件源码位置：

```text
integrations/astrbot_plugin_gathere
```

先启动 Gathere FastAPI：

```bash
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

将插件复制到 AstrBot 插件目录：

```text
astrbot-gathere/data/plugins/astrbot_plugin_gathere
```

然后在 AstrBot WebUI 中重载插件。

当前版本是命令式 AstrBot 插件调用，不是 LLM Tool Calling。后续可升级为自然语言 Agent，由 LLM 抽取 `participants`、`keywords`、`city` 等参数，再调用同一个 `/recommend` 接口。

第四段支持可选附加参数：出行方式（`公交`/`驾车`/`步行`）或人均预算（`人均100`）。

测试命令：

```text
/gathere 我@苏州大学天赐庄校区；小王@园区湖东邻里中心；小李@新区狮山路 | 火锅 | 苏州
/gathere 我@苏州大学天赐庄校区；小王@园区湖东邻里中心 | 火锅 | 苏州 | 驾车
/gathere 我@苏州大学天赐庄校区；小王@园区湖东邻里中心 | 火锅 | 苏州 | 人均100
```

## 使用方式五：MCP Server 接入

Gathere 可以作为 MCP（Model Context Protocol）Server 运行，任何支持 MCP 的客户端（ZCode、Claude Desktop、Cursor 等）都能直接调用聚会地点推荐能力，不需要自建 FastAPI 服务。

高德官方自己也提供 MCP Server（原子级地图工具：单次搜索、单次算路等）。Gathere MCP 是在地图数据能力之上的垂直封装：一个工具完成"多人选址"，内部自动处理地理编码、几何中位数中心点、多中心候选搜索、路线规划和归一化公平性排序。

### 1. 在 MCP 客户端中配置

stdio 方式（推荐，客户端自动拉起进程）：

```json
{
  "mcpServers": {
    "gathere": {
      "command": "python",
      "args": ["/你的路径/Gathere/mcp_server.py"]
    }
  }
}
```

`AMAP_API_KEY` 会从 Gathere 目录下的 `.env` 自动读取；如果客户端工作目录不同，也可以直接在配置的 `env` 字段里给出：

```json
{
  "mcpServers": {
    "gathere": {
      "command": "python",
      "args": ["/你的路径/Gathere/mcp_server.py"],
      "env": { "AMAP_API_KEY": "your_amap_api_key_here" }
    }
  }
}
```

### 2. 提供的工具

| 工具 | 说明 |
| --- | --- |
| `recommend_meeting_places` | 核心工具：输入参与者列表（每人 `name`/`address`，可选自己的 `mode` 出行方式），支持 `keywords`、`city`、`max_cost` 人均预算、`strategy` 排序策略，返回 Top_k 推荐与每人通勤明细 |
| `geocode_address` | 地址/地名 → 高德经纬度坐标 |
| `plan_route` | 两点路线耗时与距离，起终点支持坐标或地名（地名自动地理编码） |

### 3. 调用示例

在支持 MCP 的客户端对话里直接说：

```text
帮我找个人人通勤都合理的火锅店：我在苏州大学天赐庄校区，
小王在园区湖东邻里中心（他开车），小李在新区狮山路，人均100以内。
```

客户端会自动调用 `recommend_meeting_places` 并汇总结果。

## 推荐排序逻辑

Gathere 的排序不是只看中心点距离，而是通过 `ranker.py` 对候选 POI 进行二次评分。

为了让通勤时间（几百分钟量级）和 POI 评分（0~5 分量级）这类量纲不同的指标可以直接比较，所有指标会先在当前候选集内做 min-max 归一化，再加权求和。以 balanced 策略为例：

```text
综合得分（越低越好）=
  0.40 × 总通勤时间（归一化）
+ 0.25 × 最长单人通勤时间（归一化）
+ 0.20 × 公平性差值（归一化）
+ 0.10 × 距中心点距离（归一化）
- 0.05 × POI 评分（归一化）
+ 数据缺失惩罚（0.10 × 路线缺失比例）
```

fair 策略提高公平性权重（0.30/0.30），fast 策略提高总时间权重（0.55）。排序结果会附带 `score_breakdown` 字段，展示每个候选地点在各项指标上的得分构成。

几个要点：

- **归一化**：每个指标在候选集内归一化到 0~1，避免"总通勤几百分钟"完全碾压"评分只有 0~5 分"的问题，POI 评分真正参与排序
- **无评分不等于差评**：高德返回空评分的 POI 按中性值处理，不会被当成 0 分垫底
- **数据缺失惩罚**：有参与者路线规划失败的候选按缺失比例扣分，避免"只算出两个人路线"的候选占便宜（路线规划至少要成功一半，否则候选被丢弃）

## 中心点与候选搜索逻辑

- **几何中位数中心点**：中心点使用 Weiszfeld 迭代计算几何中位数而不是算术平均。某个参与者位置特别偏远时，中心点不会被明显带偏。
- **多中心候选搜索**：候选地点除了在中心点附近搜索，还会在（最多 4 个）参与者位置附近搜索后合并去重。这样即使中心点落在湖泊、山区等空旷区域（比如独墅湖、金鸡湖），也依然能找到候选。
- **粗筛后再规划路线**：候选过多时先按直线通勤总距离粗筛，只对最有希望的前 10 个候选调用真实的路线规划接口，显著节省高德 API 配额。`filtered_count` 字段记录被粗筛掉的数量。

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
- 支持通过 HTTP 请求传入 `participants`、`keywords`、`city`、`mode`、`top_k`、`strategy` 等推荐参数
- 推荐结果以结构化 JSON 返回，便于网页端、QQ Bot 或其他 Agent 调用
- 项目从本地脚本 Demo 进一步升级为可集成的后端服务模块

### v1.0：接入 AstrBot 插件

- 新增 AstrBot 插件 `astrbot_plugin_gathere`
- 支持在 AstrBot Chat 中通过 `/gathere` 命令调用 Gathere 推荐服务
- 插件将聊天命令解析为 `/recommend` 接口所需的结构化 JSON
- Gathere FastAPI 接收请求后，完成地理编码、中心点计算、POI 搜索、路线规划与 `ranker.py` 综合排序
- 插件读取后端返回的 `places` 字段，并格式化输出 Top 3 推荐结果
- 当前版本为命令式插件调用，后续可升级为 LLM Tool Calling，由 LLM 抽取 `participants`、`keywords`、`city` 等参数后调用同一个 `/recommend` 接口

### v1.1：推荐算法优化

- **评分归一化**：总通勤、最长通勤、公平性差值、中心距离、POI 评分先在候选集内 min-max 归一化再加权，评分项从"形同虚设"变为真正参与排序；`score` 变为 0~1 量纲（越低越好），并新增 `score_breakdown` 得分构成字段
- **无评分中性处理**：高德返回空评分的 POI 不再被当作 0 分垫底
- **几何中位数中心点**：`compute_centroid` 改用 Weiszfeld 迭代，抗单点离群
- **多中心候选搜索**：在中心点和各参与者位置附近分别搜索后合并去重，中心点落在湖泊等空旷区域时依然能出结果；候选不足时自动扩大半径重试
- **路线粗筛**：候选过多时按直线通勤总距离预筛，只对前 10 个候选做真实路线规划，节省 API 配额
- **路线容错**：单个参与者路线规划失败不再丢弃整个候选，改为按数据缺失比例扣分（至少一半参与者成功才保留）
- 新增 pytest 离线测试套件（`tests/`，16 个用例，不依赖 API Key）

### v1.2：产品功能完善

- **人均预算过滤**：`/recommend` 新增 `max_cost` 参数，使用高德 POI 的人均消费数据（`business.cost`）过滤超预算候选；没有人均数据的候选保留不计罚。Streamlit 对话中"人均100以内"由 LLM 自动转为该参数
- **每参与者独立出行方式**：`participants` 中每个人可带自己的 `mode`（如有人开车、其他人坐地铁），路线规划按人分别执行，返回的 `routes` 中包含每人的出行方式
- **API 鉴权**：`.env` 设置 `GATHERE_API_KEY` 后，`/recommend` 要求请求头 `X-API-Key`，公网部署不再裸奔
- **地图可视化**：Streamlit 界面在推荐后展示位置示意图（参与者/中心点/推荐地点），数据来自 Agent 历史中最近一次推荐结果（`viz.py`）
- **AstrBot 插件增强**：命令新增第四段可选参数，支持指定出行方式或人均预算，通勤明细展示每人出行方式
- 修复 `requirements.txt` 缺少 `fastapi`/`uvicorn`/`httpx` 导致按文档安装后无法启动 FastAPI 的问题；`DEFAULT_CITY` 接入所有默认参数
- 测试套件扩充至 33 个用例，新增 FastAPI 参数透传与鉴权、预算过滤、混合出行方式、地图数据构建的测试

### v1.3：MCP Server 接入

- 新增 `mcp_server.py`，基于 MCP 官方 Python SDK 将 Gathere 封装为 MCP Server，stdio 传输
- 暴露三个业务粒度工具：`recommend_meeting_places`（多人聚会选址）、`geocode_address`（地理编码）、`plan_route`（路线规划，地名自动解析为坐标）
- ZCode、Claude Desktop、Cursor 等 MCP 客户端即插即用，无需自建服务；`AMAP_API_KEY` 从 `.env` 或客户端配置的 `env` 读取，不内置任何 Key
- 测试覆盖 stdio 协议握手、工具列表、参数透传，以及（配置真实 Key 时）端到端地理编码调用，套件共 39 个用例



## License

MIT
