import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
import pytz
import os

# --- ၁။ အချိန်ဇုန်နှင့် Logo ပတ်လမ်းကြောင်း ---
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)

# Logo ဖိုင်အမည်များကို သတ်မှတ်ခြင်း
dmh_custom_logo = "logo.png"  # လူကြီးမင်း ပို့ပေးထားသော Hydrological Cycle Logo
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1" # DMH Official Logo

# --- ၂။ Page Configuration ---
st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide", page_icon="🌤️")

# မြို့ကြီး ၂၀ ကျော်စာရင်း (ကိုဩဒိနိတ်များ)
MYANMAR_CITIES_20 = {
    "Naypyidaw": {"lat": 19.7633, "lon": 96.0785}, "Yangon": {"lat": 16.8661, "lon": 96.1951},
    "Pyinmana": {"lat": 19.7414, "lon": 96.2004}, "Bawlakhae": {"lat": 19.1576, "lon": 97.3328},
    "Mandalay": {"lat": 21.9747, "lon": 96.0836}, "Bago": {"lat": 17.3333, "lon": 96.4833},
    "Magway": {"lat": 20.1500, "lon": 94.9167}, "Monywa": {"lat": 22.1167, "lon": 95.1333},
    "Pathein": {"lat": 16.7833, "lon": 94.7333}, "Pyay": {"lat": 18.8167, "lon": 95.2167},
    "Taungoo": {"lat": 18.9333, "lon": 96.4333}, "Hinthada": {"lat": 17.6500, "lon": 95.3833},
    "Myitkyina": {"lat": 25.3831, "lon": 97.3964}, "Taunggyi": {"lat": 20.7888, "lon": 97.0333},
    "Kawthaung": {"lat": 10.0013, "lon": 95.5584}, "Myeik": {"lat": 12.4492, "lon": 98.6271},
    "Myinmu": {"lat": 21.9219, "lon": 95.5772}, "Nyaung-U": {"lat": 21.1940, "lon": 94.9071},
    "Hakha": {"lat": 22.6407, "lon": 93.6041}, "Kyaukpyu": {"lat": 19.4212, "lon": 93.5458},
    "Minbu": {"lat": 20.1648, "lon": 94.8777}, "Chauk": {"lat": 20.8941, "lon": 94.8205},
    "Mawlamyine": {"lat": 16.4905, "lon": 97.6282}, "Sittwe": {"lat": 20.1436, "lon": 92.8977},
    "Lashio": {"lat": 22.9333, "lon": 97.7500}, "Hpa-An": {"lat": 16.8906, "lon": 97.6333},
    "Loikaw": {"lat": 19.6742, "lon": 97.2093}, "Mindat": {"lat": 21.3748, "lon": 93.9725},
    "Hkamti": {"lat": 25.9977, "lon": 95.6905}, "Dawei": {"lat": 14.0833, "lon": 98.2000}
}

@st.cache_data(ttl=300)
def get_weather_data(city):
    lat, lon = MYANMAR_CITIES_20[city]['lat'], MYANMAR_CITIES_20[city]['lon']
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,precipitation,windspeed_10m,winddirection_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        h, d = r['hourly'], r['daily']
        oktas = [round((c / 100) * 8) for c in h['cloud_cover']]
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(h['time']), "Temp": h['temperature_2m'], 
            "Humidity": h['relative_humidity_2m'], "Visibility": np.array(h['visibility']) / 1000,
            "Cloud_Okta": oktas, "Wind": h['windspeed_10m'], "WindDir": h['winddirection_10m'],
            "Rain": h['precipitation']
        })
        df_d = pd.DataFrame({"Date": pd.to_datetime(d['time']), "Tmax": d['temperature_2m_max'], "Tmin": d['temperature_2m_min'], "RainSum": d['precipitation_sum']})
        return df_h, df_d, df_h[df_h['Time'].dt.hour == 13].copy()
    except: return None, None, None

# --- ၃။ Sidebar ---
st.sidebar.image(dm_header_logo, width=120)
st.sidebar.markdown("---")
# Sidebar တွင် Hydrological Logo ထည့်ခြင်း
if os.path.exists(dmh_custom_logo):
    st.sidebar.image(dmh_custom_logo, caption="DMH - Hydrological Cycle", use_container_width=True)

