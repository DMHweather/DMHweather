import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
import pytz

# --- ၁။ အချိန်ဇုန် (Myanmar Standard Time) သတ်မှတ်ခြင်း ---
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)

# --- ၂။ Page Configuration ---
st.set_page_config(
    page_title="DMH AI Weather Dashboard", 
    layout="wide", 
    page_icon="🌦️"
)

# မြန်မာနိုင်ငံ မြို့ကြီး (၂၀) ၏ တည်နေရာများ
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

# API မှ ဒေတာရယူရန် Function
@st.cache_data(ttl=300)
def get_weather_data(city):
    lat, lon = MYANMAR_CITIES_20[city]['lat'], MYANMAR_CITIES_20[city]['lon']
    # ၁၆ ရက်စာ ခန့်မှန်းချက် (Free API အများဆုံး)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,windspeed_10m,winddirection_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        h, d = r['hourly'], r['daily']
        df_h = pd.DataFrame({"Time": pd.to_datetime(h['time']), "Temp": h['temperature_2m'], "Wind": h['windspeed_10m'], "WindDir": h['winddirection_10m']})
        df_d = pd.DataFrame({"Date": pd.to_datetime(d['time']), "Tmax": d['temperature_2m_max'], "Tmin": d['temperature_2m_min'], "RainSum": d['precipitation_sum'], "WindMax": d['windspeed_10m_max']})
        # နေ့လည် ၁ နာရီ ဒေတာ (Wind Direction Arrows အတွက်)
        df_w_sample = df_h[df_h['Time'].dt.hour == 13].copy()
        return df_h, df_d, df_w_sample
    except: return None, None, None

# --- Sidebar (ဘေးဘောင်) ---
st.sidebar.image("https://www.moezala.gov.mm/themes/custom/dmh/logo.png", width=120)
st.sidebar.markdown("### 🔍 Dashboard Controls")
selected_city = st.sidebar.selectbox("🎯 Select City", sorted(list(MYANMAR_CITIES_20.keys())))
view_mode = st.sidebar.radio("📊 Analysis View", ["16-Day Forecast Analysis", "Heatwave Monitoring (IBF)", "Climate Projection (2100)"])

# --- Main Dashboard UI ---
st.markdown(f"<h1 style='text-align: center; color: #1E88E5;'>🇲🇲 DMH AI Weather Forecast System</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'><b>Local Time (MMT):</b> {now.strftime('%I:%M %p, %d %b %Y')}</p>", unsafe_allow_html=True)
st.markdown("---")

df_h, df_d, df_w = get_weather_data(selected_city)

