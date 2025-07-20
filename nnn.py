import streamlit as st
import google.generativeai as genai
import pandas as pd
from PIL import Image
import io

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
if "uploaded_file_content" not in st.session_state:
    st.session_state.uploaded_file_content = ""
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# ---------------- 🔐 API 金鑰與檔案上傳（側邊欄） ----------------
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

# ---------------- 💾 聊天紀錄下載 ----------------
if st.session_state.chat_history:
    all_history = "\n\n".join([f"👤 {m['user']}\n🤖 {m['ai']}" for m in st.session_state.chat_history])
    st.download_button("💾 下載聊天紀錄", all_history, file_name="gemini_chat.txt")

# ---------------- 🧠 Gemini 聊天與圖片上傳功能 ----------------
# 最底層輸入欄位固定區塊
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        prompt = st.chat_input("請輸入你的問題...")
    with col2:
        uploaded_file = st.file_uploader("📎 上傳文字檔", type=["txt", "csv", "md", "json"], label_visibility="collapsed", key="file")
        uploaded_image = st.file_uploader("🖼️ 上傳圖片", type=["png", "jpg", "jpeg", "webp"], label_visibility="collapsed", key="image")

# ---------------- 💬 歷史對話區 ----------------
for msg in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(msg["user"])
        if msg.get("image"):
            st.image(msg["image"], caption="你上傳的圖片", use_column_width=True)
    with st.chat_message("ai"):
        st.markdown(msg["ai"])
# ---------------- 📎 檔案處理 ----------------
if uploaded_file:
    file_content = uploaded_file.read().decode("utf-8")
    st.session_state.uploaded_file_content = file_content
    st.info("✅ 文字檔案已上傳，可用來輔助回答問題。")

if uploaded_image:
    image_data = uploaded_image.read()
    st.session_state.uploaded_image = image_data
    st.info("✅ 圖片已上傳（目前不送入模型，只供參考顯示）。")

# ---------------- 🚀 Gemini 回應 ----------------
if prompt:
    if not api_key_input:
        st.error("❌ 請輸入有效的 API 金鑰")
        st.stop()

    try:
        genai.configure(api_key=api_key_input)
        model = genai.GenerativeModel("gemini-1.5-flash")

        if not st.session_state.chat:
            st.session_state.chat = model.start_chat(history=[])

        # 合成完整提示
        full_prompt = prompt
        if st.session_state.uploaded_file_content:
            full_prompt += "\n\n（附檔內容如下，請一併考慮）\n" + st.session_state.uploaded_file_content
        if st.session_state.uploaded_image:
            full_prompt += "\n\n（使用者同時上傳了一張圖片，僅供參考，尚未支援圖片分析）"

        with st.spinner("🤔 Gemini 思考中..."):
            response = st.session_state.chat.send_message(full_prompt)
            ai_text = response.text

        # 顯示提問與圖片
        with st.chat_message("user"):
            st.markdown(prompt)
            if st.session_state.uploaded_image:
                st.image(st.session_state.uploaded_image, caption="你上傳的圖片", use_column_width=True)

        # 顯示 AI 回覆
        with st.chat_message("ai"):
            st.markdown(ai_text)

        # 儲存對話紀錄
        st.session_state.chat_history.append({
            "user": prompt,
            "ai": ai_text,
            "image": st.session_state.uploaded_image
        })

        # 清空暫存
        st.session_state.uploaded_file_content = ""
        st.session_state.uploaded_image = None

        # 記住金鑰
        if st.session_state.remember_api:
            st.session_state.api_key = api_key_input
        else:
            st.session_state.api_key = ""

    except Exception as e:
        st.error(f"❌ 錯誤：{e}")
