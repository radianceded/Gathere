# Gathere AstrBot 插件

这个插件用于将 Gathere 接入 AstrBot，通过 `/gathere` 命令调用本地 Gathere FastAPI，为群聊或私聊用户推荐相对公平的聚会地点。

当前插件会按规则解析命令文本，向 Gathere `/recommend` 接口发送结构化 JSON，并读取返回结果中的 `places` 字段，格式化输出 Top 3 推荐地点。

## 使用前提

先启动 Gathere FastAPI：

```powershell
cd D:\document\grade22\Gathere\files
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

接口地址：

```text
http://127.0.0.1:8000/recommend
```

## 安装位置

将本目录复制到 AstrBot 的插件目录，例如：

```text
astrbot-gathere/data/plugins/astrbot_plugin_gathere
```

复制后，在 AstrBot WebUI 中重载插件。

## 命令格式

```text
/gathere 人名@位置；人名@位置 | 关键词 | 城市
```

示例：

```text
/gathere 我@苏州大学天赐庄校区；小王@园区湖东邻里中心；小李@新区狮山路 | 火锅 | 苏州
```

插件会解析为：

```json
{
  "participants": [
    {
      "name": "我",
      "address": "苏州大学天赐庄校区"
    },
    {
      "name": "小王",
      "address": "园区湖东邻里中心"
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
  "strategy": "balanced"
}
```

## 当前版本说明

当前 v0.4 是命令式插件调用，不是 LLM Tool Calling。

插件通过规则解析命令，调用 Gathere FastAPI。后续可升级为自然语言 Agent，由 LLM 抽取参数并调用同一个 `/recommend` 接口。
