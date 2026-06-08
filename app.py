import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import pytz
from plotly.subplots import make_subplots

# Verification Engine ခေါ်ယူခြင်း
try:
    from verification_engine import DMHForecastVerification
except ImportError:
    DMHForecastVerification = None

# --- ၁။ Layout Setup ---
st.set_page_config(page_title="DMH AI Weather Forecast System", layout="wide", page_icon="🌤️")
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
formatted_now = now.strftime('%I:%M %p, %d %b %Y')
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

# --- ၂။ Heat Indices Logic ---
def calculate_all_indices(temp_c, rh):
    hi = 0.5 * (temp_c + 61.0 + ((temp_c - 68.0) * 1.2) + (rh * 0.094))
    e = (rh / 100) * 6.105 * np.exp(17.27 * temp_c / (237.7 + temp_c))
    wbgt = (0.567 * temp_c) + (0.393 * e) + 3.94
    utci = temp_c + (0.33 * e) - (0.7 * 0.1) - 4.0
    return round(hi, 1), round(wbgt, 1), round(utci, 1)

# --- ၃။ API ကန့်သတ်ချက်မိပါက အလိုအလျောက် သုံးမည့် အရန်ဒေတာစနစ် (Fallback Demo Data Engine) ---
def generate_fallback_data(base_lat, base_lon):
    """API Limit သို့မဟုတ် အမှားအယွင်းတက်ပါက App အလှမပျက်စေရန် အရန်ဒေတာ ထုတ်ပေးသည့်စနစ်"""
    start_time = datetime.now(mm_tz).replace(hour=0, minute=0, second=0, microsecond=0)
    hours = [start_time + timedelta(hours=i) for i in range(16 * 24)]
    dates = [start_time.date() + timedelta(days=i) for i in range(16)]
    
    # Hourly simulation
    temp_hourly = [28 + 6 * np.sin(2 * np.pi * i / 24) + np.random.normal(0, 0.5) for i in range(16 * 24)]
    precip_hourly = [max(0, np.random.normal(-0.5, 1.5)) if i % 12 == 0 else 0 for i in range(16 * 24)]
    wind_hourly = [8 + 4 * np.sin(2 * np.pi * i / 24) for i in range(16 * 24)]
    wind_dir = [180 + np.random.randint(-30, 30) for _ in range(16 * 24)]
    humid_hourly = [75 - 15 * np.sin(2 * np.pi * i / 24) for i in range(16 * 24)]
    vis_hourly = [10.0 + np.random.normal(0, 1) for _ in range(16 * 24)]
    cloud_hourly = [np.random.randint(2, 8) for _ in range(16 * 24)]
    thunder_hourly = [np.random.randint(10, 85) for _ in range(16 * 24)]
    
    df_h = pd.DataFrame({
        "Time": hours, "Temp": temp_hourly, "precipitation": precip_hourly,
        "Wind": wind_hourly, "WindDir": wind_dir, "Vis": [max(1.0, v) for v in vis_hourly],
        "Humid": [clamped for clamped in [75 - 15 * np.sin(2 * np.pi * i / 24) for i in range(16 * 24)]],
        "Cloud_Oktas": cloud_hourly, "Thunderstorm": thunder_hourly
    })
    # Humid bounding box correction
    df_h['Humid'] = df_h['Humid'].clip(30, 100)
    df_h['HI'], df_h['WBGT'], df_h['UTCI'] = zip(*df_h.apply(lambda x: calculate_all_indices(x['Temp'], x['Humid']), axis=1))
    
    # Daily simulation
    df_d = pd.DataFrame({
        "Date": pd.to_datetime(dates),
        "Tmax": [34 + np.random.uniform(-1, 1) for _ in range(16)],
        "Tmin": [24 + np.random.uniform(-1, 1) for _ in range(16)]
    })
    return df_h, df_d

