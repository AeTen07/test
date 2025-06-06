import streamlit as st
import pandas as pd
import google.generativeai as genai

# 直接寫在程式碼裡
api_key = "AIzaSyCWLb6_xQ57OsIOFFN5MfJtybzNV2vjxsw"

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="CSV 上傳 + Gemini AI", layout="wide")
st.title("📊 資料集上傳 + 🤖 Gemini AI 聊天室")

st.subheader("1️⃣ 上傳你的 CSV 檔案")
uploaded_file = st.file_uploader("請選擇一個 CSV 檔案", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("成功上傳！預覽資料如下：")
    st.dataframe(df)

st.subheader("2️⃣ 與 Gemini AI 聊聊")
prompt = st.text_input("輸入你的問題")

if st.button("送出"):
    st.success("AI 回覆：")
    st.write(response)

