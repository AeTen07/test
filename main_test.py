import streamlit as st
import google.generativeai as genai
import time

# ======================
# 🔑 API KEY 設定
# ======================
st.title("🧪 Gemini API 模型測試工具")

api_key = st.text_input("AIzaSyAKE7etexSgsiI41vjHnXg3UcUVNJoSEhE", type="password")

if api_key:
    genai.configure(api_key=api_key)

    # ======================
    # 📥 取得模型列表
    # ======================
    @st.cache_data
    def get_models():
        models = genai.list_models()
        usable_models = []

        for m in models:
            # 只保留 generateContent 可用模型
            if "generateContent" in m.supported_generation_methods:
                usable_models.append(m.name)

        return usable_models

    models = get_models()

    st.subheader("📦 可用模型列表")
    st.write(models)

    # ======================
    # ✏️ 測試輸入
    # ======================
    prompt = st.text_area("輸入測試 Prompt", "請用一句話介紹人工智慧")

    # ======================
    # 🚀 一鍵測試
    # ======================
    if st.button("🚀 一鍵測試所有模型"):
        results = []

        for model_name in models:
            st.write(f"🔄 測試中：{model_name}")

            try:
                model = genai.GenerativeModel(model_name)

                start = time.time()
                response = model.generate_content(prompt)
                end = time.time()

                results.append({
                    "model": model_name,
                    "time": round(end - start, 2),
                    "text": response.text
                })

            except Exception as e:
                results.append({
                    "model": model_name,
                    "time": None,
                    "text": f"❌ 錯誤：{str(e)}"
                })

        # ======================
        # 📊 顯示結果
        # ======================
        st.subheader("📊 測試結果")

        for r in results:
            st.markdown(f"### 🧠 {r['model']}")
            st.write(f"⏱️ 耗時：{r['time']} 秒")
            st.write(r["text"])
            st.divider()

else:
    st.warning("請先輸入 API Key 才能開始測試")