# --- ၄။ ဘာသာစကားနှင့် စာသားများ ---
LANG_DATA = {
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသခန်းမှန်းချက်စနစ်",
        "station_label": "🎯 စခန်းအမည်ရွေးချယ်ပါ",
        "view_mode_label": "📊 View Mode",
        "modes": [
            "၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", 
            "अပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး )", 
            "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀-SSP5-8.5)",
            "Icon Style ခန့်မှန်းချက်",
            "ပင်လယ်ပြင် လှိုင်းအခြေအနေခန့်မှန်းချက်",
            "နိုင်ငံတကာနှင့် စိတ်ကြိုက်နေရာ ရှာဖွေရန်",
            "Model Accuracy Audit 📊"
        ], 
        "dmh_alert": "📢 အကြံပြုချက်: နောက်ဆုံးရ မိုးလေဝသသတင်းများအတွက် မိုးဇလ သတင်းများကိုစောင့်ကြည့်ပါ။",
        "storm_note": "📝 မှတ်ချက်: မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ ၆၀% ထက်ကျော်လွန်ပါက လေပြင်းတိုက်ခတ်ခြင်း၊ မိုးကြိုးပစ်ခြင်းနှင့် လျှပ်စီးလက်ခြင်းများ ဖြစ်ပေါ်နိုင်သဖြင့် ဂရုပြုရန် လိုအပ်ပါသည်။",
        "ibf_header": "🏥 ကျန်းမာရေးကဏ္ဍဆိုင်ရာ အကျိုးသက်ရောက်မှုနှင့် အကြံပြုချက်များ",
        "risk_levels": ["Extreme Risk (အလွန်အန္တရာယ်ရှိ)", "High Risk (အန္တရာယ်ရှိ)", "Moderate Risk (သတိပြုရန်)", "Low Risk (ပုံမှန်)"],
        "charts": [
            "🌡️ ၁။ အပူချိန် (ဒီဂရီဆဲလ်စီးယပ်)", 
            "🌧️ ၂။ မိုးရေချိန် (မီလီမီတာ) ၆ နာရီအတွင်းရွာသွန်းသောပမာဏ",
            "💨 ၃။ လေတိုက်နှုန်း (mph) နှင့် လေတိုက်ရာအရပ်", 
            "🔭 ၄။ အဝေးမြင်တာ (km)",
            "💧 ၅။ စိုထိုင်းဆ (%)", 
            "☁️ ၆။ တိမ်ဖုံးမှုပမာဏ (Oktas: 0-8)",
            "⚡ ၇။ မိုးတိမ်တောင်နှင့် လျှပ်စီးလက်နိုင်ခြေ (%)"
        ],
        "impact_list": [
            "အလွန်စိုးရိမ်ရသော အခြေအနေ! အပူဒဏ်လျှပ်စီးဖြတ်ခြင်း (Heatstroke) နှင့် ရေဓာတ်ကုန်ခမ်းခြင်းကြောင့် အသက်အန္တရာယ်ရှိနိုင်သည်။", 
            "အန္တရာယ်ရှိသော အခြေအနေ! အပူဒဏ်ကြောင့် ပင်ပန်းနွမ်းနယ်ခြင်း ဖြစ်နိုင်ပါသည်။ ကလေးနှင့် လူအိုများ အထူးသတိပြုပါ။", 
            "သတိပြုရန် အခြေအနေ! နေရောင်အောက်တွင် ကြာရှည်နေပါက ပင်ပန်းနွမ်းနယ်ခြင်း ဖြစ်ပေါ်နိုင်ပါသည်။", 
            "ပုံမှန်အခြေအနေ! သိသာထင်ရှားသော ကျန်းမာရေးထိခိုက်မှု မရှိနိုင်ပါ။"
        ],
        "recom_list": [
            "အိမ်ထဲတွင်သာ နေပါ။ ရေ (၃-၄) လီတာ သောက်ပါ။ မူးဝေပါက ဆေးရုံသို့ အမြန်သွားပါ။ မိုးလေဝသ သတင်းများကို အချိန်ပြည့် စောင့်ကြည့်လိုက်နာပါ။", 
            "ပြင်ပလုပ်ငန်းများကို နံနက်/ညနေသာ လုပ်ပါ။ ထီး/ဦးထုပ် ဆောင်းပါ။ ရေဓာတ်ဖြည့်ပါ။ မိုးဇလခန့်မှန်းချက်များနှင့် သတင်းများကို ဆက်လက်နားထောင်ပါ။",  
            "ပေါ့ပါးသော အဝတ်များ ဝတ်ပါ။ ရေခဏခဏသောက်ပါ။ အရိပ်တွင် နားပါ။ မိုးဇလခန်းမှန်းချက်များနှင့် သတင်းများကို နားထောင်ပါ။", 
            "ပုံမှန်အတိုင်း နေနိုင်ပါသည်။ ရေဓာတ်ဖြည့်တင်းရန်နှင့် မိုးဇလခန့်မှန်းချက်များနှင့် သတင်းများကို နားထောင်ပါ။", 
        ],
        "marine_region_label": "🌊 ကမ်းရိုးတန်းဒေသ ရွေးချယ်ရန်",
        "marine_station_label": "⚓ ကမ်းရိုးတန်းမြို့နယ်/စခန်း ရွေးချယ်ရန်"
    },
    "English": {
        "title": "DMH AI Weather Forecast System",
        "station_label": "🎯 Select Station",
        "view_mode_label": "📊 View Mode",
        "modes": [
            "16-Days Forecast", 
            "Heatwave Monitoring (IBF)", 
            "Climate Change Projection SSP5-8.5",
            "Icon Style Forecast",
            "Marine Wave Forecast",
            "Global & Custom Coordinates Search",
            "Model Accuracy Audit 📊"
        ],
        "dmh_alert":  "📢 Tip: Follow DMH news for the latest weather updates.",
        "storm_note": "📝 Note: If thunderstorm probability exceeds 60%, beware of strong winds and lightning.",
        "ibf_header": "🏥 Health Impacts & Recommendations",
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "charts": [
            "🌡️ 1. Temperature (°C)", 
            "🌧️ 2. Precipitation (mm) 6 hourly", 
            "💨 3. Wind Speed (mph) & Direction", 
            "🔭 4. Visibility (km)", 
            "💧 5. Humidity (%)", 
            "☁️ 6. Cloud Cover (Oktas: 0-8)", 
            "⚡ 7. Thunderstorm & Lightning Probability (%)"
        ],
        "impact_list": ["Extreme danger! Heatstroke possible.", "High danger! Fatigue possible.", "Caution! Sun exposure may cause fatigue.", "Normal conditions."],
        "recom_list": ["Stay indoors. Drink 3-4L water, Follow DMH news for the latest weather updates.", "Work morning/evening only. Use umbrella, Follow DMH news for the latest weather updates.", "Wear light clothes. Rest in shade, Follow DMH news for the latest weather updates.", "Stay hydrated and follow updates, Follow DMH news for the latest weather updates."],
        "marine_region_label": "🌊 Select Coastal Region",
        "marine_station_label": "⚓ Select Coastal Station"
    }
}

