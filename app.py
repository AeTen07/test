import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import google.generativeai as genai

# 載入 .env 檔案
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# 設定 Gemini API 金鑰
genai.configure(api_key=api_key)

# 建立 Gemini 模型
model = genai.GenerativeModel('gemini-pro')

# Streamlit 網頁設定
st.set_page_config(page_title="CSV 上傳 + Gemini AI", layout="wide")

# 標題
st.title("📊 資料集上傳 + 🤖 Gemini AI 聊天室")

# 資料上傳區塊
st.subheader("1️⃣ 上傳你的 CSV 檔案")
uploaded_file = st.file_uploader("請選擇一個 CSV 檔案", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("成功上傳！預覽資料如下：")
    st.dataframe(df)

# Gemini AI 區塊
st.subheader("2️⃣ 與 Gemini AI 聊聊")
prompt = st.text_input("輸入你的問題")

if st.button("送出"):
    if not api_key:
        st.error("請確認你的 API 金鑰是否正確設定在 .env 檔案中。")
    elif prompt.strip() == "":
        st.warning("請輸入問題再送出。")
    else:
        try:
            with st.spinner("Gemini 思考中..."):
                response = model.generate_content(prompt)
                st.success("AI 回覆：")
                st.write(response.text)
        except Exception as e:
            st.error(f"發生錯誤：{e}")
