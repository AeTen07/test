# utils.py (更新版)

import os
import pandas as pd
import math
import streamlit as st

def get_city_options(data_dir="./Data"):
    if not os.path.exists(data_dir):
        return {}
    name_map = {
        "Taichung-city_buy_properties.csv": "台中市",
        "Taipei-city_buy_properties.csv": "台北市"
    }
    files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    options = {name_map[f]: f for f in files if f in name_map}
    return dict(sorted(options.items(), key=lambda x: x[0]))

def parse_layout(layout_str):
    """解析格局欄位 -> rooms, living_rooms, bathrooms"""
    import re
    if not isinstance(layout_str, str):
        return {"rooms": None, "living_rooms": None, "bathrooms": None}
    m = re.match(r'(\d+)房(\d+)廳(\d+)衛', layout_str)
    if m:
        return {"rooms": int(m.group(1)), "living_rooms": int(m.group(2)), "bathrooms": int(m.group(3))}
    nums = re.findall(r'(\d+)', layout_str)
    return {
        "rooms": int(nums[0]) if len(nums) > 0 else None,
        "living_rooms": int(nums[1]) if len(nums) > 1 else None,
        "bathrooms": int(nums[2]) if len(nums) > 2 else None
    }

def parse_floor(floor_str):
    """解析樓層欄位 -> floor min/max"""
    import re
    if not isinstance(floor_str, str):
        return {"min": None, "max": None}
    nums = re.findall(r'(\d+)', floor_str)
    return {"min": int(nums[0]) if len(nums) > 0 else None,
            "max": int(nums[1]) if len(nums) > 1 else None}

def normalize_special_value(val):
    """解析 Gemini 特殊要求成 min/max 或數字"""
    import re
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    s = str(val).strip()
    # 區間
    m = re.match(r'^(\d+)\s*[-~–]\s*(\d+)$', s)
    if m:
        return {"min": int(m.group(1)), "max": int(m.group(2))}
    # 以上
    m = re.search(r'(\d+)\s*(以上|\+|>=)', s)
    if m:
        return {"min": int(m.group(1))}
    # 以下
    m = re.search(r'(以下|<=)\s*(\d+)', s)
    if m:
        return {"max": int(m.group(2))}
    # 文字抽數字
    m = re.search(r'(\d+)', s)
    if m:
        return int(m.group(1))
    # 標籤
    if '低' in s:
        return {"min": 1, "max": 5}
    if '高' in s:
        return {"min": 6}
    return None

def filter_properties(df, filters):
    """篩選房產 DataFrame"""
    filtered_df = df.copy()
    try:
        # 類型
        if filters.get('housetype') and filters['housetype'] != "不限":
            if '類型' in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df['類型'].astype(str).str.contains(filters['housetype'], case=False, na=False)
                ]
        # 總價
        if '總價(萬)' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['總價(萬)'] >= filters.get('budget_min', 0)) &
                (filtered_df['總價(萬)'] <= filters.get('budget_max', 1e9))
            ]
        # 屋齡
        if '屋齡' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['屋齡'] >= filters.get('age_min', 0)) &
                (filtered_df['屋齡'] <= filters.get('age_max', 1e9))
            ]
        # 建坪
        if '建坪' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['建坪'] >= filters.get('area_min', 0)) &
                (filtered_df['建坪'] <= filters.get('area_max', 1e9))
            ]
        # 車位
        if 'car_grip' in filters and '車位' in filtered_df.columns:
            if filters['car_grip'] == "需要":
                filtered_df = filtered_df[
                    (filtered_df['車位'].notna()) &
                    (filtered_df['車位'] != "無") &
                    (filtered_df['車位'] != 0)
                ]
            elif filters['car_grip'] == "不要":
                filtered_df = filtered_df[
                    (filtered_df['車位'].isna()) |
                    (filtered_df['車位'] == "無") |
                    (filtered_df['車位'] == 0)
                ]
        # 格局與樓層
        for col in ['rooms', 'living_rooms', 'bathrooms', 'floor']:
            if col in filters and col in filtered_df.columns:
                val = filters[col]
                if isinstance(val, dict):
                    if 'min' in val:
                        filtered_df = filtered_df[filtered_df[col] >= val['min']]
                    if 'max' in val:
                        filtered_df = filtered_df[filtered_df[col] <= val['max']]
                else:
                    filtered_df = filtered_df[filtered_df[col] >= val]

    except Exception as e:
        st.error(f"篩選過程中發生錯誤: {e}")
        return df
    return filtered_df

def display_pagination(df, items_per_page=10):
    if 'current_search_page' not in st.session_state:
        st.session_state.current_search_page = 1
    total_items = len(df)
    total_pages = max(1, math.ceil(total_items / items_per_page))
    if st.session_state.current_search_page > total_pages:
        st.session_state.current_search_page = 1
    start_idx = (st.session_state.current_search_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    current_page_data = df.iloc[start_idx:end_idx]
    return current_page_data, st.session_state.current_search_page, total_pages, total_items
