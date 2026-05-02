"""
Gathere - Streamlit UI
多人聚会地点协商助手的对话界面
"""

import streamlit as st
from agent import chat

# 页面配置
st.set_page_config(
    page_title="Gathere - 聚会地点助手",
    page_icon="📍",
    layout="centered",
)

# 标题
<<<<<<< HEAD
st.title("📍 Gathere")
=======
st.title("📍 Gathere 📍")
>>>>>>> 784ba4a (feat: add ranker for fair place recommendation)
st.caption("多人聚会地点协商助手 — 告诉我每个人在哪，我帮你找最佳聚会地点")

# 初始化 session state
if "messages" not in st.session_state:
    st.session_state.messages = []  # UI 显示用
if "history" not in st.session_state:
    st.session_state.history = []   # Agent 对话历史

# 显示已有消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 用户输入
if prompt := st.chat_input("比如：我们三个人想聚餐，我在苏大本部，小王在园区湖东，小李在新区狮山..."):
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 调用 Agent
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                response_text, updated_history = chat(
                    prompt,
                    st.session_state.history if st.session_state.history else None,
                )
                st.session_state.history = updated_history
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                error_msg = f"出错了: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# 侧边栏
with st.sidebar:
    st.markdown("### 使用说明")
    st.markdown("""
    1. 告诉我有几个人参加聚会
    2. 说出每个人的出发位置
    3. 我会推荐最佳聚会地点
    
    **支持追加条件：**
    - "要有包间"
    - "想吃火锅"  
    - "人均别超过100"
    - "改成KTV"
    """)
    
    st.markdown("---")
    
    if st.button("🗑️ 清空对话"):
        st.session_state.messages = []
        st.session_state.history = []
        st.rerun()
    
    st.markdown("---")
<<<<<<< HEAD
    st.caption("Gathere v0.1 | Claude + 高德地图API")
=======
    st.caption("Gathere v0.2 | LLM + 高德地图API")
>>>>>>> 784ba4a (feat: add ranker for fair place recommendation)
