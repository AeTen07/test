import streamlit as st
import google.generativeai as genai
import pandas as pd

# 頁面設定
st.set_page_config(page_title="Gemini 聊天室", layout="wide")
st.title("🤖 Gemini AI 聊天室")
st.subheader("💬 Gemini AI 對話區")

# 初始化狀態
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "remember_api" not in st.session_state:
    st.session_state.remember_api = False
if "chat" not in st.session_state:
    st.session_state.chat = None
if "uploaded_context" not in st.session_state:
    st.session_state.uploaded_context = ""

# ---------------- 🔐 API 金鑰與檔案上傳 ----------------
with st.sidebar:
    st.markdown("## 🔐 API 設定")
    remember_api_checkbox = st.checkbox("記住 API 金鑰", value=st.session_state.remember_api)

    if not remember_api_checkbox and st.session_state.remember_api:
        st.session_state.api_key = ""
    st.session_state.remember_api = remember_api_checkbox

    if st.session_state.remember_api and st.session_state.api_key:
        api_key_input = st.session_state.api_key
    else:
        api_key_input = st.text_input("請輸入 Gemini API 金鑰", type="password")

    # 📂 檔案上傳區
    st.markdown("---")
    st.markdown("## 📂 上傳檔案供 Gemini 分析")
    uploaded_file = st.file_uploader("請上傳 `.txt`, `.csv`, 或 `.md` 檔", type=["txt", "csv", "md"])

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            st.session_state.uploaded_context = df.to_csv(index=False)
        else:
            st.session_state.uploaded_context = uploaded_file.read().decode("utf-8")
        st.success("✅ 檔案已上傳並讀取完成！")

# ---------------- 💬 對話歷史區 ----------------
for msg in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(msg["user"])
    with st.chat_message("ai"):
        st.markdown(msg["ai"])

if st.session_state.chat_history:
    all_history = "\n\n".join([f"👤 {m['user']}\n🤖 {m['ai']}" for m in st.session_state.chat_history])
    st.download_button("💾 下載聊天紀錄", all_history, file_name="gemini_chat.txt")

# ---------------- 💬 Gemini 聊天模式 ----------------
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

        # 顯示提問
        with st.chat_message("user"):
            st.markdown(prompt)

        # 補上檔案 context
        full_prompt = prompt
        if st.session_state.uploaded_context:
            full_prompt = f"根據以下檔案內容回答：\n\n{st.session_state.uploaded_context}\n\n問題：{prompt}"

        # 回覆
        with st.chat_message("ai"):
            with st.spinner("🤖 Gemini 思考中..."):
                response = st.session_state.chat.send_message(full_prompt)
                ai_text = response.text
                st.markdown(ai_text)

                # 儲存對話
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