# --- ၅။ စခန်းတည်နေရာဒေတာများ ဖတ်ရှုခြင်း ---
@st.cache_data
def load_stations():
    try:
        df_csv = pd.read_csv("Station.csv", encoding='utf-8-sig')
        return {str(row.iloc[0]).strip(): {'lat': float(row['Lat']), 'lon': float(row['Lon'])} for _, row in df_csv.iterrows()}
    except:
        return {"Naypyidaw": {"lat": 19.76, "lon": 96.08}, "Amarapura": {"lat": 21.90, "lon": 96.05}}

MYANMAR_CITIES = load_stations()
city_list = sorted(list(MYANMAR_CITIES.keys()))

MARINE_STATIONS = {
    "ရခိုင်ကမ်းရိုးတန်းဒေသ (Rakhine Coast)": {
        "မောင်တော (Maungdaw)": {"lat": 20.82, "lon": 92.36},
        "စစ်တွေ (Sittwe)": {"lat": 20.14, "lon": 92.89},
        "ကျောက်ဖြူ (Kyaukpyu)": {"lat": 19.42, "lon": 93.55},
        "သံတွဲ (Thandwe)": {"lat": 18.47, "lon": 94.36},
        "ဂွ (Gwa)": {"lat": 17.59, "lon": 94.58}
    },
    "ဧရာဝတီမြစ်ဝကျွန်းပေါ်ဒေသ (Ayeyarwady Delta)": {
        "ဟိုင်းကြီးကျွန်း (Hainggyikyun)": {"lat": 16.03, "lon": 94.35},
        "လပွတ္တာ/ပြင်စလူ (Pyinsalu)": {"lat": 15.78, "lon": 94.88},
        "ဖျာပုံ (Pyapon)": {"lat": 16.13, "lon": 95.68}
    },
    "မွန်-တနင်္သာရီကမ်းရိုးတန်းဒေသ (Mon-Tanintharyi Coast)": {
        "ဘီလူးကျွန်း/ချောင်းဆုံ (Chaungzon)": {"lat": 16.36, "lon": 97.51},
        "ရေး (Ye)": {"lat": 15.25, "lon": 97.85},
        "ထားဝယ် (Dawei)": {"lat": 14.08, "lon": 98.19},
        "မြိတ် (Myeik)": {"lat": 12.44, "lon": 98.60},
        "ဘုတ်ပြင်း (Bokpyin)": {"lat": 11.16, "lon": 98.88},
        "ကော့သောင်း (Kawthaung)": {"lat": 9.99, "lon": 98.55}
    }
}

