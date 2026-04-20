import streamlit as st
import google.generativeai as genai
import time

st.set_page_config(page_title="Gemini API 測試工具", layout="wide")

st.title("🧪 Gemini API Key 測試工具")

# API KEY 輸入
api_key = st.text_input("🔑 輸入你的 Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)

    # ========================
    # 1️⃣ 列出可用模型
    # ========================
    st.subheader("📋 可用模型列表")

    try:
        models = genai.list_models()

        model_list = []
        for m in models:
            if "generateContent" in m.supported_generation_methods:
                model_list.append(m.name)

        st.success(f"共找到 {len(model_list)} 個可用模型")

        selected_model = st.selectbox("選擇模型", model_list)

    except Exception as e:
        st.error(f"讀取模型失敗：{e}")
        selected_model = None

    # ========================
    # 2️⃣ 測試 Prompt
    # ========================
    st.subheader("💬 測試 Prompt")

    prompt = st.text_area("輸入內容", "你好，請簡單介紹你自己")

    if st.button("🚀 開始測試") and selected_model:
        try:
            model = genai.GenerativeModel(selected_model)

            start = time.time()
            response = model.generate_content(prompt)
            end = time.time()

            st.success("回應成功！")

            st.markdown("### 🤖 模型回應")
            st.write(response.text)

            st.info(f"⏱️ 耗時：{end - start:.2f} 秒")

        except Exception as e:
            st.error(f"發生錯誤：{e}")
else:
    st.warning("請先輸入 API Key")
