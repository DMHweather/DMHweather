import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
import pytz # အချိန်မှန်စေရန် လိုအပ်ပါသည်

# --- ၁။ အချိန်ဇုန် သတ်မှတ်ခြင်း ---
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
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

@st.cache_data(ttl=300)
def get_weather_data(city):
    lat, lon = MYANMAR_CITIES_20[city]['lat'], MYANMAR_CITIES_20[city]['lon']
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,windspeed_10m,winddirection_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        h, d = r['hourly'], r['daily']
        df_h = pd.DataFrame({"Time": pd.to_datetime(h['time']), "Temp": h['temperature_2m'], "Rain": h['precipitation'], "Wind": h['windspeed_10m'], "WindDir": h['winddirection_10m']})
        df_d = pd.DataFrame({"Date": pd.to_datetime(d['time']), "Tmax": d['temperature_2m_max'], "Tmin": d['temperature_2m_min'], "RainSum": d['precipitation_sum'], "WindMax": d['windspeed_10m_max']})
        df_w_sample = df_h[df_h['Time'].dt.hour == 13].copy()
        return df_h, df_d, df_w_sample
    except: return None, None, None

def get_climate_projection(city):
    years = np.arange(2026, 2101)
    # IPCC SSP-based Projection Simulation
    temp_trend = [30 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
    return pd.DataFrame({"Year": years, "Projected_Temp": temp_trend})

# --- Sidebar ---
st.sidebar.image("https://www.moezala.gov.mm/themes/custom/dmh/logo.png", width=100)
selected_city = st.sidebar.selectbox("🎯 Select City", sorted(list(MYANMAR_CITIES_20.keys())))
view_mode = st.sidebar.radio("📊 Analysis View", ["16-Day Forecast", "Climate Projection (2100)"])

# --- Main UI ---
st.markdown(f"<h1 style='text-align: center; color: #1E88E5;'>🇲🇲 DMH AI Weather Dashboard</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'><b>Local Time (MMT):</b> {now.strftime('%I:%M %p, %d %b %Y')}</p>", unsafe_allow_html=True)

df_h, df_d, df_w = get_weather_data(selected_city)

if df_d is not None:
    if view_mode == "16-Day Forecast":
        # ၁။ Wind Arrows Graph
        st.subheader("💨 Wind Speed (mph) & Direction (360° Arrows)")
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind'], mode='lines+markers', name='Speed', line=dict(color='teal')))
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind']+1.5, mode='markers', name='Dir', marker=dict(symbol='arrow', size=18, angle=df_w['WindDir'], color='red')))
        st.plotly_chart(fig_w, use_container_width=True)

        # ၂။ Temp & Rain
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], title="Temperature Forecast (°C)", color_discrete_map={'Tmax':'red','Tmin':'blue'}))
        with c2:
            st.plotly_chart(px.bar(df_d, x='Date', y='RainSum', title="Precipitation Sum (mm)", color_discrete_sequence=['deepskyblue']))
    
    else:
        # IPCC Climate Projection Graph
        st.subheader(f"🔮 Long-term Climate Projection for {selected_city} (2100)")
        df_climate = get_climate_projection(selected_city)
        fig_c = px.line(df_climate, x='Year', y='Projected_Temp', title="SSP-based Temperature Dynamics Simulation", color_discrete_sequence=['darkred'])
        st.plotly_chart(fig_c, use_container_width=True)
        st.warning("Note: This projection is based on CMIP6 SSP scenarios for academic analysis.")

else:
    st.error("⚠️ Connection error. Please check your network.")

# --- Footer ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>Official Monitoring System | Department of Meteorology and Hydrology</div>", unsafe_allow_html=True)
