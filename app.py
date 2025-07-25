import streamlit as st
import google.generativeai as genai
import pandas as pd

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
if "use_uploaded_file" not in st.session_state:
    st.session_state.use_uploaded_file = False
if "enable_memory" not in st.session_state:
    st.session_state.enable_memory = True  # ✅ 預設啟用可持續對話

# ---------------- 🔐 側邊欄：API 金鑰、上傳檔案、是否啟用記憶、聊天紀錄下載、載入聊天紀錄----------------
with st.sidebar:
    st.markdown("## 🔐 API 設定")
    st.markdown("限 gemini-1.5-flash")
    remember_api_checkbox = st.checkbox("記住 API 金鑰", value=st.session_state.remember_api)
    if not remember_api_checkbox and st.session_state.remember_api:
        st.session_state.api_key = ""
    st.session_state.remember_api = remember_api_checkbox

    if st.session_state.remember_api and st.session_state.api_key:
        api_key_input = st.session_state.api_key
    else:
        api_key_input = st.text_input("請輸入 Gemini API 金鑰", type="password")
#--------------
    st.markdown("---")
    st.markdown("## 💡 對話設定")
    st.session_state.enable_memory = st.checkbox("✅ 啟用持續對話記憶", value=st.session_state.enable_memory)
#--------------
    st.markdown("---")
    st.markdown("## 📎 檔案輔助")
    uploaded_file = st.file_uploader("上傳文字檔", type=["txt", "csv", "md", "json"])
    if uploaded_file:
        file_content = uploaded_file.read().decode("utf-8")
        st.session_state.uploaded_file_content = file_content
        st.info("✅ 文字檔案已上傳。")
        st.session_state.use_uploaded_file = st.checkbox("✅ 使用上傳檔案輔助回答", value=True)
    else:
        st.session_state.use_uploaded_file = False
    st.markdown("---")# 💾 聊天紀錄下載 
    st.markdown("## 💾 聊天紀錄下載(未完成)")
    if st.session_state.chat_history:
        all_history = "\n\n".join([f"👤 {m['user']}\n🤖 {m['ai']}" for m in st.session_state.chat_history])
        st.download_button("💾 下載聊天紀錄", all_history, file_name="gemini_chat.txt", use_container_width=True)
#--------------
    st.markdown("---")
    st.markdown("## 🗑️ 清除聊天")
    if st.button("清除所有聊天記錄", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.chat = None
        st.success("✅ 已清除聊天紀錄")
#--------------
    st.markdown("---")
    st.markdown("## 📤 載入聊天紀錄")
    uploaded_history = st.file_uploader("載入 .txt 聊天紀錄", type=["txt"], key="load_history")

    if uploaded_history:
        try:
            content = uploaded_history.read().decode("utf-8")
            history = []
            blocks = content.strip().split("\n\n")
            for block in blocks:
                if block.startswith("👤 ") and "\n🤖 " in block:
                    user_part, ai_part = block.split("\n🤖 ", 1)
                    user_msg = user_part.replace("👤 ", "").strip()
                    ai_msg = ai_part.strip()
                    history.append({"user": user_msg, "ai": ai_msg})
            st.session_state.chat_history = history
            st.success("✅ 聊天紀錄已載入！")
        except Exception as e:
            st.error("❌ 載入失敗，請確認格式是否正確")
            st.exception(e)

# ---------------- 💬 歷史對話區 ----------------
for msg in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(msg["user"])
    with st.chat_message("ai"):
        st.markdown(msg["ai"])

# ---------------- 📥 輸入區 ----------------
prompt = st.chat_input("請輸入你的問題...")

# ---------------- 🚀 Gemini 回應 ----------------
if prompt:
    if not api_key_input:
        st.error("❌ 請輸入有效的 API 金鑰")
        st.stop()

    try:
        genai.configure(api_key=api_key_input)
        model = genai.GenerativeModel("gemini-1.5-flash")

        # ✅ 若啟用記憶，使用 chat 對象；否則每次用單獨 model.generate_content()
        if st.session_state.enable_memory:
            if not st.session_state.chat:
                st.session_state.chat = model.start_chat(history=[])
        else:
            st.session_state.chat = None

        # 合成完整提示
        full_prompt = prompt
        if st.session_state.use_uploaded_file and st.session_state.uploaded_file_content:
            full_prompt += "\n\n（附檔內容如下，請一併考慮）\n" + st.session_state.uploaded_file_content

        with st.spinner("🤔 Gemini 思考中..."):
            if st.session_state.enable_memory:
                response = st.session_state.chat.send_message(full_prompt)
                ai_text = response.text
            else:
                response = model.generate_content(full_prompt)
                ai_text = response.text

        # 顯示提問與 AI 回覆
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("ai"):
            st.markdown(ai_text)

        # 儲存對話紀錄
        st.session_state.chat_history.append({
            "user": prompt,
            "ai": ai_text
        })

        # 清空暫存內容（不清掉 checkbox）
        st.session_state.uploaded_file_content = ""

        # 記住金鑰
        if st.session_state.remember_api:
            st.session_state.api_key = api_key_input
        else:
            st.session_state.api_key = ""

    except Exception as e:
        if "API key" in str(e) or "permission" in str(e).lower() or "403" in str(e):
            st.error("❌ API 金鑰無效或權限不足，請確認後重新輸入。")
        else:
            st.error("❌ 發生未知錯誤，請稍後再試。")
            st.exception(e)
