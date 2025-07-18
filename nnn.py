import streamlit as st
import google.generativeai as genai

# 頁面設定
with st.container():
    st.markdown("## 🤖 Gemini AI 聊天室")


# 初始化狀態
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "remember_api" not in st.session_state:
    st.session_state.remember_api = False
if "chat" not in st.session_state:
    st.session_state.chat = None  # Gemini 的 chat 物件

# ---------------- 🔐 API 金鑰輸入區 ----------------
with st.sidebar:
    st.markdown("## 🔐 API 設定")

    remember_api_checkbox = st.checkbox("記住 API 金鑰", value=st.session_state.remember_api)

    # 檢查是否從勾選變為取消，若是則清空 API 金鑰
    if not remember_api_checkbox and st.session_state.remember_api:
        st.session_state.api_key = ""

    # 更新勾選狀態
    st.session_state.remember_api = remember_api_checkbox

    # 根據勾選狀態與 API 金鑰顯示或輸入
    if st.session_state.remember_api and st.session_state.api_key:
        api_key_input = st.session_state.api_key
    else:
        api_key_input = st.text_input("請輸入 Gemini API 金鑰", type="password")

# ---------------- 💬 對話顯示區 ----------------
st.subheader("💬 Gemini AI 對話區")

# 顯示歷史對話泡泡
for msg in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(msg["user"])
    with st.chat_message("ai"):
        st.markdown(msg["ai"])

# 💾 下載對話紀錄
if st.session_state.chat_history:
    all_history = "\n\n".join([f"👤 {m['user']}\n🤖 {m['ai']}" for m in st.session_state.chat_history])
    st.download_button("💾 下載聊天紀錄", all_history, file_name="gemini_chat.txt")

# ---------------- 💬 使用 chat 模式持續對話 ----------------
# 下方輸入框（固定）
prompt = st.chat_input("請輸入你的問題...")

if prompt:
    if not api_key_input:
        st.error("❌ 請輸入有效的 API 金鑰")
        st.stop()

    try:
        # 設定 API
        genai.configure(api_key=api_key_input)

        # 建立 model 與對話物件
        model = genai.GenerativeModel("gemini-1.5-flash")

        if not st.session_state.chat:
            st.session_state.chat = model.start_chat(history=[])

        # 顯示提問
        with st.chat_message("user"):
            st.markdown(prompt)

        # Gemini 回應
        with st.chat_message("ai"):
            with st.spinner("🤖 Gemini 思考中..."):
                response = st.session_state.chat.send_message(prompt)
                ai_text = response.text
                st.markdown(ai_text)

                # 儲存對話
                st.session_state.chat_history.append({
                    "user": prompt,
                    "ai": ai_text
                })

        # 記住 API 金鑰
        if st.session_state.remember_api:
            st.session_state.api_key = api_key_input
        else:
            st.session_state.api_key = ""

    except Exception as e:
        st.error(f"❌ 錯誤：{e}")