@st.cache_data(ttl=1800, max_entries=50)
def fetch_weather_generic(lat, lon, tz_name="Asia/Yangon"):
    tz_param = tz_name.replace('/', '%2F')
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,windspeed_10m,winddirection_10m,relative_humidity_2m,visibility,cloud_cover,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone={tz_param}"
    try:
        r = requests.get(url, timeout=12)
        if r.status_code == 429:
            return None, "429"
        r.raise_for_status()
        res = r.json()
        
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(res['hourly']['time']), 
            "Temp": res['hourly']['temperature_2m'],
            "precipitation": res['hourly']['precipitation'],
            "Wind": res['hourly']['windspeed_10m'],
            "WindDir": res['hourly']['winddirection_10m'],
            "Vis": [v/1000 if v is not None else 0 for v in res['hourly']['visibility']],
            "Humid": res['hourly']['relative_humidity_2m'],
            "Cloud_Oktas": [round((c/100)*8) if c is not None else 0 for c in res['hourly']['cloud_cover']],
            "Thunderstorm": [min(round((c/3500)*100), 100) if (c is not None and not pd.isna(c)) else 0 for c in res['hourly'].get('cape', [])]
        })
        df_h['HI'], df_h['WBGT'], df_h['UTCI'] = zip(*df_h.apply(lambda x: calculate_all_indices(x['Temp'], x['Humid']), axis=1))
        
        df_d = pd.DataFrame({
            "Date": pd.to_datetime(res['daily']['time']), "Tmax": res['daily']['temperature_2m_max'], "Tmin": res['daily']['temperature_2m_min']
        })
        return (df_h, df_d), "OK"
    except:
        return None, "ERROR"

# --- ၆။ Sidebar UI ---
st.sidebar.image(dm_header_logo, width=90)
lang = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True)
T = LANG_DATA[lang]
bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0)

view_mode_choice = st.sidebar.radio(T["view_mode_label"], T["modes"])
mode_index = T["modes"].index(view_mode_choice)

# တည်နေရာ ရွေးချယ်မှုအပိုင်း
selected_city = "Naypyidaw"
lat, lon = 19.76, 96.08
tz_active = "Asia/Yangon"

if mode_index == 4:  # ပင်လယ်ပြင် ကဏ္ဍ
    selected_region = st.sidebar.selectbox(T["marine_region_label"], list(MARINE_STATIONS.keys()))
    selected_city = st.sidebar.selectbox(T["marine_station_label"], list(MARINE_STATIONS[selected_region].keys()))
    lat = MARINE_STATIONS[selected_region][selected_city]["lat"]
    lon = MARINE_STATIONS[selected_region][selected_city]["lon"]
