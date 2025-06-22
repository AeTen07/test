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
st.subheader("1️⃣ 上傳你的 CSV 檔案")
uploaded_file = st.file_uploader("請選擇一個 CSV 檔案", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("✅ 成功上傳！")
    st.dataframe(df)

# Gemini 聊天
st.subheader("2️⃣ 與 Gemini AI 聊聊")
prompt = st.text_input("請輸入問題")

if st.button("送出"):
    if prompt.strip() == "":
        st.warning("⚠️ 請輸入問題再送出。")
    else:
        try:
            with st.spinner("Gemini 思考中..."):
                response = model.generate_content(prompt)
                answer = response.text

                # 保存對話到記憶區
                st.session_state.chat_history.append({
                    "user": prompt,
                    "ai": answer
                })

                # 顯示回答
                st.success("AI 回覆：")
                st.write(answer)

        except Exception as e:
            st.error(f"發生錯誤：{e}")
