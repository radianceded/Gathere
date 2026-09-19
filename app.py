"""
Gathere - Streamlit UI.
Chat interface for multi-person meeting-place recommendations.
"""

import pandas as pd
import streamlit as st

from agent import chat
from viz import build_map_points, extract_last_recommendation


st.set_page_config(
    page_title="Gathere - 聚会地点助手",
    page_icon="📍",
    layout="centered",
)

st.title("📍 Gathere 📍")
st.caption("多人聚会地点协商助手 - 告诉我每个人在哪，我帮你找最佳聚会地点")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("比如：我们三个人想聚餐，我在苏大本部，小王在园区湖东，小李在新区狮山..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                response_text, updated_history = chat(
                    prompt,
                    st.session_state.history if st.session_state.history else None,
                )
                st.session_state.history = updated_history
                st.session_state.last_result = extract_last_recommendation(updated_history)
                st.markdown(response_text)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                })
            except Exception as exc:
                error_msg = f"出错了: {str(exc)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })

if st.session_state.last_result:
    points = build_map_points(st.session_state.last_result)
    if points:
        st.subheader("🗺️ 位置示意图")
        st.map(pd.DataFrame(points))
        st.caption(
            "蓝色 = 参与者，橙色 = 中心点，红色 = 推荐地点。"
            "坐标为高德 GCJ-02，渲染可能有数百米偏移，仅供示意。"
        )

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
    - "小王开车来"
    - "改成KTV"
    """)

    st.markdown("---")

    if st.button("🗑️ 清空对话"):
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.last_result = None
        st.rerun()

    st.markdown("---")
    st.caption("Gathere v1.2 | LLM + 高德地图 API")
