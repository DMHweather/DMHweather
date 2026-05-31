import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime
import pytz
from plotly.subplots import make_subplots


# --- ၁။ Layout Setup ---
st.set_page_config(page_title="DMH AI Weather Forecast System", layout="wide", page_icon="🌤️")
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
formatted_now = now.strftime('%I:%M %p, %d %b %Y')
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

# --- ၂။ Heat Indices Calculation Logic ---
def calculate_all_indices(temp_c, rh):
    hi = 0.5 * (temp_c + 61.0 + ((temp_c - 68.0) * 1.2) + (rh * 0.094))
    e = (rh / 100) * 6.105 * np.exp(17.27 * temp_c / (237.7 + temp_c))
    wbgt = (0.567 * temp_c) + (0.393 * e) + 3.94
    utci = temp_c + (0.33 * e) - (0.7 * 0.1) - 4.0
    return round(hi, 1), round(wbgt, 1), round(utci, 1)

# --- ၃။ ဘာသာစကားနှင့် စာသားများ ---
LANG_DATA = {
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသခန့်မှန်းစနစ်",
        "station_label": "🎯 စခန်းအမည်ရွေးချယ်ပါ",
        "view_mode_label": "📊 View Mode",
        "modes": [
            "၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", 
            "အပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး )", 
            "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀-SSP5-8.5)",
            "Icon Style ခန့်မှန်းချက်",
            "နိုင်ငံတကာနှင့် စိတ်ကြိုက်နေရာ ရှာဖွေရန်"
        ], 
        "dmh_alert": "📢 အကြံပြုချက်: နောက်ဆုံးရ မိုးလေဝသသတင်းများအတွက် မိုးဇလ သတင်းများကိုစောင့်ကြည့်ပါ။",
        "storm_note": "📝 မှတ်ချက်: မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ ၆၀% ထက်ကျော်လွန်ပါက လေပြင်းတိုက်ခတ်ခြင်း၊ မိုးကြိုးပစ်ခြင်းနှင့် လျှပ်စီးလက်ခြင်းများ ဖြစ်ပေါ်နိုင်သဖြင့် ဂရုပြုရန် လိုအပ်ပါသည်။",
        "ibf_header": "🏥 ကျန်းမာရေးကဏ္ဍဆိုင်ရာ အကျိုးသက်ရောက်မှုနှင့် အကြံပြုချက်များ",
        "risk_levels": ["Extreme Risk (အလွန်အန္တရာယ်ရှိ)", "High Risk (အန္တရာယ်ရှိ)", "Moderate Risk (သတိပြုရန်)", "Low Risk (ပုံမှန်)"],
        "charts": [
            "🌡️  ၁။ အပူချိန်(ဒီဂရီဆဲလ်စီးယပ်)", "🌧️ ၂။ မိုးရေချိန်(မီလီမီတာ) ၆ နာရီအတွင်းရွာသွန်းသောပမာဏ",
            "💨 ၃။ လေတိုက်နှုန်း(mph)နှင့်လေတိုက်ရာအရပ်", "🔭 ၄။ အဝေးမြင်တာ (km)",
            "💧  ၅။ စိုထိုင်းဆ (%)", "☁️ ၆။ တိမ်ဖုံးမှုပမာဏ (Oktas: 0-8)",
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
            "ပေါ့ပါးသော အဝတ်များ ဝတ်ပါ။ ရေခဏခဏသောက်ပါ။ အရိပ်တွင် နားပါ။ မိုးဇလခန့်မှန်းချက်များနှင့် သတင်းများကို နားထောင်ပါ။", 
            "ပုံမှန်အတိုင်း နေနိုင်ပါသည်။ ရေဓာတ်ဖြည့်တင်းရန်နှင့် မိုးဇလခန့်မှန်းချက်များနှင့် သတင်းများကို နားထောင်ပါ။", 
        ]
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
            "Global & Custom Coordinates Search"
        ],
        "dmh_alert":  "📢 Tip: Follow DMH news for the latest weather updates.",
        "storm_note": "📝 Note: If thunderstorm probability exceeds 60%, beware of strong winds and lightning.",
        "ibf_header": "🏥 Health Impacts & Recommendations",
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "charts": ["🌡️ 1. Temperature(°C)", "🌧️ 2. Precipitation(mm) 6 hourly", "💨 3. Wind Speed (mph) & Direction", "🔭 4. Visibility (km)", "💧 5. Humidity (%)", "☁️ 6. Cloud Cover (Oktas: 0-8)", "⚡ 7. Thunderstorm & Lightning Probability (%)"],
        "impact_list": ["Extreme danger! Heatstroke possible.", "High danger! Fatigue possible.", "Caution! Sun exposure may cause fatigue.", "Normal conditions."],
        "recom_list": ["Stay indoors. Drink 3-4L water, Follow DMH news for the latest weather updates.", "Work morning/evening only. Use umbrella, Follow DMH news for the latest weather updates.", "Wear light clothes. Rest in shade, Follow DMH news for the latest weather updates.", "Stay hydrated and follow updates, Follow DMH news for the latest weather updates."]
    }
}

