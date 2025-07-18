import streamlit as st
import google.generativeai as genai

# 頁面設定
st.set_page_config(page_title="Gemini 聊天室", layout="wide")

# 💡 插入固定標題的 CSS
st.markdown("""
    <style>
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #0e1117;
        padding: 10px 20px;
        z-index: 100;
        border-bottom: 1px solid #444;
    }
    .content {
        padding-top: 100px;
    }
    </style>
    <div class="fixed-header">
        <h1 style="margin-bottom:0">🤖 Gemini AI 聊天室</h1>
        <h3 style="margin-top:0">💬 Gemini AI 對話區</h3>
    </div>
""", unsafe_allow_html=True)

# 🧱 初始化狀態
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "remember_api" not in st.session_state:
    st.session_state.remember_api = False
if "chat" not in st.session_state:
    st.session_state.chat = None  # Gemini 的 chat 物件

# 🧾 API 金鑰輸入區（側邊欄）
with st.sidebar:
    st.markdown("## 🔐 API 設定")
    remember_api_checkbox = st.checkbox("記住 API 金鑰", value=st.session_state.remember_api)

    # 勾選狀態更新 & 金鑰清除
    if not remember_api_checkbox and st.session_state.remember_api:
        st.session_state.api_key = ""
    st.session_state.remember_api = remember_api_checkbox

    # 顯示或輸入金鑰
    if st.session_state.remember_api and st.session_state.api_key:
        api_key_input = st.session_state.api_key
    else:
        api_key_input = st.text_input("請輸入 Gemini API 金鑰", type="password")

# 💬 對話顯示區（主內容區塊）
with st.container():
    st.markdown('<div class="content">', unsafe_allow_html=True)

    for msg in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(msg["user"])
        with st.chat_message("ai"):
            st.markdown(msg["ai"])

    if st.session_state.chat_history:
        all_history = "\n\n".join([f"👤 {m['user']}\n🤖 {m['ai']}" for m in st.session_state.chat_history])
        st.download_button("💾 下載聊天紀錄", all_history, file_name="gemini_chat.txt")

    prompt = st.chat_input("請輸入你的問題...")

    if prompt:
        if not api_key_input:
            st.error("❌ 請輸入有效的 API 金鑰")
            st.stop()

        try:
            genai.configure(api_key=api_key_input)
            model = genai.GenerativeModel("gemini-1.5-flash")

            if not st.session_state.chat:
                st.session_state.chat = model.start_chat(history=[])

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("ai"):
                with st.spinner("🤖 Gemini 思考中..."):
                    response = st.session_state.chat.send_message(prompt)
                    ai_text = response.text
                    st.markdown(ai_text)

                    st.session_state.chat_history.append({
                        "user": prompt,
                        "ai": ai_text
                    })

            if st.session_state.remember_api:
                st.session_state.api_key = api_key_input
            else:
                st.session_state.api_key = ""

        except Exception as e:
            st.error(f"❌ 錯誤：{e}")

    st.markdown('</div>', unsafe_allow_html=True)  # 關閉 content 區塊
