import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px

# 頁面設定
st.set_page_config(page_title="Gemini 聊天室", layout="wide")
st.title("🤖 Gemini AI 聊天室 ")

# 初始化狀態
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "remember_api" not in st.session_state:
    st.session_state.remember_api = False

# ---------------- Gemini AI 對話區 ----------------
st.subheader("💬 Gemini AI 對話區")

# 顯示聊天記錄
for msg in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(msg["user"])
    with st.chat_message("ai"):
        st.markdown(msg["ai"])

# 提問表單（可勾選是否記住 API）
with st.chat_message("user"):
    with st.form("chat_form", clear_on_submit=True):
        prompt = st.text_input("💬 請輸入你的問題")
        use_saved_key = st.checkbox("🔒 記住 API 金鑰", value=st.session_state.remember_api)
        if use_saved_key and st.session_state.api_key:
            api_key_input = st.session_state.api_key
        else:
            api_key_input = st.text_input("🔑 請輸入 Gemini API 金鑰", type="password")
        submitted = st.form_submit_button("送出")

# 當使用者按下送出
if submitted:
    if not api_key_input:
        st.error("❌ 請輸入有效的 API 金鑰")
        st.stop()

    if prompt.strip() == "":
        st.warning("⚠️ 請輸入問題")
        st.stop()

    try:
        # 配置模型
        genai.configure(api_key=api_key_input)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # ⏳ 加入最近 5 次對話作為上下文
        context_messages = []
        for msg in st.session_state.chat_history[-5:]:
            context_messages.append(f"使用者：{msg['user']}")
            context_messages.append(f"AI：{msg['ai']}")
        context_messages.append(f"使用者：{prompt}")
        full_prompt = "\n".join(context_messages)

        # 顯示使用者訊息
        with st.chat_message("user"):
            st.markdown(prompt)

        # 取得 Gemini 回覆
        with st.chat_message("ai"):
            with st.spinner("🤖 Gemini 思考中..."):
                response = model.generate_content(full_prompt)
                ai_text = response.text
                st.markdown(ai_text)

                # 儲存對話
                st.session_state.chat_history.append({
                    "user": prompt,
                    "ai": ai_text
                })

        # 是否記住金鑰
        st.session_state.remember_api = use_saved_key
        if use_saved_key:
            st.session_state.api_key = api_key_input
        else:
            st.session_state.api_key = ""

    except Exception as e:
        st.error(f"❌ API 金鑰無效或發生錯誤：{e}")