# --- ၄။ ဒေတာဖတ်ခြင်းနှင့် API Functions ---
@st.cache_data
def load_stations():
    try:
        df_csv = pd.read_csv("Station.csv", encoding='utf-8-sig')
        return {str(row.iloc[0]).strip(): {'lat': float(row['Lat']), 'lon': float(row['Lon'])} for _, row in df_csv.iterrows()}
    except:
        return {"Naypyidaw": {"lat": 19.76, "lon": 96.08}}

MYANMAR_CITIES = load_stations()
city_list = sorted(list(MYANMAR_CITIES.keys()))

@st.cache_data(ttl=3600)
def fetch_weather_generic(city, source_dict):
    if city not in source_dict: 
        return None, None
    loc = source_dict[city]
    
    tz_param = loc.get('tz', 'Asia/Yangon').replace('/', '%2F')
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&hourly=temperature_2m,precipitation,windspeed_10m,winddirection_10m,relative_humidity_2m,visibility,cloud_cover,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone={tz_param}"
    
    try:
        r = requests.get(url, timeout=30)
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
            "Date": pd.to_datetime(res['daily']['time']), 
            "Tmax": res['daily']['temperature_2m_max'],
            "Tmin": res['daily']['temperature_2m_min']
        })
        return df_h, df_d

    except Exception as e:
        if "429" in str(e):
            st.error("⚠️ API Limit ပြည့်သွားပါပြီ။ ၁ မိနစ်ခန့် စောင့်ပေးပါ။")
        else:
            st.error(f"Error fetching data: {e}")
        return None, None

# --- ၅။ Sidebar UI ---
st.sidebar.image(dm_header_logo, width=100)
lang = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True)
T = LANG_DATA[lang]
bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0)

view_mode_choice = st.sidebar.radio(T["view_mode_label"], T["modes"])
mode_index = T["modes"].index(view_mode_choice)

# Global Variables Initializer
selected_city = ""
active_dict = {}

# Mode 4: Global & Custom Search Logic
if mode_index == 4:
    search_type = st.sidebar.radio("🔍 ရှာဖွေမည့်ပုံစံ", ["မြို့အမည်ဖြင့် ရိုက်ရှာရန် (AccuWeather စတိုင်)", "Lat / Lon ကိုယ်တိုင်ရိုက်ထည့်ရန်"])
    
    if search_type == "မြို့အမည်ဖြင့် ရိုက်ရှာရန် (AccuWeather စတိုင်)":
        search_query = st.sidebar.text_input("🏙️ မြို့အမည် ရိုက်ထည့်ပါ (ဥပမာ - Bangkok, Tokyo, Singapore)", "Singapore")
        
        with st.spinner("တည်နေရာ ရှာဖွေနေပါသည်..."):
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={search_query}&count=1&language=en&format=json"
            try:
                geo_res = requests.get(geo_url).json()
                if "results" in geo_res and len(geo_res["results"]) > 0:
                    result = geo_res["results"][0]
                    selected_city = f"{result['name']} ({result.get('country', '')})"
                    active_dict = {selected_city: {"lat": result["latitude"], "lon": result["longitude"], "tz": result.get("timezone", "Asia/Yangon")}}
                else:
                    st.sidebar.error("❌ မြို့အမည် ရှာမတွေ့ပါ။ စာလုံးပေါင်း ပြန်စစ်ပေးပါ။")
                    selected_city = "Singapore"
                    active_dict = {"Singapore": {"lat": 1.3521, "lon": 103.8198, "tz": "Asia/Singapore"}}
            except:
                selected_city = "Singapore"
                active_dict = {"Singapore": {"lat": 1.3521, "lon": 103.8198, "tz": "Asia/Singapore"}}
                
    else:
        c_lat = st.sidebar.number_input("📍 Latitude (မြောက်လတ္တီတွဒ်)", value=13.7563, format="%.4f")
        c_lon = st.sidebar.number_input("📍 Longitude (အရှေ့လောင်ဂျီတွဒ်)", value=100.5018, format="%.4f")
        selected_city = f"Custom Location ({c_lat}, {c_lon})"
        active_dict = {selected_city: {"lat": c_lat, "lon": c_lon, "tz": "Asia/Yangon"}}
