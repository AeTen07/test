import streamlit as st
import requests
import folium
import os
import math
from dotenv import load_dotenv
from streamlit_folium import st_folium
import google.generativeai as genai
from streamlit.components.v1 import html

# ===============================
# 載入環境變數
# ===============================
load_dotenv()
OPENCAGE_KEY = os.getenv("OPENCAGE_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")

if not OPENCAGE_KEY:
    st.error("❌ 請先設定環境變數 OPENCAGE_API_KEY")
    st.stop()

if not GEMINI_KEY:
    st.error("❌ 請先設定環境變數 GEMINI_API_KEY")
    st.stop()

if not GOOGLE_KEY:
    st.error("❌ 請先設定環境變數 GOOGLE_API_KEY")
    st.stop()

# 設定 Gemini API
genai.configure(api_key=GEMINI_KEY)

# ===============================
# 支援查詢的 OSM Tags
# ===============================
OSM_TAGS = {
    "交通": {"public_transport": "stop_position"},
    "超商": {"shop": "convenience"},
    "餐廳": {"amenity": "restaurant"},
    "學校": {"amenity": "school"},
    "醫院": {"amenity": "hospital"},
    "藥局": {"amenity": "pharmacy"}
}

# ===============================
# Google Places 支援的分類
# ===============================
PLACE_TYPES = {
    "教育": {
        "圖書館": "library",
        "幼兒園": "preschool",
        "小學": "primary_school",
        "學校": "school",
        "中學": "secondary_school",
        "大學": "university",
    },
    "健康與保健": {
        "牙醫": "dentist",
        "醫師": "doctor",
        "藥局": "pharmacy",
        "醫院": "hospital",
        "藥妝店": "drugstore",
        "物理治療所": "physiotherapist",
        "按摩": "massage",
        "三溫暖": "sauna",
        "SPA": "spa",
        "瑜伽教室": "yoga_studio",
    },
    "購物": {
        "便利商店": "convenience_store",
        "超市": "supermarket",
        "百貨公司": "department_store",
        "書店": "book_store",
        "五金行": "hardware_store",
        "鞋店": "shoe_store",
        "寵物店": "pet_store",
        "體育用品店": "sporting_goods_store",
    },
    "交通運輸": {
        "機場": "airport",
        "公車站": "bus_station",
        "地鐵站": "subway_station",
        "火車站": "train_station",
        "計程車招呼站": "taxi_stand",
        "交通站點": "transit_station",
    },
    "餐飲": {
        "餐廳": "restaurant"
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


def query_osm(lat, lng, radius=200):
    """合併查詢 OSM，一次拿回所有資料"""
    query_parts = []
    for tag_dict in OSM_TAGS.values():
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
        return {}

    results = {k: [] for k in OSM_TAGS.keys()}

    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name", "未命名")

        for label, tag_dict in OSM_TAGS.items():
            for k, v in tag_dict.items():
                if tags.get(k) == v:
                    results[label].append(name)

    return results


def format_info(address, info_dict):
    """整理統計數字給 Gemini"""
    lines = [f"房屋（{address}）："]
    for k, v in info_dict.items():
        lines.append(f"- {k}: {len(v)} 個")
    return "\n".join(lines)


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
# Streamlit UI 主選單
# ===============================
st.title("🏠 房屋助手 & 地址周邊查詢")

menu = st.sidebar.radio("功能選單", ["房屋比較助手", "地址周邊查詢"])

# ===============================
# 功能 1：房屋比較助手
# ===============================
if menu == "房屋比較助手":
    st.header("🏠 房屋比較助手 + 💬 對話框")

    if "comparison_done" not in st.session_state:
        st.session_state["comparison_done"] = False
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "text_a" not in st.session_state:
        st.session_state["text_a"] = ""
    if "text_b" not in st.session_state:
        st.session_state["text_b"] = ""

    col1, col2 = st.columns(2)
    with col1:
        addr_a = st.text_input("輸入房屋 A 地址")
    with col2:
        addr_b = st.text_input("輸入房屋 B 地址")

    if st.button("比較房屋"):
        if not addr_a or not addr_b:
            st.warning("請輸入兩個地址")
            st.stop()

        lat_a, lng_a = geocode_address(addr_a)
        lat_b, lng_b = geocode_address(addr_b)
        if not lat_a or not lat_b:
            st.error("❌ 無法解析其中一個地址")
            st.stop()

        info_a = query_osm(lat_a, lng_a, radius=200)
        info_b = query_osm(lat_b, lng_b, radius=200)

        text_a = format_info(addr_a, info_a)
        text_b = format_info(addr_b, info_b)

        st.session_state["text_a"] = text_a
        st.session_state["text_b"] = text_b

        prompt = f"""
        你是一位房地產分析專家，請比較以下兩間房屋的生活機能。
        請列出優點與缺點，最後做總結：

        {text_a}

        {text_b}
        """
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)

        st.subheader("📊 Gemini 分析結果")
        st.write(response.text)

        st.session_state["comparison_done"] = True

    with st.sidebar:
        if st.session_state["comparison_done"]:
            st.subheader("🏠 房屋資訊對照表")
            st.markdown(f"### 房屋 A\n{st.session_state['text_a']}")
            st.markdown(f"### 房屋 B\n{st.session_state['text_b']}")
        else:
            st.info("⚠️ 請先輸入房屋地址並比較")

    if st.session_state["comparison_done"]:
        st.header("💬 簡單對話框")

        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("你想問什麼？", placeholder="請輸入問題...")
            submitted = st.form_submit_button("🚀 送出")

        if submitted and user_input:
            st.session_state["chat_history"].append(("👤", user_input))

            chat_prompt = f"""
            以下是兩間房屋的周邊資訊：

            {st.session_state['text_a']}

            {st.session_state['text_b']}

            使用者問題：{user_input}

            請根據房屋周邊的生活機能與位置，提供有意義的回答。
            """

            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(chat_prompt)
            st.session_state["chat_history"].append(("🤖", response.text))

        for role, msg in st.session_state["chat_history"]:
            st.markdown(f"**{role}**：{msg}")

# ===============================
# 功能 2：Google 地址周邊查詢
# ===============================
elif menu == "地址周邊查詢":
    st.header("📍 地址周邊查詢 (Google Places API)")
    address = st.text_input("輸入地址")
    radius = st.slider("搜尋半徑（公尺）", 100, 1000, 600)

    main_category = st.selectbox("選擇分類", PLACE_TYPES.keys())
    sub_types = st.multiselect("選擇要查詢的地點類型", list(PLACE_TYPES[main_category].keys()))

    if st.button("查詢"):
        geo_url = "https://maps.googleapis.com/maps/api/geocode/json"
        geo_params = {"address": address, "key": GOOGLE_KEY, "language": "zh-TW"}
        geo_res = requests.get(geo_url, params=geo_params).json()

        if geo_res.get("status") != "OK":
            st.error("無法解析該地址")
            st.stop()

        location = geo_res["results"][0]["geometry"]["location"]
        lat, lng = location["lat"], location["lng"]

        all_places = []
        for sub_type in sub_types:
            place_type = PLACE_TYPES[main_category][sub_type]
            places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            places_params = {
                "location": f"{lat},{lng}",
                "radius": radius,
                "type": place_type,
                "key": GOOGLE_KEY,
                "language": "zh-TW"
            }
            places_res = requests.get(places_url, params=places_params).json()

            for place in places_res.get("results", []):
                name = place.get("name", "未命名")
                p_lat = place["geometry"]["location"]["lat"]
                p_lng = place["geometry"]["location"]["lng"]
                dist = int(haversine(lat, lng, p_lat, p_lng))
                all_places.append((sub_type, name, p_lat, p_lng, dist))

        all_places = sorted(all_places, key=lambda x: x[4])

        st.subheader("查詢結果（由近到遠）")
        if all_places:
            for t, name, _, _, dist in all_places:
                st.write(f"**{t}** - {name} ({dist} 公尺)")
        else:
            st.write("該範圍內無相關地點。")

        icon_map = {
            "餐廳": "http://maps.google.com/mapfiles/ms/icons/orange-dot.png",
            "醫院": "http://maps.google.com/mapfiles/ms/icons/green-dot.png",
            "便利商店": "http://maps.google.com/mapfiles/ms/icons/blue-dot.png",
            "交通站點": "http://maps.google.com/mapfiles/ms/icons/yellow-dot.png"
        }

        markers_js = ""
        for t, name, p_lat, p_lng, dist in all_places:
            icon_url = icon_map.get(t, "http://maps.google.com/mapfiles/ms/icons/blue-dot.png")
            markers_js += f"""
            var marker = new google.maps.Marker({{
                position: {{lat: {p_lat}, lng: {p_lng}}},
                map: map,
                title: "{t}: {name}",
                icon: {{ url: "{icon_url}" }}
            }});
            var infowindow = new google.maps.InfoWindow({{
                content: "{t}: {name}<br>距離中心 {dist} 公尺"
            }});
            marker.addListener("click", function() {{
                infowindow.open(map, marker);
            }});
            """

        map_html = f"""
        <div id="map" style="height:500px;"></div>
        <script>
        function initMap() {{
            var center = {{lat: {lat}, lng: {lng}}};
            var map = new google.maps.Map(document.getElementById('map'), {{
                zoom: 16,
                center: center
            }});

            new google.maps.Marker({{
                position: center,
                map: map,
                title: "查詢中心",
                icon: {{ url: "http://maps.google.com/mapfiles/ms/icons/red-dot.png" }}
            }});

            {markers_js}
        }}
        </script>
        <script src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_KEY}&callback=initMap" async defer></script>
        """

        html(map_html, height=500)
