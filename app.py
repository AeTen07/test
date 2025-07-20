import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# 載入 .env 檔案
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# 設定 Gemini API 金鑰
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

# 設定網頁標題與icon
st.set_page_config(page_title="Gemini 聊天室", page_icon="🤖")
st.title("🤖 Gemini AI 聊天室")
st.markdown("## 💬 Gemini AI 對話區")

# 插入自定 CSS：固定輸入欄在底部
st.markdown("""
<style>
div[data-testid="stChatInput"] {
    position: fixed;
    bottom: 20px;
    width: 85%;
    z-index: 100;
    background-color: white;
    padding-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# 建立聊天歷史紀錄
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 顯示歷史訊息
for msg in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(msg["user"])
        if msg.get("image"):
            st.image(msg["image"], caption="你上傳的圖片", use_column_width=True)
    with st.chat_message("ai"):
        st.markdown(msg["ai"])

# 使用者輸入
prompt = st.chat_input("請輸入你的問題...")

# 檔案上傳放在最底部區塊
with st.container():
    uploaded_image = st.file_uploader("🖼️ 上傳圖片", type=["png", "jpg", "jpeg", "webp"], label_visibility="visible")

# 判斷是否送出訊息或圖片
if prompt or uploaded_image:
    # 儲存使用者訊息
    user_msg = {"user": prompt, "image": None}
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_image:
            image = Image.open(uploaded_image)
            st.image(image, caption="你上傳的圖片", use_column_width=True)
            user_msg["image"] = image

    # Gemini 回覆
    with st.chat_message("ai"):
        with st.spinner("Gemini 思考中..."):
            if uploaded_image:
                img_data = genai.upload_file(uploaded_image.name, uploaded_image.read())
                response = model.generate_content([prompt, img_data])
            else:
                response = model.generate_content(prompt)
        st.markdown(response.text)

    # 儲存對話紀錄
    ai_msg = {"user": prompt, "image": user_msg["image"], "ai": response.text}
    st.session_state.chat_history.append(ai_msg)
