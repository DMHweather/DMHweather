import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime

# --- ၁။ အချိန်နှင့် ရက်စွဲ ---
now = datetime.now()
current_hour = now.hour

# --- ၂။ Page Configuration ---
st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide", page_icon="🌦️")

# မြို့ကြီး (၂၀) စာရင်း
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

def get_wind_dir_text(deg):
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    return dirs[int((deg + 11.25) / 22.5) % 16]

@st.cache_data(ttl=300)
def get_all_weather_data(city):
    lat, lon = MYANMAR_CITIES_20[city]['lat'], MYANMAR_CITIES_20[city]['lon']
    # နေ့စဉ်ခန့်မှန်းချက်နှင့် နာရီအလိုက်ခန့်မှန်းချက် (၁၆ ရက်စာ)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,windspeed_10m,winddirection_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,winddirection_10m_dominant&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        h, d = r['hourly'], r['daily']
        df_h = pd.DataFrame({"Time": pd.to_datetime(h['time']), "Temp": h['temperature_2m'], "Rain": h['precipitation'], "Wind": h['windspeed_10m'], "WindDir": h['winddirection_10m']})
        df_d = pd.DataFrame({"Date": pd.to_datetime(d['time']), "Tmax": d['temperature_2m_max'], "Tmin": d['temperature_2m_min'], "RainSum": d['precipitation_sum'], "WindMax": d['windspeed_10m_max'], "WindDirDom": d['winddirection_10m_dominant']})
        
        # လေတိုက်ရာအရပ် အပြောင်းအလဲကို မြင်သာစေရန် နေ့စဉ် နေ့လည် ၁ နာရီ ဒေတာကို နမူနာယူခြင်း
        df_wind_sample = df_h[df_h['Time'].dt.hour == 13].copy()
        return df_h, df_d, df_wind_sample
    except: return None, None, None

# --- Sidebar ---
st.sidebar.image("https://www.moezala.gov.mm/themes/custom/dmh/logo.png", width=80)
selected_city = st.sidebar.selectbox("🎯 Select City", sorted(list(MYANMAR_CITIES_20.keys())))

# --- Main UI ---
st.markdown(f"<h1 style='text-align: center; color: #1E88E5;'>🌦️ {selected_city} Full Weather Dashboard</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'><b>Local Time (MMT):</b> {now.strftime('%I:%M %p, %d %b %Y')}</p>", unsafe_allow_html=True)

df_h, df_d, df_w = get_all_weather_data(selected_city)

if df_d is not None:
    # ၁။ Live Highlights
    curr_hour_idx = min(current_hour, len(df_h)-1)
    curr_data = df_h.iloc[curr_hour_idx]
    
    st.markdown("### 📍 Live Highlights")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌡️ Temp", f"{curr_data['Temp']} °C")
    c2.metric("🌧️ Rain", f"{curr_data['Rain']} mm")
    c3.metric("💨 Wind", f"{curr_data['Wind']} mph")
    c4.metric("🧭 Direction", f"{get_wind_dir_text(curr_data['WindDir'])}")
    st.markdown("---")

    # ၂။ Wind Analysis (Line + Dynamic Arrows)
    st.subheader("💨 Wind Speed (mph) & Directional Arrows (16-Day)")
    fig_wind = go.Figure()
    fig_wind.add_trace(go.Scatter(x=df_w['Time'], y=df_w['WindSpeed'] if 'WindSpeed' in df_w else df_w['Wind'], 
                                  mode='lines+markers', name='Wind Speed', line=dict(color='teal', width=2)))
    fig_wind.add_trace(go.Scatter(
        x=df_w['Time'], y=(df_w['WindSpeed'] if 'WindSpeed' in df_w else df_w['Wind']) + 1.5,
        mode='markers', name='Direction',
        marker=dict(symbol='arrow', size=18, angle=df_w['WindDir'], color='orangered', line=dict(width=1, color='black'))
    ))
    fig_wind.update_layout(height=450, xaxis_title="Date", yaxis_title="Speed (mph)")
    st.plotly_chart(fig_wind, use_container_width=True)
    st.caption("မြှားခေါင်းများသည် တစ်ရက်ချင်းစီ၏ နေ့လည်ပိုင်း လေတိုက်ရာအရပ်ကို ၃၆၀ ဒီဂရီအတိုင်း ညွှန်ပြနေခြင်းဖြစ်ပါသည်။")

    # ၃။ Temperature & Rain Charts
    st.markdown("---")
    st.subheader("🌡️ Temperature & 🌧️ Rain Forecast")
    colA, colB = st.columns(2)
    with colA:
        fig_t = px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, 
                        color_discrete_map={'Tmax': 'red', 'Tmin': 'blue'}, title="Temp Outlook (°C)")
        st.plotly_chart(fig_t, use_container_width=True)
    with colB:
        fig_r = px.bar(df_d, x='Date', y='RainSum', color_discrete_sequence=['deepskyblue'], title="Precipitation Sum (mm)")
        st.plotly_chart(fig_r, use_container_width=True)

else:
    st.error("⚠️ Data connection failed. Please check your internet or refresh.")

# --- Footer ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <p>Maintained by <a href='https://www.moezala.gov.mm/' target='_blank'>Department of Meteorology and Hydrology (DMH)</a></p>
        <p style='font-size: 0.8em;'>Source: Open-Meteo API (16-Day Forecast) | Unit: mph, °C, mm</p>
    </div>
    """, unsafe_allow_html=True
)
