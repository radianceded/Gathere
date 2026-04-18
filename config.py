"""
Gathere 配置文件
通过 .env 文件或环境变量配置 API Key（参考 .env.example）
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# LLM 配置（支持任何 OpenAI 兼容的 API）
# ============================================================

LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# API Base URL（不同提供商的地址不同）
# DeepSeek:      https://api.deepseek.com
# 通义千问:       https://dashscope.aliyuncs.com/compatible-mode/v1
# 智谱 GLM:      https://open.bigmodel.cn/api/paas/v4
# Moonshot:      https://api.moonshot.cn/v1
# OpenAI:        https://api.openai.com/v1
# 本地 Ollama:    http://localhost:11434/v1
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")

# 模型名称
# DeepSeek:      deepseek-chat
# 通义千问:       qwen-plus
# 智谱 GLM:      glm-4
# Moonshot:      moonshot-v1-8k
# OpenAI:        gpt-4o
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# ============================================================
# 高德地图配置
# ============================================================

# 高德地图 Web服务 API Key
# 申请地址: https://console.amap.com/dev/key/app
AMAP_API_KEY = os.getenv("AMAP_API_KEY", "")

# 默认城市
DEFAULT_CITY = "苏州"