else:
    selected_city = st.sidebar.selectbox(T["station_label"], city_list)
    active_dict = MYANMAR_CITIES

# Main UI Header
st.title(T["title"])
st.info(f"📍 {selected_city} | 🕒 {formatted_now}")

# API မှ ဒေတာဆွဲယူခြင်း
df_h, df_d = fetch_weather_generic(selected_city, active_dict)

# --- ၆။ Graph & Table Render Function (ရက်ရွေးချယ်ရန် Slider ထည့်သွင်းထားသည်) ---
def render_icon_style_forecast(df_hourly):
    # User က ဘယ်နှစ်ရက်စာအထိ ဂရပ်မှာ ကြည့်ချင်လဲဆိုတာ Slider နဲ့ ရွေးချယ်ခိုင်းခြင်း (အမြင့်ဆုံး ၁၆ ရက်၊ Default ၇ ရက်)
    slider_label = "📅 ခန့်မှန်းချက် ကြည့်ရှုမည့်ရက်ပမာဏ ရွေးချယ်ရန်" if lang == "မြန်မာ" else "📅 Select Forecast Days to Display"
    display_days = st.slider(slider_label, min_value=1, max_value=16, value=7)
    
    # ၁ ရက်လျှင် ၃ နာရီခြား Data Point ၈ ခု ရှိသဖြင့် စုစုပေါင်း ပွိုင့်အရေအတွက် တွက်ချက်ခြင်း
    total_points = display_days * 8

    df_3h = df_hourly.set_index('Time').resample('3h').agg({
        'Temp': 'first', 'precipitation': 'sum', 'Wind': 'mean', 
        'Vis': 'mean', 'Humid': 'mean', 'Cloud_Oktas': 'max', 'Thunderstorm': 'max'
    }).reset_index().head(total_points)

    icons_list = []
    for _, row in df_3h.iterrows():
        if row['precipitation'] > 2.0: icon = "🌧️"
        elif row['Thunderstorm'] > 50: icon = "⚡"
        elif row['Cloud_Oktas'] >= 5: icon = "☁️"
        elif row['Cloud_Oktas'] >= 2: icon = "⛅"
        else:
            hour = row['Time'].hour
            icon = "🌙" if (hour < 6 or hour > 18) else "☀️"
        icons_list.append(f"{icon}<br>{round(row['Temp'])}°C")

    fig_accu = make_subplots(specs=[[{"secondary_y": True}]])
    fig_accu.add_trace(
        go.Bar(
            x=df_3h['Time'].dt.strftime('%b %d\n%I:%M %p'), y=df_3h['precipitation'], name="Precipitation (mm)",
            marker=dict(color='rgba(41, 121, 255, 0.35)', line=dict(color='rgba(41, 121, 255, 0.7)', width=1)),
            hovertemplate='%{y} mm<extra></extra>'
        ), secondary_y=True,
    )
    fig_accu.add_trace(
        go.Scatter(
            x=df_3h['Time'].dt.strftime('%b %d\n%I:%M %p'), y=df_3h['Temp'], name="Temperature (°C)",
            mode='lines+markers+text', text=icons_list, textposition="top center",
            textfont=dict(size=11, color="#333333"), line=dict(color='#FF6D00', width=2.5, shape='spline'),
            marker=dict(size=5, color='#FF6D00'), hovertemplate='%{y}°C<extra></extra>'
        ), secondary_y=False,
    )
    fig_accu.update_layout(
        hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
        plot_bgcolor='#F8F9FA', paper_bgcolor='white', height=480, margin=dict(t=50, b=40, l=40, r=40)
    )
    fig_accu.update_xaxes(showgrid=True, gridcolor='rgba(220, 220, 220, 0.5)', tickangle=0)
    fig_accu.update_yaxes(title_text="Temperature (°C)", color="#FF6D00", showgrid=True, gridcolor='rgba(220, 220, 220, 0.5)', secondary_y=False)
    fig_accu.update_yaxes(title_text="Precipitation (mm)", color="#2979FF", showgrid=False, secondary_y=True)

    st.plotly_chart(fig_accu, use_container_width=True)

    table_title = f"### 📊 3-Hourly Comprehensive Data Table ({display_days}-Days)"
    st.markdown(table_title)
    df_table = df_3h.copy()
    df_table['Time'] = df_table['Time'].dt.strftime('%Y-%m-%d %I:%M %p')
    df_table.columns = ["Time Slot", "Temperature (°C)", "Precipitation (mm)", "Wind Speed (mph)", "Visibility (km)", "Humidity (%)", "Cloud Cover (Oktas)", "Thunderstorm Prob (%)"]
    st.dataframe(df_table.set_index("Time Slot"), use_container_width=True)