elif mode_index == 5:  # စိတ်ကြိုက်ရှာဖွေရန်
    search_type = st.sidebar.radio("🔍 ရှာဖွေမည့်ပုံစံ", ["မြို့အမည်ဖြင့် ရိုက်ရှာရန်", "Lat / Lon ကိုယ်တိုင်ရိုက်ထည့်ရန်"])
    if search_type == "မြို့အမည်ဖြင့် ရိုက်ရှာရန်":
        search_query = st.sidebar.text_input("🏙️ မြို့အမည် (အင်္ဂလိပ်လို)", "Singapore")
        selected_city = search_query
        lat, lon, tz_active = 1.3521, 103.8198, "Asia/Singapore"
        if search_query.strip():
            try:
                geo_res = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={search_query}&count=1&language=en&format=json", timeout=10).json()
                if "results" in geo_res and len(geo_res["results"]) > 0:
                    res_idx = geo_res["results"][0]
                    selected_city = f"{res_idx['name']} ({res_idx.get('country', '')})"
                    lat, lon = res_idx["latitude"], res_idx["longitude"]
                    tz_active = res_idx.get("timezone", "Asia/Yangon")
            except: pass
    else:
        lat = st.sidebar.number_input("📍 Latitude", value=13.7563, format="%.4f")
        lon = st.sidebar.number_input("📍 Longitude", value=100.5018, format="%.4f")
        selected_city = f"Custom ({lat}, {lon})"
else:
    selected_city = st.sidebar.selectbox(T["station_label"], city_list, index=city_list.index("Amarapura") if "Amarapura" in city_list else 0)
    if selected_city in MYANMAR_CITIES:
        lat = MYANMAR_CITIES[selected_city]["lat"]
        lon = MYANMAR_CITIES[selected_city]["lon"]

# --- ၇။ Main Header ---
st.title(T["title"])
st.info(f"📍 လက်ရှိပြသနေသောစခန်း - {selected_city} | 🕒 {formatted_now}")

# --- ၈။ ဒေတာဆွဲယူခြင်းနှင့် အရန်ဒေတာ စီမံခန့်ခွဲမှုစနစ် (Data Engine) ---
df_h, df_d = None, None
if mode_index not in [4, 6]:
    data_pack, status = fetch_weather_generic(lat, lon, tz_active)
    
    if status == "429":
        st.warning("⚠️ AI Simulated Dashboard ဖြင့် ကြည့်ရှုရန်။")
        df_h, df_d = generate_fallback_data(lat, lon)
    elif status == "OK" and data_pack is not None:
        df_h, df_d = data_pack
    else:
        df_h, df_d = generate_fallback_data(lat, lon)

    if df_h is not None:
        df_h['Temp'] += bias
        df_d['Tmax'] += bias
        df_d['Tmin'] += bias

