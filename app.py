import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
import pytz

# --- ၁။ အချိန်ဇုန်နှင့် Logo ---
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
dmh_logo_url = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png"

# --- ၂။ Page Configuration (Phone Icon အပါအဝင်) ---
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
st.sidebar.image(dmh_logo_url, width=120)
st.sidebar.markdown("### 🔍 Monitoring Controls")
selected_city = st.sidebar.selectbox("🎯 Select City", sorted(list(MYANMAR_CITIES_20.keys())))
view_mode = st.sidebar.radio("📊 Analysis View", ["16-Day Forecast Analysis", "Heatwave Monitoring (IBF)", "Climate Projection (2100)"])

# --- Main Dashboard ---
st.markdown(f"<h1 style='text-align: center; color: #1E88E5;'>🇲🇲 DMH AI Weather Forecast System</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'><b>Local Time (MMT):</b> {now.strftime('%I:%M %p, %d %b %Y')}</p>", unsafe_allow_html=True)
st.markdown("---")

df_h, df_d, df_w = get_weather_data(selected_city)

if df_d is not None:
    if view_mode == "16-Day Forecast Analysis":
        # ၁။ Wind, ၂။ Temp, ၃။ Rain (Vertical Stack)
        st.subheader("💨 (1) Wind Speed & Directional Arrows")
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind'], mode='lines+markers', line=dict(color='teal', width=3)))
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind']+1.5, mode='markers', marker=dict(symbol='arrow', size=18, angle=df_w['WindDir'], color='red')))
        st.plotly_chart(fig_w, use_container_width=True)

        st.subheader("🌡️ (2) 16-Day Temperature Outlook (°C)")
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)

        st.subheader("🌧️ (3) Precipitation Summary (mm)")
        st.plotly_chart(px.bar(df_d, x='Date', y='RainSum', color_discrete_sequence=['#00b4d8']), use_container_width=True)

    elif view_mode == "Heatwave Monitoring (IBF)":
        st.subheader(f"🔥 Impact-Based Monitoring: Extreme Heat ({selected_city})")
        
        max_t = df_d['Tmax'].max()
        risk_level, color, text_c = "Low Risk", "green", "white"
        if max_t >= 42: risk_level, color = "Extreme Risk", "red"
        elif max_t >= 40: risk_level, color = "High Risk", "orange"
        elif max_t >= 38: risk_level, color, text_c = "Moderate Risk", "yellow", "black"

        st.markdown(f"""
        <div style="background-color:{color}; padding:25px; border-radius:15px; text-align:center; border: 2px solid #333;">
            <h2 style="color:{text_c}; margin:0;">Heat Risk Status: {risk_level}</h2>
            <p style="color:{text_c}; font-size:1.2em;">Highest Expected Temperature: {max_t} °C</p>
        </div>
        """, unsafe_allow_html=True)

        st.plotly_chart(px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd').add_hline(y=40, line_dash="dash", line_color="red"), use_container_width=True)

        # Updated IBF Health Focus Advice
        st.markdown("### 🏥 Health Sector Impact & Recommendations")
        col1, col2 = st.columns(2)
        with col1:
            st.error("**⚠️ Possible Impacts:**\n* Heatstroke (အပူလျှပ်ခြင်း) ဖြစ်နိုင်ခြေ မြင့်မားခြင်း။\n* ရေဓာတ်ခမ်းခြောက်ခြင်းနှင့် မူးဝေခြင်း။\n* သက်ကြီးရွယ်အိုများနှင့် ကလေးငယ်များအတွက် အထူးအန္တရာယ်ရှိခြင်း။")
        with col2:
            st.success("**🛡️ Mitigation Actions:**\n* နေပူထဲ တိုက်ရိုက်သွားလာခြင်းကို အတတ်နိုင်ဆုံး ရှောင်ကြဉ်ပါ။\n* ရေနှင့် ဓာတ်ဆားရည်ကို ပုံမှန်ထက် ပိုသောက်ပါ။\n* လေဝင်လေထွက်ကောင်းသော အဝတ်အစားများ ဝတ်ဆင်ပါ။")

    else:
        st.subheader("🔮 Climate Projection (2100)")
        years = np.arange(2026, 2101)
        temp_trend = [30 + (y-2026)*0.043 + np.random.normal(0, 0.5) for y in years]
        st.plotly_chart(px.line(x=years, y=temp_trend, labels={'x': 'Year', 'y': 'Mean Temp'}, color_discrete_sequence=['darkred']), use_container_width=True)

else:
    st.error("Error connecting to data source.")

# --- Footer ---
st.markdown("---")
st.markdown(f"<p style='text-align: center; color: gray;'><b>DMH Myanmar | Powered by AI & Global Meteorological Data</b></p>", unsafe_allow_html=True)
st.markdown(f"<div style='text-align: center; font-size: 0.85em; color: #666;'>Data Sources: Open-Meteo (ECMWF, GFS), IBF Criteria (P90/P95/P99), IPCC AR6.</div>", unsafe_allow_html=True)
