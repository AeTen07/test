import streamlit as st
import google.generativeai as genai

# 頁面設定
st.set_page_config(page_title="Gemini 聊天室", layout="wide")
st.title("🤖 Gemini AI 聊天室")

# 初始化狀態
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "remember_api" not in st.session_state:
    st.session_state.remember_api = False
if "chat" not in st.session_state:
    st.session_state.chat = None  # Gemini 的 chat 物件

# ---------------- 🔐 API 金鑰輸入區 ----------------
with st.sidebar:
    st.markdown("## 🔐 API 設定")
    st.markdown("## 限gemini-1.5-flash")
    
    remember_api_checkbox = st.checkbox("記住 API 金鑰", value=st.session_state.remember_api)

    # 檢查是否從勾選變為取消，若是則清空 API 金鑰
    if not remember_api_checkbox and st.session_state.remember_api:
        st.session_state.api_key = ""

    # 更新勾選狀態
    st.session_state.remember_api = remember_api_checkbox

    # 根據勾選狀態與 API 金鑰顯示或輸入
    if st.session_state.remember_api and st.session_state.api_key:
        api_key_input = st.session_state.api_key
    else:
        api_key_input = st.text_input("請輸入 Gemini API 金鑰", type="password")

# ---------------- 💬 對話顯示區 ----------------
st.subheader("💬 Gemini AI 對話區")

# 顯示歷史對話泡泡
for msg in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(msg["user"])
    with st.chat_message("ai"):
        st.markdown(msg["ai"])

# 💾 下載對話紀錄
if st.session_state.chat_history:
    all_history = "\n\n".join([f"👤 {m['user']}\n🤖 {m['ai']}" for m in st.session_state.chat_history])
    st.download_button("💾 下載聊天紀錄", all_history, file_name="gemini_chat.txt")
# ---------------- 📎 檔案上傳區 ----------------
st.subheader("📎 上傳檔案（PDF / TXT / CSV）")
uploaded_file = st.file_uploader("選擇一個檔案", type=["txt", "pdf", "csv"])

uploaded_text = ""
if uploaded_file:
    try:
        file_type = uploaded_file.name.split(".")[-1].lower()
        if file_type == "txt":
            uploaded_text = uploaded_file.read().decode("utf-8")
        elif file_type == "csv":
            import pandas as pd
            df = pd.read_csv(uploaded_file)
            uploaded_text = df.to_string()
        elif file_type == "pdf":
            import fitz  # PyMuPDF
            with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                uploaded_text = "\n".join([page.get_text() for page in doc])
        else:
            st.warning("❗ 不支援的檔案格式")
    except Exception as e:
        st.error(f"❌ 檔案讀取失敗：{e}")

    st.success("✅ 檔案已上傳並讀取完成")
    with st.expander("📄 檔案內容預覽"):
        st.text(uploaded_text[:3000])  # 預覽前 3000 字元


# ---------------- 💬 使用 chat 模式持續對話 ----------------
# 下方輸入框（固定）
prompt = st.chat_input("請輸入你的問題...")

if prompt:
    if not api_key_input:
        st.error("❌ 請輸入有效的 API 金鑰")
        st.stop()

    try:
        # 設定 API
        genai.configure(api_key=api_key_input)

        # 建立 model 與對話物件
        model = genai.GenerativeModel("gemini-1.5-flash")

        if not st.session_state.chat:
            st.session_state.chat = model.start_chat(history=[])

        # 顯示提問
        with st.chat_message("user"):
            st.markdown(prompt)

        # Gemini 回應
        with st.chat_message("ai"):
            with st.spinner("🤖 Gemini 思考中..."):
                response = st.session_state.chat.send_message(prompt)
                ai_text = response.text
                st.markdown(ai_text)

                # 儲存對話
                st.session_state.chat_history.append({
                    "user": prompt,
                    "ai": ai_text
                })

        # 記住 API 金鑰
        if st.session_state.remember_api:
            st.session_state.api_key = api_key_input
        else:
            st.session_state.api_key = ""

    except Exception as e:
        st.error(f"❌ 錯誤：{e}")