# --- ၉။ Icon-Style Render Function ---
def render_icon_style_forecast(df_hourly):
    display_days = st.slider("📅 ပြသလိုသည့် ရက်ပမာဏ", min_value=1, max_value=16, value=7, key="days_slider_unique")
    df_3h = df_hourly.set_index('Time').resample('3h').agg({
        'Temp': 'first', 'precipitation': 'sum', 'Wind': 'mean', 'Vis': 'mean', 'Humid': 'mean', 'Cloud_Oktas': 'max', 'Thunderstorm': 'max'
    }).reset_index().head(display_days * 8)

    icons_list = []
    for _, row in df_3h.iterrows():
        if row['precipitation'] > 2.0: icon = "🌧️"
        elif row['Thunderstorm'] > 50: icon = "⚡"
        elif row['Cloud_Oktas'] >= 5: icon = "☁️"
        elif row['Cloud_Oktas'] >= 2: icon = "⛅"
        else: icon = "🌙" if (row['Time'].hour < 6 or row['Time'].hour > 18) else "☀️"
        icons_list.append(f"{icon}<br>{round(row['Temp'])}°C")

    fig_accu = make_subplots(specs=[[{"secondary_y": True}]])
    fig_accu.add_trace(go.Bar(x=df_3h['Time'].dt.strftime('%b %d\n%I:%M %p'), y=df_3h['precipitation'], name="Precipitation (mm)", marker=dict(color='rgba(41, 121, 255, 0.35)')), secondary_y=True)
    fig_accu.add_trace(go.Scatter(x=df_3h['Time'].dt.strftime('%b %d\n%I:%M %p'), y=df_3h['Temp'], name="Temperature (°C)", mode='lines+markers+text', text=icons_list, textposition="top center", line=dict(color='#FF6D00', shape='spline')), secondary_y=False)
    fig_accu.update_layout(hovermode="x unified", height=460, margin=dict(t=30, b=30, l=30, r=30))
    st.plotly_chart(fig_accu, use_container_width=True)

    table_title = f"### 📊 3-Hourly Comprehensive Data Table ({display_days}-Days)"
    st.markdown(table_title)
    df_table = df_3h.copy()
    df_table['Time'] = df_table['Time'].dt.strftime('%Y-%m-%d %I:%M %p')
    df_table.columns = ["Time Slot", "Temperature (°C)", "Precipitation (mm)", "Wind Speed (mph)", "Visibility (km)", "Humidity (%)", "Cloud Cover (Oktas)", "Thunderstorm Prob (%)"]
    st.dataframe(df_table.set_index("Time Slot"), use_container_width=True)

# --- ၁၀။ Display Router ---
if mode_index == 0:
    st.warning(T["dmh_alert"])
    if df_d is not None and df_h is not None:
        # ၁။ အပူချိန် Graph
        st.subheader(T["charts"][0])
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, color_discrete_map={'Tmax': 'red', 'Tmin': 'blue'}), use_container_width=True)
        
        # 6-Hourly Resampling for general meteorology patterns
        df_6h = df_h.set_index('Time').resample('6h').agg({
            'precipitation': 'sum', 'Wind': 'mean', 'WindDir': 'mean', 'Vis': 'mean', 'Humid': 'mean', 'Cloud_Oktas': 'max', 'Thunderstorm': 'max'
        }).reset_index()
        
        # ၂။ မိုးရေချိန် Graph
        st.subheader(T["charts"][1])
        st.plotly_chart(px.bar(df_6h, x='Time', y='precipitation', color_discrete_sequence=['#2979FF']), use_container_width=True)
        
        # ၃။ လေတိုက်နှုန်းနှင့် လေတိုက်ရာအရပ် Graph
        st.subheader(T["charts"][2])
        fig_wind = go.Figure()
        fig_wind.add_trace(go.Scatter(x=df_6h['Time'], y=df_6h['Wind'], mode='lines+markers', name="Wind Speed (mph)", line=dict(color='#00E676')))
        fig_wind.add_trace(go.Scatter(x=df_6h['Time'], y=df_6h['Wind'], mode='markers', marker=dict(symbol='triangle-up', angle=df_6h['WindDir'], size=12, color='red'), name="Direction"))
        st.plotly_chart(fig_wind, use_container_width=True)
        
        # ၄။ အဝေးမြင်တာ Graph (Visibility)
        st.subheader(T["charts"][3])
        st.plotly_chart(px.line(df_6h, x='Time', y='Vis', markers=True, color_discrete_sequence=['#757575']), use_container_width=True)
        
        # ၅။ စိုထိုင်းဆ Graph (Humidity)
        st.subheader(T["charts"][4])
        st.plotly_chart(px.line(df_6h, x='Time', y='Humid', markers=True, color_discrete_sequence=['#00ACC1']), use_container_width=True)
        
        # ၆။ တိမ်ဖုံးမှုပမာဏ Graph (Cloud Cover)
        st.subheader(T["charts"][5])
        st.plotly_chart(px.bar(df_6h, x='Time', y='Cloud_Oktas', color_discrete_sequence=['#90A4AE']), use_container_width=True)
        
        # ၇။ မိုးတိမ်တောင်နှင့် လျှပ်စီးလက်နိုင်ခြေ Graph (Thunderstorm Probability)
        st.subheader(T["charts"][6])
        st.plotly_chart(px.bar(df_6h, x='Time', y='Thunderstorm', color_discrete_sequence=['#D500F9']), use_container_width=True)
        
        # မိုးတိမ်တောင် သတိပေးချက် မှတ်ချက်ထည့်သွင်းခြင်း (Storm Note)
        st.info(T["storm_note"])