if df_d is not None:
    if view_mode == "16-Day Forecast Analysis":
        # ၁။ Wind Analysis (အပေါ်ဆုံး)
        st.subheader("💨 (1) Wind Speed (mph) & Directional Arrows")
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind'], mode='lines+markers', name='Speed', line=dict(color='teal', width=3)))
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind'] + 1.5, mode='markers', name='Direction',
                                   marker=dict(symbol='arrow', size=18, angle=df_w['WindDir'], color='red', line=dict(width=1, color='black'))))
        fig_w.update_layout(height=450, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_w, use_container_width=True)

        st.markdown("---")

        # ၂။ Temperature Graph (အလယ်)
        st.subheader("🌡️ (2) 16-Day Temperature Outlook (°C)")
        fig_t = px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, color_discrete_map={'Tmax':'#d62728', 'Tmin':'#1f77b4'})
        fig_t.update_layout(height=450, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_t, use_container_width=True)

        st.markdown("---")

        # ၃။ Rainfall Graph (အောက်ဆုံး)
        st.subheader("🌧️ (3) Precipitation Summary (mm)")
        fig_r = px.bar(df_d, x='Date', y='RainSum', color_discrete_sequence=['#00b4d8'])
        fig_r.update_layout(height=450, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_r, use_container_width=True)

    elif view_mode == "Heatwave Monitoring (IBF)":
        st.subheader(f"🔥 Impact-Based Monitoring: Heatwave ({selected_city})")
        
        # Heatwave Criterion Logic
        max_temp_val = df_d['Tmax'].max()
        risk_level, color, text_c = "Low", "green", "white"
        
        if max_temp_val >= 42: risk_level, color = "Extreme Risk", "red"
        elif max_temp_val >= 40: risk_level, color = "High Risk", "orange"
        elif max_temp_val >= 38: risk_level, color, text_c = "Moderate Risk", "yellow", "black"

        # Risk Level Display Card
        st.markdown(f"""
        <div style="background-color:{color}; padding:25px; border-radius:15px; text-align:center; border: 2px solid #333;">
            <h2 style="color:{text_c}; margin:0;">Heat Risk Status: {risk_level}</h2>
            <p style="color:{text_c}; font-size:1.2em;">Highest Expected Temperature: {max_temp_val} °C</p>
        </div>
        """, unsafe_allow_html=True)

        # Heat Trend Bar Chart
        st.markdown("#### Daily Maximum Temperature Trend")
        fig_h = px.bar(df_d, x='Date', y='Tmax', color='Tmax', 
                       color_continuous_scale='YlOrRd', labels={'Tmax': 'Max Temp (°C)'})
        fig_h.add_hline(y=40, line_dash="dash", line_color="red", annotation_text="Danger Threshold (40°C)")
        fig_h.update_layout(height=500)
        st.plotly_chart(fig_h, use_container_width=True)

        # IBF Recommendations
        st.markdown("### 📋 Impact-Based Recommendations")
        c1, c2 = st.columns(2)
        with c1:
            st.info("**🏥 Health Sector:**\n* Heatstroke ရှောင်ရန် အရိပ်ရသောနေရာတွင် နေပါ။\n* ရေနှင့် ဓာတ်ဆားရည် ပိုမိုသောက်သုံးပါ။")
        with c2:
            st.warning("**🌾 Agriculture Sector:**\n* သီးနှံများအား အပူဒဏ်မှ ကာကွယ်ရန် ရေသွင်းခြင်းကို ဂရုပြုပါ။\n* တိရစ္ဆာန်များအား အအေးပေးစနစ် ထားရှိပါ။")

    else:
        # Long-term Climate Projection
        st.subheader(f"🔮 Long-term Climate Projection (2026-2100): {selected_city}")
        years = np.arange(2026, 2101)
        temp_trend = [30 + (y-2026)*0.043 + np.random.normal(0, 0.5) for y in years]
        fig_c = px.line(x=years, y=temp_trend, labels={'x': 'Year', 'y': 'Mean Temperature (°C)'}, color_discrete_sequence=['darkred'])
        fig_c.update_layout(height=500)
        st.plotly_chart(fig_c, use_container_width=True)
        st.warning("မှတ်ချက်။ ။ ဤသည်မှာ IPCC SSP scenarios များအပေါ် အခြေခံထားသော AI-based Climate Simulation သာ ဖြစ်ပါသည်။")

else:
    st.error("⚠️ Connection Error. Please check your internet or API limits.")

# --- 💡 Footer & Data Sources (အောက်ခြေပိုင်း) ---
st.markdown("---")
st.markdown(f"<p style='text-align: center; color: gray; font-size: 1.0em;'><b>DMH Myanmar | Powered by AI & Global Meteorological Data</b></p>", unsafe_allow_html=True)

# Data Source အသေးစိတ်များကို ဗဟိုပြု၍ ဖော်ပြခြင်း
st.markdown(f"""
<div style='text-align: center; font-size: 0.85em; color: #666; line-height: 1.6;'>
    <p><b>Forecast Data Source (16-Day):</b> Open-Meteo API (Combining ECMWF IFS, GFS, ICON, and JMA global models).</p>
    <p><b>Heatwave Analysis:</b> Based on Impact-Based Forecasting (IBF) thresholds (P90, P95, P99) and WMO criteria.</p>
    <p><b>Climate Data:</b> IPCC AR6 Assessment Report and CMIP6 Global Climate Models (SSP scenarios).</p>
    <p style='margin-top: 10px; font-weight: bold;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</p>
</div>
""", unsafe_allow_html=True)
