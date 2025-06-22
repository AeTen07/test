import streamlit as st
import pandas as pd
import google.generativeai as genai

# 頁面設定
st.set_page_config(page_title="Gemini 聊天室", layout="wide")
st.title("🤖 Gemini AI 聊天室 + 📁 CSV 上傳")

# 取得使用者輸入的 API 金鑰
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

st.sidebar.header("🔑 輸入 Gemini API 金鑰")
api_key_input = st.sidebar.text_input("請輸入你的 API 金鑰", type="password")
if api_key_input:
    st.session_state.api_key = api_key_input

# 檢查 API 金鑰是否存在
if not st.session_state.api_key:
    st.warning("⚠️ 請在左側輸入有效的 Gemini API 金鑰後使用本系統。")
    st.stop()

# 設定 Gemini
try:
    genai.configure(api_key=st.session_state.api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"API 金鑰設定失敗：{e}")
    st.stop()

# 初始化聊天紀錄
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 📁 CSV 上傳功能
st.subheader("📂 上傳 CSV 檔案")
uploaded_file = st.file_uploader("請選擇一個 CSV 檔案", type="csv")
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.success("✅ 成功上傳！以下是資料預覽：")

        # 顯示欄位選擇器
        selected_columns = st.multiselect("📌 請選擇要使用的欄位", df.columns.tolist(), default=df.columns.tolist())

        # 按鈕區：選擇圖表類型
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            show_table = st.button("📋 顯示資料表")
        with col2:
            show_bar = st.button("📊 長條圖")
        with col3:
            show_pie = st.button("🥧 圓餅圖")
        with col4:
            show_line = st.button("📈 折線圖")

        # 資料篩選
        if selected_columns:
            filtered_df = df[selected_columns]
        else:
            st.warning("⚠️ 請選擇至少一個欄位")
            st.stop()

        # 顯示表格
        if show_table:
            st.subheader("📋 資料表")
            st.dataframe(filtered_df)

        # 顯示長條圖（限類別 + 數值）
        if show_bar:
            st.subheader("📊 長條圖")
            if len(selected_columns) >= 2:
                st.bar_chart(filtered_df)
            else:
                st.warning("⚠️ 請選擇兩個以上欄位來畫長條圖")

        # 顯示圓餅圖（只支援一欄類別、一欄數值）
        if show_pie:
            st.subheader("🥧 圓餅圖")
            if len(selected_columns) == 2:
                cat_col, val_col = selected_columns
                pie_data = df.groupby(cat_col)[val_col].sum().reset_index()
                fig_pie = px.pie(pie_data, names=cat_col, values=val_col, title="圓餅圖")
                st.plotly_chart(fig_pie)
            else:
                st.warning("⚠️ 圓餅圖需選擇 1 個類別欄位 + 1 個數值欄位")

        # 顯示折線圖（通常用於時間序列）
        if show_line:
            st.subheader("📈 折線圖")
            st.line_chart(filtered_df)

    except Exception as e:
        st.error(f"CSV 讀取錯誤：{e}")


# 🧠 側邊欄：記憶留存區
with st.sidebar:
    st.header("🧠 記憶留存區")
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            st.markdown(f"👤 **你：** {msg['user']}")
            st.markdown(f"🤖 **AI：** {msg['ai']}")
            st.markdown("---")
        if st.button("🗑️ 清除對話紀錄"):
            st.session_state.chat_history = []
            st.experimental_rerun()
    else:
        st.info("目前沒有對話紀錄。")

# 💬 聊天介面
st.subheader("💬 Gemini AI 對話區")

# 顯示聊天氣泡
for msg in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(msg["user"])
    with st.chat_message("ai"):
        st.markdown(msg["ai"])

# 輸入對話
if prompt := st.chat_input("輸入你的問題..."):
    # 顯示自己的訊息
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gemini 回應
    with st.chat_message("ai"):
        with st.spinner("Gemini 思考中..."):
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
