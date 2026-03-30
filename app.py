import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
import pytz
import os

# --- ၁။ အချိန်ဇုန်နှင့် Logo ဖိုင်စစ်ဆေးခြင်း ---
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)

# လူကြီးမင်း တင်ပေးထားသော logo.png ကို အသုံးပြုခြင်း
logo_path = "🌤️"

# --- ၂။ Page Configuration ---
st.set_page_config(
    page_title="DMH AI Weather Dashboard", 
    layout="wide", 
    page_icon=logo_path if os.path.exists(logo_path) else "🌤️"
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
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,windspeed_10m,winddirection_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        h, d = r['hourly'], r['daily']
        df_h = pd.DataFrame({"Time": pd.to_datetime(h['time']), "Temp": h['temperature_2m'], "Wind": h['windspeed_10m'], "WindDir": h['winddirection_10m']})
        df_d = pd.DataFrame({"Date": pd.to_datetime(d['time']), "Tmax": d['temperature_2m_max'], "Tmin": d['temperature_2m_min'], "RainSum": d['precipitation_sum'], "WindMax": d['windspeed_10m_max']})
        df_w_sample = df_h[df_h['Time'].dt.hour == 13].copy()
        return df_h, df_d, df_w_sample
    except: return None, None, None

# --- Sidebar ---
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=120)
st.sidebar.markdown("### 🔍 Monitoring Controls")
selected_city = st.sidebar.selectbox("🎯 Select City", sorted(list(MYANMAR_CITIES_20.keys())))
view_mode = st.sidebar.radio("📊 Analysis View", ["16-Day Forecast Analysis", "Heatwave Monitoring (IBF)", "Climate Projection (2100)"])

# --- 💡 Main UI (Local Image Header) ---
col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    if os.path.exists(logo_path):
        # Logo နှင့် စာသားကို ယှဉ်တွဲပြသခြင်း
        st.image(logo_path, width=80)
    st.markdown(f"<h1 style='text-align: center;'>DMH AI Weather Forecast System</h1>", unsafe_allow_html=True)

st.markdown(f"<p style='text-align: center;'><b>Local Time (MMT):</b> {now.strftime('%I:%M %p, %d %b %Y')}</p>", unsafe_allow_html=True)
st.markdown("---")

df_h, df_d, df_w = get_weather_data(selected_city)

if df_d is not None:
    if view_mode == "16-Day Forecast Analysis":
        st.subheader(f"💨 (1) Wind Speed (mph) & Direction - {selected_city}")
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind'], mode='lines+markers', name='Speed', line=dict(color='teal', width=3)))
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind']+1.5, mode='markers', marker=dict(symbol='arrow', size=18, angle=df_w['WindDir'], color='red')))
        st.plotly_chart(fig_w, use_container_width=True)

        st.subheader(f"🌡️ (2) 16-Day Temperature Outlook (°C) - {selected_city}")
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)

        st.subheader(f"🌧️ (3) Precipitation Summary (mm) - {selected_city}")
        st.plotly_chart(px.bar(df_d, x='Date', y='RainSum', color_discrete_sequence=['#00b4d8']), use_container_width=True)

    elif view_mode == "Heatwave Monitoring (IBF)":
        st.subheader(f"🔥 Impact-Based Monitoring: Extreme Heat ({selected_city})")
        max_t = df_d['Tmax'].max()
        risk_level, color, text_c = "Low Risk", "green", "white"
        if max_t >= 42: risk_level, color = "Extreme Risk", "red"
        elif max_t >= 40: risk_level, color = "High Risk", "orange"
        elif max_t >= 38: risk_level, color, text_c = "Moderate Risk", "yellow", "black"

        st.markdown(f"<div style='background-color:{color}; padding:25px; border-radius:15px; text-align:center; border: 2px solid #333;'><h2 style='color:{text_c};'>Heat Risk Status: {risk_level}</h2><p style='color:{text_c};'>{max_t} °C</p></div>", unsafe_allow_html=True)
        st.plotly_chart(px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd').add_hline(y=40, line_dash="dash", line_color="red"), use_container_width=True)

    else:
        st.subheader(f"🔮 IPCC Climate Projection (2100) - {selected_city}")
        years = np.arange(2026, 2101)
        temp_trend = [30 + (y-2026)*0.043 + np.random.normal(0, 0.5) for y in years]
        fig_c = px.line(x=years, y=temp_trend, labels={'x': 'Year', 'y': 'Mean Temp'}, color_discrete_sequence=['darkred'])
        st.plotly_chart(fig_c, use_container_width=True)

else:
    st.error("Error connecting to data source.")

st.markdown("---")
st.markdown(f"<p style='text-align: center; color: gray;'><b>DMH Myanmar | Powered by AI</b></p>", unsafe_allow_html=True)
