import streamlit as st
import pandas as pd
import google.generativeai as genai

# 直接寫在程式碼裡
api_key = "你的_GEMINI_API_KEY_直接貼在這裡"

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

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
    if not api_key:
        st.error("API 金鑰未設定！")
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
