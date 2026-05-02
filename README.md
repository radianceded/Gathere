# 📍 Gathere

**多人聚会地点协商助手** — 基于 LLM + 高德地图 API 的智能 Agent

## 解决什么问题

几个朋友想聚餐，每个人在城市不同位置。去哪吃？谁来的路最远？有没有一个“对大家都公平”的地方？

Gathere 帮你回答这些问题。告诉它每个人在哪，它会：

1. 在大家位置的“中间地带”搜索候选地点
2. 计算每个人到每个候选地点的通勤时间
3. 使用综合评分函数对候选地点排序
4. 推荐更公平、更合适的 Top 3 方案
5. 支持追加约束（“要有包间”、“想吃火锅”、“人均100以内”）

相比单纯按距离中心点推荐，Gathere 会综合考虑：

- 平均通勤时间
- 最长单人通勤时间
- 通勤公平性差值
- 距离中心点远近
- POI 评分

## 技术架构

```text
用户 ⟷ Streamlit (聊天界面)
              │
        Agent 核心 (LLM, tool use)
              │
     ┌────────┼──────────┬──────────┬──────────┐
  地理编码     POI搜索     路线规划    中心点计算
  (高德API)   (高德API)   (高德API)   (本地计算)
              │
        综合评分排序
        (ranker.py)
```

## 快速开始

### 1. 准备 API Key

- **LLM API Key**：任意 OpenAI 兼容服务（DeepSeek / 通义千问 / 智谱 / Moonshot 等）
- **高德地图 Key**：[高德开放平台](https://console.amap.com/dev/key/app)（选择 Web 服务）

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

`.env` 示例：

```env
LLM_API_KEY=your_llm_api_key_here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

AMAP_API_KEY=your_amap_api_key_here
```

### 4. 启动

Streamlit 界面（推荐）：

```bash
streamlit run app.py
```

命令行模式：

```bash
python agent.py
```

## 使用示例

```text
你: 我们四个人周六想聚餐。我在苏大本部，小王在园区湖东邻里中心，
    小李在新区狮山路，小张在吴中区宝带西路。想吃火锅。

Gathere: [自动执行]
  1. 将 4 个地名转为坐标
  2. 计算地理中心点
  3. 在中心点附近搜索火锅店
  4. 计算每人到每家店的公交耗时
  5. 使用 ranker.py 综合评分排序
  6. 推荐 Top 3 方案，附带每人通勤数据
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

## License

MIT