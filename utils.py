import os
import pandas as pd
import math
import streamlit as st

def get_city_options(data_dir="./Data"):
    """
    獲取城市選項，只顯示對照表內有定義的檔案
    """
    if not os.path.exists(data_dir):
        return {}

    name_map = {
        "Taichung-city_buy_properties.csv": "台中市",
        "Taipei-city_buy_properties.csv": "台北市"
    }

    files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    options = {name_map[f]: f for f in files if f in name_map}
    options = dict(sorted(options.items(), key=lambda x: x[0]))

    return options


def filter_properties(df, filters):
    """
    根據篩選條件過濾房產資料（支援模糊搜尋 + Gemini 特殊要求）
    """
    filtered_df = df.copy()
    try:
        # 🏠 房產類型（模糊搜尋）
        if filters.get('housetype') and filters['housetype'] != "不限":
            if '類型' in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df['類型'].astype(str).str.contains(filters['housetype'], case=False, na=False)
                ]

        # 💰 預算範圍
        if filters.get('budget_min', 0) > 0 and '總價(萬)' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['總價(萬)'] >= filters['budget_min']]
        if filters.get('budget_max', 1000000) < 1000000 and '總價(萬)' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['總價(萬)'] <= filters['budget_max']]

        # 🏢 屋齡
        if filters.get('age_min', 0) > 0 and '屋齡' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['屋齡'] >= filters['age_min']]
        if filters.get('age_max', 100) < 100 and '屋齡' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['屋齡'] <= filters['age_max']]

        # 📏 建坪
        if filters.get('area_min', 0) > 0 and '建坪' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['建坪'] >= filters['area_min']]
        if filters.get('area_max', 1000) < 1000 and '建坪' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['建坪'] <= filters['area_max']]

        # 🚗 車位
        if 'car_grip' in filters and '車位' in filtered_df.columns:
            if filters['car_grip'] == "需要":
                filtered_df = filtered_df[
                    (filtered_df['車位'].notna()) &
                    (~filtered_df['車位'].astype(str).str.contains("無"))
                ]
            elif filters['car_grip'] == "不要":
                filtered_df = filtered_df[
                    (filtered_df['車位'].isna()) |
                    (filtered_df['車位'].astype(str).str.contains("無"))
                ]

        # ===== Gemini AI 特殊要求 =====
        exact_match = filters.get("_exact_match", False)

        # 🛏 房間數
        if "rooms" in filters and '房間數' in filtered_df.columns:
            rooms = filters["rooms"]
            if exact_match:
                filtered_df = filtered_df[filtered_df['房間數'] == rooms]
            else:
                filtered_df = filtered_df[filtered_df['房間數'] >= rooms]

        # 🛋 廳數
        if "living_rooms" in filters and '廳數' in filtered_df.columns:
            living = filters["living_rooms"]
            if exact_match:
                filtered_df = filtered_df[filtered_df['廳數'] == living]
            else:
                filtered_df = filtered_df[filtered_df['廳數'] >= living]

        # 🚿 衛數
        if "bathrooms" in filters and '衛數' in filtered_df.columns:
            bath = filters["bathrooms"]
            if exact_match:
                filtered_df = filtered_df[filtered_df['衛數'] == bath]
            else:
                filtered_df = filtered_df[filtered_df['衛數'] >= bath]

    except Exception as e:
        st.error(f"篩選過程中發生錯誤: {e}")
        return df

    return filtered_df


def display_pagination(df, items_per_page=10):
    """
    處理分頁邏輯並返回當前頁面的資料
    """
    if 'current_search_page' not in st.session_state:
        st.session_state.current_search_page = 1

    total_items = len(df)
    total_pages = math.ceil(total_items / items_per_page) if total_items > 0 else 1

    if st.session_state.current_search_page > total_pages:
        st.session_state.current_search_page = 1

    start_idx = (st.session_state.current_search_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    current_page_data = df.iloc[start_idx:end_idx]

    return current_page_data, st.session_state.current_search_page, total_pages, total_items