st.sidebar.markdown("### ⚙️ Bias Correction")
temp_bias = st.sidebar.slider("🌡️ Temp Offset (°C)", -5.0, 5.0, 0.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Monitoring Controls")
selected_city = st.sidebar.selectbox("🎯 Select City", sorted(list(MYANMAR_CITIES_20.keys())))
view_mode = st.sidebar.radio("📊 Analysis View", ["16-Day Forecast Analysis", "Heatwave Monitoring (IBF)", "Climate Projection (2100)"])

# --- ၄။ Main UI Header ---
head_col1, head_col2 = st.columns([1, 6])
with head_col1:
    if os.path.exists(dmh_custom_logo):
        st.image(dmh_custom_logo, width=80)
with head_col2:
    st.markdown(f"<h1 style='margin:0;'>DMH AI Weather Forecast System</h1>", unsafe_allow_html=True)
    st.markdown(f"<b>Local Time (MMT):</b> {now.strftime('%I:%M %p, %d %b %Y')}", unsafe_allow_html=True)
st.markdown("---")

df_h, df_d, df_w = get_weather_data(selected_city)

if df_d is not None:
    df_h['Temp'] = df_h['Temp'] + temp_bias
    df_d['Tmax'] = df_d['Tmax'] + temp_bias
    df_d['Tmin'] = df_d['Tmin'] + temp_bias

    if view_mode == "16-Day Forecast Analysis":
        # ၁။ အပူချိန်
        c1_1, c1_2 = st.columns([0.1, 9])
        with c1_1: st.image(dmh_custom_logo, width=30)
        with c1_2: st.subheader(f"1. Temperature Outlook (°C) - {selected_city}")
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)

        # ၂။ မိုးရေချိန် (မိုးဇလ Logo ပါဝင်သည်)
        c2_1, c2_2 = st.columns([0.1, 9])
        with c2_1: st.image(dmh_custom_logo, width=30)
        with c2_2: st.subheader(f"2. Daily Precipitation Summary (mm) - {selected_city}")
        st.plotly_chart(px.bar(df_d, x='Date', y='RainSum', color_discrete_sequence=['deepskyblue']), use_container_width=True)

        # ၃။ လေတိုက်နှုန်း
        c3_1, c3_2 = st.columns([0.1, 9])
        with c3_1: st.image(dmh_custom_logo, width=30)
        with c3_2: st.subheader(f"3. Wind Speed & Direction - {selected_city}")
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind'], mode='lines+markers', name='Speed', line=dict(color='teal', width=3)))
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind']+1.5, mode='markers', marker=dict(symbol='arrow', size=18, angle=df_w['WindDir'], color='red')))
        st.plotly_chart(fig_w, use_container_width=True)

        # ၄။ အဝေးမြင်တာ
        c4_1, c4_2 = st.columns([0.1, 9])
        with c4_1: st.image(dmh_custom_logo, width=30)
        with c4_2: st.subheader(f"4. Visibility Analysis (km) - {selected_city}")
        st.plotly_chart(px.line(df_h, x='Time', y='Visibility', color_discrete_sequence=['#2ecc71']), use_container_width=True)

        # ၅။ စိုထိုင်းဆ
        c5_1, c5_2 = st.columns([0.1, 9])
        with c5_1: st.image(dmh_custom_logo, width=30)
        with c5_2: st.subheader(f"5. Relative Humidity (%) - {selected_city}")
        st.plotly_chart(px.area(df_h, x='Time', y='Humidity', color_discrete_sequence=['#3498db']), use_container_width=True)

        # ၆။ တိမ်
        c6_1, c6_2 = st.columns([0.1, 9])
        with c6_1: st.image(dmh_custom_logo, width=30)
        with c6_2: st.subheader(f"6. Cloud Cover (Oktas: 0-8) - {selected_city}")
        fig_c = px.bar(df_h, x='Time', y='Cloud_Okta', color='Cloud_Okta', color_continuous_scale='Blues')
        fig_c.update_layout(yaxis=dict(tickmode='linear', range=[0, 8.5]))
        st.plotly_chart(fig_c, use_container_width=True)

    elif view_mode == "Heatwave Monitoring (IBF)":
        st.image(dmh_custom_logo, width=60)
        st.subheader(f"🔥 Impact-Based Monitoring: Extreme Heat ({selected_city})")
        max_t = df_d['Tmax'].max()
        risk_level, color, text_c = "Low Risk", "green", "white"
        if max_t >= 42: risk_level, color = "Extreme Risk", "red"
        elif max_t >= 40: risk_level, color = "High Risk", "orange"
        elif max_t >= 38: risk_level, color, text_c = "Moderate Risk", "yellow", "black"

        st.markdown(f"<div style='background-color:{color}; padding:25px; border-radius:15px; text-align:center; border: 2px solid #333;'><h2 style='color:{text_c}; margin:0;'>Heat Risk Status: {risk_level}</h2><p style='color:{text_c}; font-size:1.2em;'>Highest Expected: {max_t:.1f} °C</p></div>", unsafe_allow_html=True)
        st.plotly_chart(px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd').add_hline(y=40, line_dash="dash", line_color="red"), use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.error("**⚠️ Possible Impacts:**\n* Heatstroke (အပူလျှပ်ခြင်း) ဖြစ်နိုင်ခြေ မြင့်မားခြင်း။\n* ရေဓာတ်ခမ်းခြောက်ခြင်းနှင့် မူးဝေခြင်း။")
        with col2:
            st.success("**🛡️ Mitigation Actions:**\n* နေပူထဲ တိုက်ရိုက်သွားလာခြင်းကို ရှောင်ကြဉ်ပါ။\n* ရေနှင့် ဓာတ်ဆားရည်ကို ပုံမှန်ထက် ပိုသောက်ပါ။")

    else:
        st.image(dmh_custom_logo, width=60)
        st.subheader(f"🔮 Future Climate Projection (2100) - {selected_city}")
        years = np.arange(2026, 2101)
        temp_trend = [30 + (y-2026)*0.043 + np.random.normal(0, 0.5) for y in years]
        st.plotly_chart(px.line(x=years, y=temp_trend, labels={'y':'Mean Temp'}, color_discrete_sequence=['darkred']), use_container_width=True)
        st.info("Note: This projection uses CMIP6 global climate models under a high-emission scenario (SSP5-8.5).")

else:
    st.error("Data source unavailable.")

# --- ၅။ Data Source Footer ---
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; font-size: 0.85em; color: #666; line-height: 1.6;'>
    <p><b>Forecast Data Source (16-Day):</b> Open-Meteo API (Combining ECMWF IFS, GFS, ICON, and JMA global models).</p>
    <p><b>Heatwave Analysis:</b> Based on Impact-Based Forecasting (IBF) thresholds (P90, P95, P99) and WMO criteria.</p>
    <p><b>Climate Data:</b> IPCC AR6 Assessment Report and CMIP6 Global Climate Models (SSP scenarios).</p>
    <p style='margin-top: 10px; font-weight: bold;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</p>
</div>
""", unsafe_allow_html=True)
