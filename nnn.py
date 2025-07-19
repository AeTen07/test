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
if "uploaded_context" not in st.session_state:
    st.session_state.uploaded_context = ""
if "uploaded_file_content" not in st.session_state:
    st.session_state.uploaded_file_content = ""
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# ---------------- 🔐 API 金鑰與設定 ----------------
with st.sidebar:
    st.markdown("## 🔐 API 設定")
    st.session_state.remember_api = st.checkbox("記住 API 金鑰", value=st.session_state.remember_api)
    if not st.session_state.remember_api:
        st.session_state.api_key = ""

    if st.session_state.remember_api and st.session_state.api_key:
        api_key_input = st.session_state.api_key
    else:
        api_key_input = st.text_input("請輸入 Gemini API 金鑰", type="password")

# ---------------- 📜 對話紀錄顯示區 ----------------
chat_display = st.container()
with chat_display:
    for msg in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(msg["user"])
        with st.chat_message("ai"):
            st.markdown(msg["ai"])

    if st.session_state.chat_history:
        all_history = "\n\n".join([f"👤 {m['user']}\n🤖 {m['ai']}" for m in st.session_state.chat_history])
        st.download_button("💾 下載聊天紀錄", all_history, file_name="gemini_chat.txt")

# ---------------- 📥 最下方輸入與上傳區 ----------------
bottom_input = st.empty()
with bottom_input.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        prompt = st.chat_input("請輸入你的問題...")

    with col2:
        uploaded_file = st.file_uploader("📎 上傳輔助文字檔案", type=["txt", "csv", "md", "json"], label_visibility="collapsed", key="text_file")
        image_file = st.file_uploader("🖼️ 上傳圖片", type=["jpg", "jpeg", "png"], label_visibility="collapsed", key="image_file")

    # 儲存文字檔內容
    if uploaded_file:
        file_content = uploaded_file.read().decode("utf-8")
        st.session_state.uploaded_file_content = file_content
        st.info("✅ 文字檔已上傳，可用來輔助回答問題。")

    # 儲存圖片
    if image_file:
        image = Image.open(image_file)
        st.session_state.uploaded_image = image
        st.image(image, caption="已上傳的圖片", use_column_width=True)

# ---------------- 🤖 Gemini 回應邏輯 ----------------
if prompt:
    if not api_key_input:
        st.error("❌ 請輸入有效的 API 金鑰")
        st.stop()

    try:
        genai.configure(api_key=api_key_input)

        # 建立聊天模型（text-only）
        text_model = genai.GenerativeModel("gemini-1.5-flash")

        # 圖像模型
        vision_model = genai.GenerativeModel("gemini-pro-vision")

        # 初始化 chat
        if not st.session_state.chat:
            st.session_state.chat = text_model.start_chat(history=[])

        # 顯示提問
        with st.chat_message("user"):
            st.markdown(prompt)

        # 組合 prompt（加入文字檔）
        full_prompt = prompt
        if st.session_state.uploaded_file_content:
            full_prompt += "\n\n以下是輔助資料：\n" + st.session_state.uploaded_file_content

        # 回覆生成
        with st.chat_message("ai"):
            with st.spinner("🤖 Gemini 思考中..."):

                # 如果有圖片，呼叫 vision model
                if st.session_state.uploaded_image:
                    image_bytes = io.BytesIO()
                    st.session_state.uploaded_image.save(image_bytes, format='PNG')
                    image_bytes.seek(0)
                    response = vision_model.generate_content([full_prompt, image_bytes.getvalue()])
                else:
                    response = st.session_state.chat.send_message(full_prompt)

                ai_text = response.text
                st.markdown(ai_text)

                # 儲存對話
                st.session_state.chat_history.append({
                    "user": prompt,
                    "ai": ai_text
                })

        # 記住金鑰
        if st.session_state.remember_api:
            st.session_state.api_key = api_key_input
        else:
            st.session_state.api_key = ""

    except Exception as e:
        st.error(f"❌ 發生錯誤：{e}")
