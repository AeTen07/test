import streamlit as st
import requests
import folium
import os
import math
from dotenv import load_dotenv
from streamlit_folium import st_folium
import google.generativeai as genai

# ===============================
# 載入環境變數
# ===============================
load_dotenv()
OPENCAGE_KEY = os.getenv("OPENCAGE_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not OPENCAGE_KEY:
    st.error("❌ 請先設定環境變數 OPENCAGE_API_KEY")
    st.stop()

if not GEMINI_KEY:
    st.error("❌ 請先設定環境變數 GEMINI_API_KEY")
    st.stop()

# 設定 Gemini API
genai.configure(api_key=GEMINI_KEY)

# ===============================
# OSM Tags (替代 Google Places 類別)
# ===============================
PLACE_TYPES = {
    "教育": {
        "學校": {"amenity": "school"},
        "大學": {"amenity": "university"},
        "圖書館": {"amenity": "library"},
    },
    "健康與保健": {
        "醫院": {"amenity": "hospital"},
        "藥局": {"amenity": "pharmacy"},
        "診所": {"amenity": "doctors"},
    },
    "購物": {
        "便利商店": {"shop": "convenience"},
        "超市": {"shop": "supermarket"},
        "百貨公司": {"shop": "department_store"},
    },
    "交通運輸": {
        "公車站": {"highway": "bus_stop"},
        "火車站": {"railway": "station"},
        "捷運/地鐵站": {"railway": "subway_entrance"},
    },
    "餐飲": {
        "餐廳": {"amenity": "restaurant"},
        "咖啡廳": {"amenity": "cafe"},
    }
}

# ===============================
# 工具函式
# ===============================
def geocode_address(address: str):
    """利用 OpenCage 把地址轉成經緯度"""
    url = "https://api.opencagedata.com/geocode/v1/json"
    params = {"q": address, "key": OPENCAGE_KEY, "language": "zh-TW", "limit": 1}
    try:
        res = requests.get(url, params=params, timeout=10).json()
        if res["results"]:
            return res["results"][0]["geometry"]["lat"], res["results"][0]["geometry"]["lng"]
        else:
            return None, None
    except Exception:
        return None, None

def query_osm_places(lat, lng, radius, selected_types):
    """用 Overpass API 查詢指定類型地點"""
    query_parts = []
    for sub_type in selected_types:
        tag_dict = selected_types[sub_type]
        for k, v in tag_dict.items():
            query_parts.append(f"""
              node["{k}"="{v}"](around:{radius},{lat},{lng});
              way["{k}"="{v}"](around:{radius},{lat},{lng});
              relation["{k}"="{v}"](around:{radius},{lat},{lng});
            """)
    query = f"""
    [out:json][timeout:25];
    (
        {"".join(query_parts)}
    );
    out center;
    """

    try:
        r = requests.post("https://overpass-api.de/api/interpreter", data=query.encode("utf-8"), timeout=20)
        data = r.json()
    except:
        return []

    results = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name", "未命名")
        lat_p = el.get("lat") or el.get("center", {}).get("lat")
        lon_p = el.get("lon") or el.get("center", {}).get("lon")
        if lat_p and lon_p:
            results.append((name, lat_p, lon_p, tags))
    return results

def haversine(lat1, lon1, lat2, lon2):
    """計算兩點距離（公尺）"""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(d_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ===============================
# Streamlit UI
# ===============================
st.title("📍 地址周邊查詢 (OSM 版，免 Google API)")

address = st.text_input("輸入地址")
radius = st.slider("搜尋半徑（公尺）", 100, 1000, 600)

main_category = st.selectbox("選擇分類", PLACE_TYPES.keys())
sub_types = st.multiselect("選擇要查詢的地點類型", list(PLACE_TYPES[main_category].keys()))

if st.button("查詢"):
    lat, lng = geocode_address(address)
    if not lat or not lng:
        st.error("❌ 無法解析該地址")
        st.stop()

    selected_dict = {sub: PLACE_TYPES[main_category][sub] for sub in sub_types}
    places = query_osm_places(lat, lng, radius, selected_dict)

    if not places:
        st.warning("⚠️ 這個範圍內沒有找到相關地點")
        st.stop()

    # 排序 (由近到遠)
    places = [(name, p_lat, p_lng, int(haversine(lat, lng, p_lat, p_lng)))
              for name, p_lat, p_lng, _ in places]
    places.sort(key=lambda x: x[3])

    st.subheader("查詢結果（由近到遠）")
    for name, p_lat, p_lng, dist in places:
        st.write(f"**{name}** - {dist} 公尺")

    # 在地圖上顯示
    m = folium.Map(location=[lat, lng], zoom_start=16)
    folium.Marker([lat, lng], tooltip="查詢中心", icon=folium.Icon(color="red")).add_to(m)

    for name, p_lat, p_lng, dist in places:
        folium.Marker(
            [p_lat, p_lng],
            tooltip=f"{name} ({dist} 公尺)",
            icon=folium.Icon(color="blue")
        ).add_to(m)

    st_folium(m, width=700, height=500)