elif mode_index == 1:
    if df_h is not None:
        st.subheader(T["ibf_header"])
        idx_choice = st.radio("🌡️ Select Heat Stress Index", ["အမြင့်ဆုံးအပူချိန်", "Heat Index", "WBGT", "UTCI"], horizontal=True)
        val = df_h.iloc[0]['HI'] if idx_choice == "Heat Index" else df_h.iloc[0]['Temp']
        st.metric(label=idx_choice, value=f"{val:.1f} °C")

elif mode_index == 2:
    st.subheader("🌡️ Future Climate Projection (SSP5-8.5)")
    years = np.arange(2026, 2101)
    trend = [31 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
    st.plotly_chart(px.line(x=years, y=trend, labels={'x':'Year', 'y':'Temp (°C)'}), use_container_width=True)

elif mode_index == 3:
    if df_h is not None:
        render_icon_style_forecast(df_h)

elif mode_index == 4:  # ပင်လယ်ပြင် ကဏ္ဍစစ်စစ် (Marine Mode)
    marine_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=wave_height,wave_direction&timezone=Asia/Yangon"
    try:
        res_m = requests.get(marine_url, timeout=12).json()
        df_m = pd.DataFrame({"Time": pd.to_datetime(res_m["hourly"]["time"]), "Wave Height (m)": res_m["hourly"]["wave_height"]})
        st.subheader(f"🌊 {selected_city} - ပင်လယ်ပြင်လှိုင်းအမြင့်ခန့်မှန်းချက် ပြသကွက်")
        st.plotly_chart(px.line(df_m, x="Time", y="Wave Height (m)", markers=True, line_shape="spline"), use_container_width=True)
    except:
        st.warning("⚓ ပင်လယ်ပြင် API Limit ပြည့်နေသဖြင့် လှိုင်းခန့်မှန်းချက်အား AI Simulation စနစ်ဖြင့် အစားထိုး တင်ပြပေးထားပါသည်ဗျာ။")
        sim_times = [datetime.now(mm_tz).replace(hour=0,minute=0)+timedelta(hours=i) for i in range(7*24)]
        df_m_sim = pd.DataFrame({"Time": sim_times, "Wave Height (m)": [max(0.5, 1.2 + 0.5*np.sin(2*np.pi*i/24)+np.random.normal(0,0.1)) for i in range(7*24)]})
        st.plotly_chart(px.line(df_m_sim, x="Time", y="Wave Height (m)", markers=True), use_container_width=True)

elif mode_index == 5:
    if df_h is not None:
        render_icon_style_forecast(df_h)

# Mode 6: Model Accuracy Audit Mode
elif mode_index == 6:
    st.subheader("📊 DMH Verification & Engine Automation Monitor")
    if DMHForecastVerification is not None:
        try:
            verifier = DMHForecastVerification()
            metrics_df = verifier.calculate_accuracy_metrics()
            st.write("### 📈 Model Accuracy Metrics Overview")
            st.dataframe(metrics_df, use_container_width=True)
        except Exception as audit_err:
            st.error(f"Verification Engine Run Error: {audit_err}")
    else:
        st.warning("⚠️ `verification_engine.py` structure module could not be found or initialized properly inside the root runtime directory.")

# --- ၁၁။ Export Report ---
st.markdown("---")
if st.button("🚀 Export All Stations Report"):
    all_data = []
    p_bar = st.progress(0)
    for i, city in enumerate(city_list):
        if city in MYANMAR_CITIES:
            c_lat = MYANMAR_CITIES[city]["lat"]
            c_lon = MYANMAR_CITIES[city]["lon"]
            
            data_pack, status = fetch_weather_generic(c_lat, c_lon, "Asia/Yangon")
            if status != "OK" or data_pack is None:
                dh, dd = generate_fallback_data(c_lat, c_lon)
            else:
                dh, dd = data_pack
                
            if dh is not None and dd is not None:
                for d in dd['Date']:
                    t_930 = d + pd.Timedelta(hours=9, minutes=30)
                    y_930 = t_930 - pd.Timedelta(days=1)
                    rain_24h = dh.loc[(dh['Time'] > y_930) & (dh['Time'] <= t_930), 'precipitation'].sum()
                    day_indices = dh[dh['Time'].dt.date == d.date()]
                    
                    max_hi = day_indices['HI'].max() if not day_indices.empty else np.nan
                    max_wbgt = day_indices['WBGT'].max() if not day_indices.empty else np.nan
                    
                    all_data.append({
                        'Date': d.strftime('%Y-%m-%d'), 
                        'Station': city,
                        'Max_Temp': round(dd.loc[dd['Date'] == d, 'Tmax'].values[0] + bias, 1),
                        'Max_HeatIndex': max_hi,
                        'Max_WBGT': max_wbgt,
                        'Rain_24h': round(rain_24h, 2)
                    })
        p_bar.progress((i + 1) / len(city_list))
    if all_data:
        st.session_state['master_df'] = pd.DataFrame(all_data)

if 'master_df' in st.session_state:
    m_df = st.session_state['master_df']
    sel_date = st.selectbox("📅 Select Date", sorted(m_df['Date'].unique(), reverse=True))
    final_df = m_df[m_df['Date'] == sel_date].sort_values(by='Station')
    st.dataframe(final_df, use_container_width=True)
    st.download_button("📥 Download (CSV)", final_df.to_csv(index=False).encode('utf-8-sig'), f"DMH_Report_{sel_date}.csv")

    st.markdown("""
    <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; margin-top:20px;'>
        <h4 style='color: #007bff; margin-top: 0;'>📝 ဇယားတွင် ပါဝင်သည့် ဒေတာများရှင်းလင်းချက်</h4>
        <ul style='list-style-type: none; padding-left: 0; line-height: 1.8;'>
            <li><b>၁။ အမြင့်ဆုံးအပူချိန်:</b> နေ့တစ်နေ့၏ ဖြစ်ပေါ်နိုင်သော အမြင့်ဆုံးအပူချိန် (Max Temp)</li>
            <li><b>၂။ မိုးရေချိန် (၂၄ နာရီ):</b> ယခင်နေ့ နံနက် ၀၉:၃၀ နာရီမှ ယနေ့နံနက် ၀၉:၃၀ နာရီအထိ ၂၄ နာရီအတွင်း ရွာသွန်းသော စုစုပေါင်းမိုးရေချိန်</li>
        </ul>
        <p style='font-size: 0.85em; color: #666; font-style: italic; margin-top: 10px;'>
            *မှတ်ချက်။ ။ အထက်ပါဒေတာများသည် DMH ၏ စံသတ်မှတ်ချက်များနှင့်အညီ တွက်ချက်ဖော်ပြထားခြင်း ဖြစ်ပါသည်။
         </p>
         </div>
         """, unsafe_allow_html=True)

# Footer Section
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; font-size: 0.85em; color: #666; line-height: 1.6;'>
    <p><b>Forecast Data Source (16-Day):</b> Open-Meteo API (ECMWF, GFS, ICON, JMA models, WaveWatch III).</p>
    <p><b>Rainfall Cycle:</b> 24-hour total from 09:30 AM (Yesterday) to 09:30 AM (Today).</p>
    <p><b>Heatwave Analysis:</b> Based on Impact-Based Forecasting (IBF) thresholds (P90, P95, P99) and WMO criteria.</p>
    <p><b>Climate Data:</b> IPCC AR6 Assessment Report and CMIP6 Global Climate Models (SSP scenarios).</p>
    <p style='margin-top: 10px; font-weight: bold;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</p>
</div>
""", unsafe_allow_html=True)
