import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
import pytz
import os

# --- ၁။ အချိန်ဇုန် ---
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)

# --- ၂။ Logo နှင့် Image ဖိုင်များ ---
dmh_logo_url = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"
water_cycle_img = "image_1.png"

# --- ၃။ Page Configuration ---
st.set_page_config(
    page_title="DMH AI Weather Dashboard", 
    layout="wide", 
    page_icon=dmh_logo_url
)

MYANMAR_CITIES_20 = {
    "Naypyidaw": {"lat": 19.7633, "lon": 96.0785}, "Yangon": {"lat": 16.8661, "lon": 96.1951},
    "Mandalay": {"lat": 21.9747, "lon": 96.0836}, "Bago": {"lat": 17.3333, "lon": 96.4833},
    "Magway": {"lat": 20.1500, "lon": 94.9167}, "Monywa": {"lat": 22.1167, "lon": 95.1333},
    "Pathein": {"lat": 16.7833, "lon": 94.7333}, "Pyay": {"lat": 18.8167, "lon": 95.2167},
    "Taungoo": {"lat": 18.9333, "lon": 96.4333}, "Hinthada": {"lat": 17.6500, "lon": 95.3833},
    "Myitkyina": {"lat": 25.3831, "lon": 97.3964}, "Taunggyi": {"lat": 20.7888, "lon": 97.0333},
    "Mawlamyine": {"lat": 16.4905, "lon": 97.6282}, "Sittwe": {"lat": 20.1436, "lon": 92.8977},
    "Lashio": {"lat": 22.9333, "lon": 97.7500}, "Hpa-An": {"lat": 16.8906, "lon": 97.6333},
    "Loikaw": {"lat": 19.6742, "lon": 97.2093}, "Mindat": {"lat": 21.3748, "lon": 93.9725},
    "Hkamti": {"lat": 25.9977, "lon": 95.6905}, "Dawei": {"lat": 14.0833, "lon": 98.2000}
}

@st.cache_data(ttl=300)
def get_weather_data(city):
    lat, lon = MYANMAR_CITIES_20[city]['lat'], MYANMAR_CITIES_20[city]['lon']
    # Visibility, Humidity, Cloud Cover Data များကို API မှ ထပ်မံတောင်းဆိုထားပါသည်
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,precipitation,windspeed_10m,winddirection_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        h, d = r['hourly'], r['daily']
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(h['time']), 
            "Temp": h['temperature_2m'], 
            "Humidity": h['relative_humidity_2m'],
            "Visibility": np.array(h['visibility']) / 1000, # km သို့ ပြောင်းရန်
            "Cloud": h['cloud_cover'],
            "Wind": h['windspeed_10m'], 
            "WindDir": h['winddirection_10m']
        })
        df_d = pd.DataFrame({"Date": pd.to_datetime(d['time']), "Tmax": d['temperature_2m_max'], "Tmin": d['temperature_2m_min'], "RainSum": d['precipitation_sum']})
        # နေ့လည် ၁ နာရီ ခန့်မှန်းချက် (Graph အကျဉ်းအတွက်)
        df_w_sample = df_h[df_h['Time'].dt.hour == 13].copy()
        return df_h, df_d, df_w_sample
    except: return None, None, None

# --- Sidebar ---
st.sidebar.image(dmh_logo_url, width=120)
if os.path.exists(water_cycle_img):
    st.sidebar.image(water_cycle_img, caption="Hydrological Cycle", width=150)

st.sidebar.markdown("### 🔍 Monitoring Controls")
selected_city = st.sidebar.selectbox("🎯 Select City", sorted(list(MYANMAR_CITIES_20.keys())))
view_mode = st.sidebar.radio("📊 Analysis View", ["16-Day Forecast Analysis", "Heatwave Monitoring (IBF)", "Climate Projection (2100)"])

# --- Main UI Header ---
st.markdown(f"<h1 style='text-align: center;'>DMH AI Weather Forecast System</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'><b>Local Time (MMT):</b> {now.strftime('%I:%M %p, %d %b %Y')}</p>", unsafe_allow_html=True)
st.markdown("---")

df_h, df_d, df_w = get_weather_data(selected_city)

if df_d is not None:
    if view_mode == "16-Day Forecast Analysis":
        # ၁။ Wind Speed
        st.subheader(f"💨 Wind Speed (mph) & Direction - {selected_city}")
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind'], mode='lines+markers', name='Speed', line=dict(color='teal', width=3)))
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind']+1.5, mode='markers', name='Direction', marker=dict(symbol='arrow', size=18, angle=df_w['WindDir'], color='red')))
        st.plotly_chart(fig_w, use_container_width=True)

        # ၂။ Temp Outlook
        st.subheader(f"🌡️ 16-Day Temperature Outlook (°C) - {selected_city}")
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)

        # ၃။ Rain Summary
        st.subheader(f"🌧️ Precipitation Summary (mm) - {selected_city}")
        st.plotly_chart(px.bar(df_d, x='Date', y='RainSum', color_discrete_sequence=['deepskyblue']), use_container_width=True)

        st.markdown("---")
        st.info("💡 **Extended Parameters (Visibility, Humidity, Cloud Cover)**")

        # ၄။ Visibility Graph
        st.subheader(f"🔭 Visibility Analysis (km) - {selected_city}")
        fig_v = px.line(df_h, x='Time', y='Visibility', line_shape='spline', color_discrete_sequence=['#2ecc71'])
        fig_v.update_layout(yaxis_title="Visibility (km)")
        st.plotly_chart(fig_v, use_container_width=True)

        # ၅။ Humidity Graph
        st.subheader(f"💧 Relative Humidity (%) - {selected_city}")
        fig_hu = px.area(df_h, x='Time', y='Humidity', color_discrete_sequence=['#3498db'])
        fig_hu.update_layout(yaxis_title="Humidity (%)")
        st.plotly_chart(fig_hu, use_container_width=True)

        # ၆။ Cloud Cover Graph
        st.subheader(f"☁️ Cloud Cover Percentage (%) - {selected_city}")
        fig_c = px.bar(df_h, x='Time', y='Cloud', color='Cloud', color_continuous_scale='Blues')
        fig_c.update_layout(yaxis_title="Cloud Cover (%)")
        st.plotly_chart(fig_c, use_container_width=True)

    elif view_mode == "Heatwave Monitoring (IBF)":
        st.subheader(f"🔥 Heatwave Monitoring - {selected_city}")
        max_t = df_d['Tmax'].max()
        risk_color = "red" if max_t >= 40 else "orange" if max_t >= 38 else "green"
        st.markdown(f"<div style='background-color:{risk_color}; padding:20px; border-radius:10px; text-align:center;'><h2>Max Temp: {max_t} °C</h2></div>", unsafe_allow_html=True)
        st.plotly_chart(px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd'), use_container_width=True)

    else:
        st.subheader(f"🔮 Future Climate Projection (2100) - {selected_city}")
        years = np.arange(2026, 2101)
        temp_trend = [30 + (y-2026)*0.043 + np.random.normal(0, 0.5) for y in years]
        st.plotly_chart(px.line(x=years, y=temp_trend, labels={'y':'Mean Temp'}, color_discrete_sequence=['darkred']), use_container_width=True)

else:
    st.error("Data source unavailable.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>DMH Myanmar | AI Forecast System</p>", unsafe_allow_html=True)
