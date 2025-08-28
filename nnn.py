import streamlit as st
import requests
import math
import folium
from streamlit_folium import st_folium

st.title("地址周邊 600 公尺查詢（OpenStreetMap 版）")

address = st.text_input("輸入地址")
radius = 600  # 公尺

PLACE_TAGS = {
    "教育": {
        "學校": {"amenity": "school"},
        "大學": {"amenity": "university"},
        "圖書館": {"amenity": "library"},
    },
    "健康": {
        "醫院": {"amenity": "hospital"},
        "藥局": {"amenity": "pharmacy"},
        "診所": {"amenity": "clinic"},
    },
    "購物": {
        "超市": {"shop": "supermarket"},
        "便利商店": {"shop": "convenience"},
    },
    "交通": {
        "公車站": {"highway": "bus_stop"},
        "火車站": {"railway": "station"},
        "地鐵站": {"railway": "subway_entrance"},
    },
    "餐飲": {
        "餐廳": {"amenity": "restaurant"},
        "咖啡": {"amenity": "cafe"},
    },
}

main_category = st.selectbox("選擇分類", PLACE_TAGS.keys())
sub_types = st.multiselect("選擇要查詢的地點類型", list(PLACE_TAGS[main_category].keys()))

# ------------------------------
# 工具函式
# ------------------------------
def geocode_nominatim(addr: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": addr, "format": "json", "limit": 1}
    r = requests.get(url, params=params, headers={"User-Agent": "streamlit-app"})
    if r.status_code == 200 and r.json():
        data = r.json()[0]
        return float(data["lat"]), float(data["lon"])
    return None, None


def query_overpass(lat, lon, radius, tags):
    query_parts = []
    for k, v in tags.items():
        query_parts.append(
            f"""
            node["{k}"="{v}"](around:{radius},{lat},{lon});
            way["{k}"="{v}"](around:{radius},{lat},{lon});
            relation["{k}"="{v}"](around:{radius},{lat},{lon});
            """
        )
    query = f"""
    [out:json][timeout:25];
    (
        {"".join(query_parts)}
    );
    out center;
    """
    r = requests.post("https://overpass-api.de/api/interpreter", data=query.encode("utf-8"))
    data = r.json()
    places = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name", "未命名")
        if "lat" in el:
            p_lat, p_lon = el["lat"], el["lon"]
        else:
            p_lat, p_lon = el["center"]["lat"], el["center"]["lon"]
        places.append((name, p_lat, p_lon))
    return places


# ------------------------------
# 查詢流程
# ------------------------------
if st.button("查詢"):
    if not address:
        st.error("請輸入地址")
        st.stop()

    lat, lon = geocode_nominatim(address)
    if not lat:
        st.error("無法解析地址")
        st.stop()

    all_places = []
    for sub in sub_types:
        tags = PLACE_TAGS[main_category][sub]
        results = query_overpass(lat, lon, radius, tags)
        for name, p_lat, p_lon in results:
            all_places.append((sub, name, p_lat, p_lon))

    st.subheader("查詢結果")
    if all_places:
        for t, name, _, _ in all_places:
            st.write(f"**{t}** - {name}")
    else:
        st.write("該範圍內沒有找到地點。")

    # 顯示地圖
    fmap = folium.Map(location=[lat, lon], zoom_start=16)
    folium.Marker([lat, lon], popup="查詢中心", icon=folium.Icon(color="red")).add_to(fmap)

    for t, name, p_lat, p_lon in all_places:
        folium.Marker([p_lat, p_lon], popup=f"{t}: {name}", icon=folium.Icon(color="blue")).add_to(fmap)

    st_folium(fmap, width=700, height=500)