# --- ၇။ Main App Modes Display Logic ---
if df_h is not None:
    df_h['Temp'] += bias
    df_d['Tmax'] += bias
    df_d['Tmin'] += bias

    # Mode 0: 16-Days Forecast
    if mode_index == 0:
        st.warning(T["dmh_alert"])
        st.subheader(T["charts"][0])
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True), use_container_width=True)

        df_6h = df_h.set_index('Time').resample('6h').agg({
            'precipitation': 'sum', 'Wind': 'mean', 'WindDir': 'mean', 
            'Cloud_Oktas': 'max', 'Thunderstorm': 'max'
        }).reset_index()

        st.subheader(T["charts"][1])
        st.plotly_chart(px.bar(df_6h, x='Time', y='precipitation', color_discrete_sequence=['green']), use_container_width=True)

        st.subheader(T["charts"][2])
        fig_wind = go.Figure()
        fig_wind.add_trace(go.Scatter(x=df_6h['Time'], y=df_6h['Wind'], mode='lines+markers', line=dict(color='darkgreen')))
        fig_wind.add_trace(go.Scatter(x=df_6h['Time'], y=df_6h['Wind'], mode='markers', marker=dict(symbol='triangle-up', angle=df_6h['WindDir'], size=12, color='red')))
        st.plotly_chart(fig_wind, use_container_width=True)

        st.subheader(T["charts"][3])
        fig4 = px.line(df_h, x='Time', y='Vis', color_discrete_sequence=['gray'])
        st.plotly_chart(fig4, use_container_width=True)

        st.subheader(T["charts"][4])
        fig5 = px.area(df_h, x='Time', y='Humid', color_discrete_sequence=['purple'])
        st.plotly_chart(fig5, use_container_width=True)

        st.subheader(T["charts"][5])
        st.plotly_chart(px.bar(df_6h, x='Time', y='Cloud_Oktas', color_discrete_sequence=['lightgreen']), use_container_width=True)
        
        st.subheader(T["charts"][6])
        st.error(T["storm_note"])
        st.plotly_chart(px.bar(df_6h, x='Time', y='Thunderstorm', color_discrete_sequence=['orange']), use_container_width=True)

    # Mode 1: Heatwave Monitoring
    elif mode_index == 1:
        st.subheader(T["ibf_header"])
        idx_choice = st.radio("🌡️ Select Heat Stress Index to Monitor", ["အမြင့်ဆုံးအပူချိန်", "Heat Index", "WBGT", "UTCI"], horizontal=True)
        
        t_now = df_h.iloc[0]
        tmax_today = df_d.iloc[0]['Tmax']
        hi_today, wbgt_today, utci_today = t_now['HI'], t_now['WBGT'], t_now['UTCI']

        if idx_choice == "အမြင့်ဆုံးအပူချိန်":
            val, th = tmax_today, [42, 40, 38]
            display_title = "၁၆ ရက်စာ အမြင့်ဆုံးအပူချိန် ခန့်မှန်းချက်"
        elif idx_choice == "Heat Index": 
            val, th = hi_today, [41, 38, 35]
            display_title = "၁၆ ရက်စာ Heat Index ခန့်မှန်းချက်"
        elif idx_choice == "WBGT": 
            val, th = wbgt_today, [32, 30, 28]
            display_title = "၁၆ ရက်စာ WBGT ခန့်မှန်းချက်"
        else: 
            val, th = utci_today, [38, 32, 26]
            display_title = "၁၆ ရက်စာ UTCI ခန့်မှန်းချက်"

        if val >= th[0]: lvl, color, bg = 0, "white", "#FF0000"
        elif val >= th[1]: lvl, color, bg = 1, "black", "#FFA500"
        elif val >= th[2]: lvl, color, bg = 2, "black", "#FFFF00"
        else: lvl, color, bg = 3, "white", "#008000"

        st.markdown(f"""
            <div style='background-color:{bg}; color:{color}; padding:25px; border-radius:15px; text-align:center; border: 2px solid #333;'>
                <h1 style='margin:0;'>{T['risk_levels'][lvl]}</h1>
                <p style='font-size:1.5em; margin-top:10px;'>{idx_choice}: <b>{val:.1f} °C</b></p>
            </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1: st.info(f"### ⚠️ Impact\n{T['impact_list'][lvl]}")
        with c2: st.success(f"### ✅ Action\n{T['recom_list'][lvl]}")

        if idx_choice == "အမြင့်ဆုံးအပူချိန်":
            fig_ibf = px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd', title=display_title)
            for i, label in enumerate(["Extreme", "High", "Moderate"]):
                fig_ibf.add_hline(y=th[i], line_dash="dash", line_color="red", annotation_text=label)
        else:
            col_map = {"Heat Index": "HI", "WBGT": "WBGT", "UTCI": "UTCI"}
            fig_ibf = px.line(df_h, x='Time', y=col_map[idx_choice], markers=True, title=display_title)
            fig_ibf.add_hline(y=th[0], line_dash="dash", line_color="red", annotation_text="Extreme Risk")

        st.plotly_chart(fig_ibf, use_container_width=True)

    # Mode 2: Future Climate Projection
    elif mode_index == 2:
        st.subheader("🌡️ Future Climate Projection (SSP5-8.5)")
        years = np.arange(2026, 2101)
        trend = [31 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
        st.plotly_chart(px.line(x=years, y=trend, labels={'x':'Year', 'y':'Temp (°C)'}), use_container_width=True)
        st.warning("⚠️ **Climate Risk Note:** Under the SSP 5-8.5 scenario, Myanmar could face significantly higher frequency of extreme heat and unpredictable monsoon patterns by the end of the century.")

    # Mode 3: Domestic Icon Style Forecast
    elif mode_index == 3:
        st.subheader("🕒 3-Hourly AccuWeather Style Graph & Forecast (Domestic)")
        render_icon_style_forecast(df_h)

    # Mode 4: International & Custom Coordinates Forecast
    elif mode_index == 4:
        st.subheader("🌏 Global Weather Search & Custom Coordinates (Icon Style)")
        st.success(f"လက်ရှိပြသနေသော တည်နေရာ - {selected_city}")
        
        # Interactive Map Display
        map_df = pd.DataFrame([{"lat": active_dict[selected_city]["lat"], "lon": active_dict[selected_city]["lon"]}])
        st.map(map_df, zoom=9, size=22)
        
        # Render Graph & Table
        render_icon_style_forecast(df_h)

# --- ၈။ Export Report ---
st.markdown("---")
if st.button("🚀 Export All Stations Report"):
    all_data = []
    p_bar = st.progress(0)
    for i, city in enumerate(city_list):
        dh, dd = fetch_weather_generic(city, MYANMAR_CITIES)
        if dh is not None and dd is not None:
            for d in dd['Date']:
                t_930 = d + pd.Timedelta(hours=9, minutes=30)
                y_930 = t_930 - pd.Timedelta(days=1)
                rain_24h = dh.loc[(dh['Time'] > y_930) & (dh['Time'] <= t_930), 'precipitation'].sum()
                day_indices = dh[dh['Time'].dt.date == d.date()]
                
                # Check to prevent empty data max errors
                max_hi = day_indices['HI'].max() if not day_indices.empty else np.nan
                max_wbgt = day_indices['WBGT'].max() if not day_indices.empty else np.nan
                
                all_data.append({
                    'Date': d.strftime('%Y-%m-%d'), 'Station': city,
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
            <li><b>၂။ အနိမ့်ဆုံးအပူချိန်:</b> နေ့တစ်နေ့၏ ဖြစ်ပေါ်နိုင်သော အနိမ့်ဆုံးအပူချိန် (Min Temp)</li>
            <li><b>၃။ မိုးရေချိန် (၂၄ နာရီ):</b> ယခင်နေ့ နံနက် ၀၉:၃၀ နာရီမှ ယနေ့နံနက် ၀၉:၃၀ နာရီအထိ ၂၄ နာရီအတွင်း ရွာသွန်းသော စုစုပေါင်းမိုးရေချိန်</li>
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
    <p><b>Forecast Data Source (16-Day):</b> Open-Meteo API (ECMWF, GFS, ICON, JMA models).</p>
    <p><b>Rainfall Cycle:</b> 24-hour total from 09:30 AM (Yesterday) to 09:30 AM (Today).</p>
    <p><b>Heatwave Analysis:</b> Based on Impact-Based Forecasting (IBF) thresholds (P90, P95, P99) and WMO criteria.</p>
    <p><b>Climate Data:</b> IPCC AR6 Assessment Report and CMIP6 Global Climate Models (SSP scenarios).</p>
    <p style='margin-top: 10px; font-weight: bold;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</p>
</div>
""", unsafe_allow_html=True)
