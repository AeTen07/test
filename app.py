import streamlit as st
import pandas as pd
import google.generativeai as genai

# 設定 Gemini API 金鑰（建議用 dotenv 隱藏）
api_key = "AIzaSyCWLb6_xQ57OsIOFFN5MfJtybzNV2vjxsw"
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# 初始化對話記錄
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.set_page_config(page_title="CSV + Gemini AI", layout="wide")
st.title("📊 資料集上傳 + 🤖 Gemini AI 聊天室")

# 側邊欄：記憶留存區
with st.sidebar:
    st.header("🧠 記憶留存區")
    if st.session_state.chat_history:
        for i, chat in enumerate(st.session_state.chat_history):
            st.markdown(f"**你：** {chat['user']}")
            st.markdown(f"**AI：** {chat['ai']}")
            st.markdown("---")
    else:
        st.info("目前尚無對話紀錄。")

# CSV 上傳
st.subheader("上傳你的 CSV 檔案")
uploaded_file = st.file_uploader("請選擇一個 CSV 檔案", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("✅ 成功上傳！")
    st.dataframe(df)


# 💬 聊天介面
st.subheader("💬 Gemini AI 對話區")

# 顯示對話氣泡
for msg in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(msg["user"])
    with st.chat_message("ai"):
        st.markdown(msg["ai"])

# 輸入新問題
if prompt := st.chat_input("輸入你的問題..."):
    # 顯示自己的訊息
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gemini 回應
    with st.chat_message("ai"):
        with st.spinner("思考中..."):
            try:
                response = model.generate_content(prompt)
                ai_text = response.text
                st.markdown(ai_text)

                # 儲存對話紀錄
                st.session_state.chat_history.append({
                    "user": prompt,
                    "ai": ai_text
                })

            except Exception as e:
                st.error(f"發生錯誤：{e}")
