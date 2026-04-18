# 📍 Gathere

**多人聚会地点协商助手** — 基于 Claude API + 高德地图 API 的智能 Agent

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
        Agent 核心 (Claude API, tool use)
              │
     ┌────────┼──────────┬──────────┐
  地理编码     POI搜索     路线规划    中心点计算
  (高德API)   (高德API)   (高德API)   (本地计算)
```

**核心设计**: 单 Agent + 4 个 Tool，Claude 通过 tool_use 自主决定调用顺序和参数。

## 快速开始

### 1. 准备 API Key
- **Claude API Key**: [Anthropic Console](https://console.anthropic.com/)
- **高德地图 Key**: [高德开放平台](https://console.amap.com/dev/key/app)（选择 Web服务）

### 2. 安装运行

```bash
git clone https://github.com/YOUR_USERNAME/gathere.git
cd gathere
pip install -r requirements.txt
```

编辑 `config.py`，填入你的 API Key：

```python
AMAP_API_KEY = "你的高德Key"
ANTHROPIC_API_KEY = "你的Claude Key"
```

### 3. 启动

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
gathere/
├── config.py          # API Key 配置
├── tools.py           # 高德地图 API 工具（4个 tool）
├── agent.py           # Claude Agent 核心（tool-calling 循环）
├── app.py             # Streamlit UI
├── requirements.txt   # Python 依赖
└── README.md
```

## License

MIT
