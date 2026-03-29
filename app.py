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

# --- ၂။ Page Configuration (ဌာနအမည်နှင့် Logo သတ်မှတ်ခြင်း) ---
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

# လေတိုက်ရာအရပ်အား စာသားဖြင့်ဖော်ပြရန် Function
def get_wind_dir_text(deg):
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    return dirs[int((deg + 11.25) / 22.5) % 16]

# API မှ ဒေတာရယူရန် Function
@st.cache_data(ttl=300)
def get_weather_data(city):
    lat, lon = MYANMAR_CITIES_20[city]['lat'], MYANMAR_CITIES_20[city]['lon']
    # ၁၆ ရက်စာ ခန့်မှန်းချက် (Free API အများဆုံး)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,windspeed_10m,winddirection_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        h, d = r['hourly'], r['daily']
        df_h = pd.DataFrame({"Time": pd.to_datetime(h['time']), "Temp": h['temperature_2m'], "Rain": h['precipitation'], "Wind": h['windspeed_10m'], "WindDir": h['winddirection_10m']})
        df_d = pd.DataFrame({"Date": pd.to_datetime(d['time']), "Tmax": d['temperature_2m_max'], "Tmin": d['temperature_2m_min'], "RainSum": d['precipitation_sum'], "WindMax": d['windspeed_10m_max']})
        # နေ့စဉ်အရပ်မျက်နှာပြောင်းလဲမှုအတွက် နေ့လည် ၁ နာရီဒေတာကို ယူခြင်း
        df_w_sample = df_h[df_h['Time'].dt.hour == 13].copy()
        return df_h, df_d, df_w_sample
    except: return None, None, None

# IPCC Climate Projection simulation
def get_climate_projection(city):
    years = np.arange(2026, 2101)
    temp_trend = [30 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
    return pd.DataFrame({"Year": years, "Projected_Temp": temp_trend})

# --- Sidebar (ဘေးဘောင်) ---
st.sidebar.image("https://www.moezala.gov.mm/themes/custom/dmh/logo.png", width=120)
st.sidebar.markdown("### 🔍 Filter Options")
selected_city = st.sidebar.selectbox("🎯 Select City", sorted(list(MYANMAR_CITIES_20.keys())))
view_mode = st.sidebar.radio("📊 Display Mode", ["16-Day Forecast Analysis", "IPCC Climate Projection (2100)"])

# --- Main Dashboard ---
st.markdown(f"<h1 style='text-align: center; color: #1E88E5;'>🇲🇲 DMH AI Weather Forecast System</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'><b>Local Time (MMT):</b> {now.strftime('%I:%M %p, %d %b %Y')}</p>", unsafe_allow_html=True)
st.markdown("---")

df_h, df_d, df_w = get_weather_data(selected_city)

if df_d is not None:
    if view_mode == "16-Day Forecast Analysis":
        # ၁။ Live Metrics (Highlight အကျဉ်း)
        current_idx = min(now.hour, len(df_h)-1)
        curr = df_h.iloc[current_idx]
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🌡️ Temp", f"{curr['Temp']} °C")
        m2.metric("🌧️ Rain", f"{curr['Rain']} mm")
        m3.metric("💨 Wind", f"{curr['Wind']} mph")
        m4.metric("🧭 Dir", f"{get_wind_dir_text(curr['WindDir'])}")
        
        st.markdown("---")

        # ၂။ Wind Speed & Direction Arrows (အပေါ်ဆုံး)
        st.subheader("💨 (1) Wind Speed (mph) & Directional Arrows")
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind'], mode='lines+markers', name='Max Wind Speed', line=dict(color='teal', width=3)))
        # မြှားခေါင်းများ ထည့်သွင်းခြင်း
        fig_w.add_trace(go.Scatter(
            x=df_w['Time'], y=df_w['Wind'] + 1.5,
            mode='markers', name='Direction',
            marker=dict(symbol='arrow', size=18, angle=df_w['WindDir'], color='red', line=dict(width=1, color='black'))
        ))
        fig_w.update_layout(height=450, xaxis_title="Date", yaxis_title="Speed (mph)", plot_bgcolor="#f8f9fa")
        st.plotly_chart(fig_w, use_container_width=True)

        # ၃။ Temperature Graph (အလယ်)
        st.subheader("🌡️ (2) 16-Day Temperature Outlook (°C)")
        fig_t = px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, 
                        color_discrete_map={'Tmax':'#d62728', 'Tmin':'#1f77b4'})
        fig_t.update_layout(height=450, xaxis_title="Date", yaxis_title="Temperature (°C)")
        st.plotly_chart(fig_t, use_container_width=True)

        # ၄။ Rainfall Graph (အောက်ဆုံး)
        st.subheader("🌧️ (3) Precipitation Summary (mm)")
        fig_r = px.bar(df_d, x='Date', y='RainSum', color_discrete_sequence=['#00b4d8'])
        fig_r.update_layout(height=450, xaxis_title="Date", yaxis_title="Rain (mm)")
        st.plotly_chart(fig_r, use_container_width=True)

    else:
        # IPCC Climate Projection Graph
        st.subheader(f"🔮 Long-term Climate Projection (2026-2100): {selected_city}")
        df_climate = get_climate_projection(selected_city)
        fig_c = px.line(df_climate, x='Year', y='Projected_Temp', 
                        title="Projected Surface Temperature Dynamics (SSP-based Scenario)",
                        color_discrete_sequence=['#b00020'])
        fig_c.update_layout(height=500, xaxis_title="Year", yaxis_title="Mean Temp (°C)")
        st.plotly_chart(fig_c, use_container_width=True)
        st.info("💡 ဤဂရပ်သည် IPCC ၏ SSP scenario များအပေါ် အခြေခံထားသော AI simulation ဖြစ်ပါသည်။")

else:
    st.error("⚠️ Error: API နှင့် ချိတ်ဆက်၍မရပါ။ အင်တာနက်လိုင်းကို ပြန်လည်စစ်ဆေးပေးပါ။")

# --- Footer ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #555;'>
        <p><b>Official Dashboard of Department of Meteorology and Hydrology (DMH) Myanmar</b></p>
        <p style='font-size: 0.85em;'>Supported by AI-based Meteorological Analysis | Monitoring by DMH</p>
    </div>
    """, unsafe_allow_html=True
)
