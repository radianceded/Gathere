# 📍 Gathere

**多人聚会地点协商助手** — 基于 LLM + 高德地图 API 的智能 Agent

## 解决什么问题

几个朋友想聚餐，每个人在城市不同位置。去哪吃？谁来的路最远？有没有一个"对大家都公平"的地方？

Gathere 帮你回答这些问题。告诉它每个人在哪，它会：

1. 在大家位置的"中间地带"搜索候选地点
2. 计算每个人到每个候选地点的通勤时间
3. 推荐总通勤成本最低的方案
4. 支持追加约束（"要有包间"、"想吃火锅"、"人均100以内"）

## 技术架构

```
用户 ⟷ Streamlit (聊天界面)
              │
        Agent 核心 (LLM, tool use)
              │
     ┌────────┼──────────┬──────────┐
  地理编码     POI搜索     路线规划    中心点计算
  (高德API)   (高德API)   (高德API)   (本地计算)
```

**核心设计**：单 Agent + 4 个 Tool，LLM 通过 tool_use 自主决定调用顺序和参数。

支持任何 OpenAI 兼容的模型，默认使用 DeepSeek，也可切换为通义千问、智谱 GLM、Moonshot 等。

## 快速开始

### 1. 准备 API Key

- **LLM API Key**：任意 OpenAI 兼容服务（DeepSeek / 通义千问 / 智谱 / Moonshot 等）
- **高德地图 Key**：[高德开放平台](https://console.amap.com/dev/key/app)（选择 Web服务）

### 2. 安装依赖

```bash
git clone https://github.com/radianceded/Gathere.git
cd Gathere
pip install -r requirements.txt
```

### 3. 配置 API Key

复制 `.env.example` 为 `.env`，填入你的 Key：

```bash
cp .env.example .env
```

```
LLM_API_KEY=your_llm_api_key_here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
AMAP_API_KEY=your_amap_api_key_here
```

### 4. 启动

**Streamlit 界面（推荐）：**
```bash
streamlit run app.py
```

**命令行模式：**
```bash
python agent.py
```

## 使用示例

```
你: 我们四个人周六想聚餐。我在苏大本部，小王在园区湖东邻里中心，
    小李在新区狮山路，小张在吴中区宝带西路。想吃火锅。

Gathere: [自动执行]
  1. 将4个地名转为坐标
  2. 计算地理中心点
  3. 在中心点附近搜索火锅店
  4. 计算每人到每家店的公交耗时
  5. 推荐 Top 3 方案，附带每人通勤数据
```

## 项目结构

```
Gathere/
├── config.py          # 配置（从环境变量读取 API Key）
├── tools.py           # 高德地图 API 工具（4个 tool）
├── agent.py           # Agent 核心（tool-calling 循环）
├── app.py             # Streamlit UI
├── requirements.txt   # Python 依赖
├── .env.example       # 环境变量模板
└── README.md
```

## License

MIT
