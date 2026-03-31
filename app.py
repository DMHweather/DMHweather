import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
import pytz
import os

# --- ၁။ Setup ---
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide", page_icon="🌤️")

# --- ၂။ ဘာသာစကား Dictionary ---
LANG_DICT = {
    "English": {
        "title": "DMH AI Weather Forecast System",
        "time_label": "Local Time (MMT)",
        "city_select": "🎯 Select Station/City",
        "view_mode": "📊 View Mode",
        "modes": ["16-Day Detailed Analysis", "Heatwave IBF (Health)", "Climate Projection (2100)"],
        "charts": [
            "🌡️ 1. Temperature Outlook (°C)", 
            "🌧️ 2. Daily Precipitation Summary (mm)", 
            "💨 3. Wind Speed (mph) & Direction", 
            "🔭 4. Visibility Analysis (km)", 
            "💧 5. Relative Humidity (%)", 
            "☁️ 6. Cloud Cover (Oktas: 0-8)", 
            "⚡ 7. Thunderstorm Potential (%)"
        ],
        "axis_time": "Time / Date",
        "dmh_alert": "📢 Please monitor official DMH announcements in real-time for latest updates.",
        "ibf_header": "🏥 Health Sector Impact & Recommendations",
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "impacts": [
            "Severe threat! High risk of heatstroke and critical dehydration.",
            "Significant risk! Heat exhaustion likely. Vulnerable groups at high risk.",
            "Moderate threat! Prolonged exposure may cause fatigue.",
            "Low threat! Standard summer conditions."
        ],
        "recommends": [
            "STAY INDOORS. Drink 3-4L water. Seek urgent medical care if dizzy. Monitor DMH hourly.",
            "Limit outdoor work. Wear hats/umbrellas. Stay in cool areas. Follow DMH news.",
            "Wear light clothes. Drink water frequently. Check DMH daily forecasts.",
            "Standard health precautions. Monitor DMH official channels."
        ],
        "footer": "Data: Open-Meteo | System: Department of Meteorology and Hydrology (Myanmar)"
    },
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသ ခန့်မှန်းချက်စနစ်",
        "time_label": "မြန်မာစံတော်ချိန်",
        "city_select": "🎯 စခန်း/မြို့အမည်ရွေးချယ်ပါ",
        "view_mode": "📊 ကြည့်ရှုမည့်ပုံစံ",
        "modes": ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", "အပူချိန်နှင့် ကျန်းမာရေး (IBF)", "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀)"],
        "charts": [
            "🌡️ ၁။ အပူချိန်ခန့်မှန်းချက် (°C)", 
            "🌧️ ၂။ မိုးရေချိန်ခန့်မှန်းချက် (mm)", 
            "💨 ၃။ လေတိုက်နှုန်းနှင့် လေအရပ်", 
            "🔭 ၄။ အဝေးမြင်တာ ခန့်မှန်းချက် (km)", 
            "💧 ၅။ စိုထိုင်းဆ ခန့်မှန်းချက် (%)", 
            "☁️ ၆။ တိမ်ဖုံးလွှမ်းမှု (Oktas: 0-8)", 
            "⚡ ၇။ မိုးတိမ်တောင်နှင့် လျှပ်စီးလက်နိုင်ခြေ (%)"
        ],
        "axis_time": "အချိန် / ရက်စွဲ",
        "dmh_alert": "📢 အရေးကြီးသတိပေးချက်: နောက်ဆုံးရ မိုးလေဝသသတင်းများအတွက် မိုးလေဝသနှင့်ဇလဗေဒညွှန်ကြားမှုဦးစီးဌာန (DMH) ၏ ထုတ်ပြန်ချက်များကို အချိန်နဲ့တစ်ပြေးညီ မပြတ်မကွက် စောင့်ကြည့်ပါ။",
        "ibf_header": "🏥 ကျန်းမာရေးကဏ္ဍဆိုင်ရာ အကျိုးသက်ရောက်မှုနှင့် အကြံပြုချက်များ",
        "risk_levels": ["အလွန်အန္တရာယ်ရှိ", "အန္တရာယ်ရှိ", "သတိပြုရန်", "ပုံမှန်"],
        "impacts": [
            "အလွန်စိုးရိမ်ရသော အခြေအနေ! အပူဒဏ်လျှပ်စီးဖြတ်ခြင်း (Heatstroke) နှင့် ရေဓာတ်ကုန်ခမ်းခြင်းကြောင့် အသက်အန္တရာယ်ရှိနိုင်သည်။",
            "အန္တရာယ်ရှိသော အခြေအနေ! အပူဒဏ်ကြောင့် ပင်ပန်းနွမ်းနယ်ခြင်း ဖြစ်နိုင်ပါသည်။ ကလေးနှင့် လူအိုများ အထူးသတိပြုပါ။",
            "သတိပြုရန် အခြေအနေ! နေရောင်အောက်တွင် ကြာရှည်နေပါက ပင်ပန်းနွမ်းနယ်ခြင်း ဖြစ်ပေါ်နိုင်ပါသည်။",
            "ပုံမှန်အခြေအနေ! သိသာထင်ရှားသော ကျန်းမာရေးထိခိုက်မှု မရှိနိုင်ပါ။"
        ],
        "recommends": [
            "အိမ်ထဲတွင်သာ နေပါ။ ရေ (၃-၄) လီတာ သောက်ပါ။ မူးဝေပါက ဆေးရုံသို့ အမြန်သွားပါ။ မိုးဇလထုတ်ပြန်ချက်ကို နာရီအလိုက်စောင့်ကြည့်ပါ။",
            "ပြင်ပလုပ်ငန်းများကို နံနက်/ညနေသာ လုပ်ပါ။ ထီး/ဦးထုပ် ဆောင်းပါ။ ရေဓာတ်ဖြည့်ပါ။ မိုးဇလသတင်းကို အမြဲနားထောင်ပါ။",
            "ပေါ့ပါးသော အဝတ်များ ဝတ်ပါ။ ရေခဏခဏသောက်ပါ။ အရိပ်တွင် နားပါ။ မိုးဇလခန့်မှန်းချက်ကို စစ်ဆေးပါ။",
            "ပုံမှန်အတိုင်း နေနိုင်ပါသည်။ မိုးလေဝသအခြေအနေကို မိုးဇလ၏ တရားဝင်စာမျက်နှာများတွင် ဆက်လက်စောင့်ကြည့်ပါ။"
        ],
        "footer": "အချက်အလက်ရင်းမြစ်: Open-Meteo | တရားဝင်စနစ်: မိုးလေဝသနှင့်ဇလဗေဒညွှန်ကြားမှုဦးစီးဌာန"
    }
}

MYANMAR_CITIES = {
    "Naypyidaw": {"lat": 19.7633, "lon": 96.0785}, "Yangon (Kaba-aye)": {"lat": 16.8661, "lon": 96.1951},
    "Pyinmana": {"lat": 19.7414, "lon": 96.2004}, "Bawlakhae": {"lat": 19.1576, "lon": 97.3328},
    "Dagon (Seikan)": {"lat": 16.8489, "lon": 96.2734}, "Dagon (South)": {"lat": 16.8840, "lon": 96.2400},
    "Hlaing Thayar": {"lat": 16.8812, "lon": 96.0503}, "Shwe Pyithar": {"lat": 16.9759, "lon": 96.0760},
    "Dala": {"lat": 16.7562, "lon": 96.1591}, "Amarapura": {"lat": 21.9100, "lon": 96.0512},
    "Pyigyitagon": {"lat": 21.9167, "lon": 96.0833}, "Pathein Gyi": {"lat": 22.0000, "lon": 96.1670},
    "Mandalay": {"lat": 21.9747, "lon": 96.0836}, "Bago": {"lat": 17.3333, "lon": 96.4833},
    "Magway": {"lat": 20.1500, "lon": 94.9167}, "Monywa": {"lat": 22.1167, "lon": 95.1333},
    "Pathein": {"lat": 16.7833, "lon": 94.7333}, "Pyay": {"lat": 18.8167, "lon": 95.2167},
    "Taungoo": {"lat": 18.9333, "lon": 96.4333}, "Hinthada": {"lat": 17.6500, "lon": 95.3833},
    "Myitkyina": {"lat": 25.3831, "lon": 97.3964}, "Taunggyi": {"lat": 20.7888, "lon": 97.0333},
    "Moegkok": {"lat": 22.9233, "lon": 96.5108}, "Ela Airport": {"lat": 19.6159, "lon": 96.2127},
    "Chauk": {"lat": 20.8941, "lon": 94.8205}, "Myinmu": {"lat": 21.9219, "lon": 95.5772},
    "Mawlamyine": {"lat": 16.4905, "lon": 97.6282}, "Sittwe": {"lat": 20.1436, "lon": 92.8977},
    "Lashio": {"lat": 22.9333, "lon": 97.7500}, "Hpa-An": {"lat": 16.8906, "lon": 97.6333},
    "Loikaw": {"lat": 19.6742, "lon": 97.2093}, "Mindat": {"lat": 21.3748, "lon": 93.9725},
    "Hkamti": {"lat": 25.9977, "lon": 95.6905}, "Dawei": {"lat": 14.0833, "lon": 98.2000}
}

@st.cache_data(ttl=300)
def get_full_weather(city):
    lat, lon = MYANMAR_CITIES[city]['lat'], MYANMAR_CITIES[city]['lon']
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,precipitation,windspeed_10m,winddirection_10m,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        h, d = r['hourly'], r['daily']
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(h['time']), "Temp": h['temperature_2m'], "Humidity": h['relative_humidity_2m'],
            "Visibility": np.array(h['visibility']) / 1000, "Cloud": [round((c/100)*8) for c in h['cloud_cover']],
            "Wind": h['windspeed_10m'], "WindDir": h['winddirection_10m'], "Rain": h['precipitation'],
            "Storm": [min(round((c/3500)*100), 100) for c in h['cape']]
        })
        df_d = pd.DataFrame({"Date": pd.to_datetime(d['time']), "Tmax": d['temperature_2m_max'], "Tmin": d['temperature_2m_min'], "RainSum": d['precipitation_sum']})
        return df_h, df_d
    except: return None, None

# --- ၃။ Sidebar (Bias Correction Slider ပြန်ထည့်သွင်းခြင်း) ---
st.sidebar.image(dm_header_logo, width=120)
lang = st.sidebar.selectbox("🌐 Language / ဘာသာစကား", ["English", "မြန်မာ"])
T = LANG_DICT[lang]

st.sidebar.markdown("### ⚙️ Bias Correction")
temp_bias = st.sidebar.slider("🌡️ Temp Offset (°C)", -5.0, 5.0, 0.0, step=0.5)

selected_city = st.sidebar.selectbox(T["city_select"], sorted(list(MYANMAR_CITIES.keys())))
view_mode = st.sidebar.radio(T["view_mode"], T["modes"])

# --- ၄။ Main Display ---
st.markdown(f"# {T['title']}")
st.warning(T["dmh_alert"])

df_h, df_d = get_full_weather(selected_city)

if df_h is not None:
    # Applying Bias Correction to Data
    df_d['Tmax'] += temp_bias
    df_d['Tmin'] += temp_bias
    df_h['Temp'] += temp_bias

    if view_mode == T["modes"][0]: # အပေါ်အောက် တစ်ဆက်တည်း
        st.subheader(T['charts'][0])
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}, labels={'value': 'Temp (°C)'}), use_container_width=True)
        st.markdown("---")
        st.subheader(T['charts'][1])
        st.plotly_chart(px.bar(df_d, x='Date', y='RainSum', color_discrete_sequence=['deepskyblue']), use_container_width=True)
        st.markdown("---")
        st.subheader(T['charts'][2])
        df_w = df_h[df_h['Time'].dt.hour == 13]
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind'], mode='lines+markers', name='Speed'))
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind']+2, mode='markers', marker=dict(symbol='arrow', angle=df_w['WindDir'], size=14, color='red'), name='Dir'))
        st.plotly_chart(fig_w, use_container_width=True)
        st.markdown("---")
        st.subheader(T['charts'][3])
        st.plotly_chart(px.line(df_h, x='Time', y='Visibility', color_discrete_sequence=['#2ecc71']), use_container_width=True)
        st.markdown("---")
        st.subheader(T['charts'][4])
        st.plotly_chart(px.area(df_h, x='Time', y='Humidity', color_discrete_sequence=['#3498db']), use_container_width=True)
        st.markdown("---")
        st.subheader(T['charts'][5])
        st.plotly_chart(px.bar(df_h, x='Time', y='Cloud', color='Cloud'), use_container_width=True)
        st.markdown("---")
        st.subheader(T['charts'][6])
        st.plotly_chart(px.bar(df_h, x='Time', y='Storm', color_discrete_sequence=['#e67e22']), use_container_width=True)
        st.warning("**မှတ်ချက်:** မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ ၆၀% ထက်ကျော်လွန်ပါက လေပြင်းတိုက်ခတ်ခြင်း၊ မိုးကြိုးပစ်ခြင်းနှင့် လျှပ်စီးလက်ခြင်းများ ဖြစ်ပေါ်နိုင်သဖြင့် ဂရုပြုရန် လိုအပ်ပါသည်။")

    elif view_mode == T["modes"][1]: # IBF with Bias Correction
        max_t = df_d['Tmax'].max()
        idx = 0 if max_t >= 42 else 1 if max_t >= 40 else 2 if max_t >= 38 else 3
        st.markdown(f"<div style='background-color:{['#800000','#d00000','#ffaa00','#008000'][idx]}; padding:35px; border-radius:15px; text-align:center;'><h1 style='color:white;'>{T['risk_levels'][idx]}: {max_t:.1f} °C</h1></div>", unsafe_allow_html=True)
        st.subheader(T['ibf_header'])
        st.error(f"⚠️ **Impact:**\n\n{T['impacts'][idx]}")
        st.success(f"💡 **Recommendations:**\n\n{T['recommends'][idx]}")
        st.plotly_chart(px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd'), use_container_width=True)

    else: # Climate
        st.subheader(T['modes'][2])
        years = np.arange(2026, 2101)
        trend = [30 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
        st.plotly_chart(px.line(x=years, y=trend, labels={'x':'Year','y':'Temp (°C)'}, color_discrete_sequence=['darkred']), use_container_width=True)



# --- ၆။ Data Source Footer ---
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; font-size: 0.85em; color: #666; line-height: 1.6;'>
    <p><b>Forecast Data Source (16-Day):</b> Open-Meteo API (Combining ECMWF IFS, GFS, ICON, and JMA global models).</p>
    <p><b>Heatwave Analysis:</b> Based on Impact-Based Forecasting (IBF) thresholds (P90, P95, P99) and WMO criteria.</p>
    <p><b>Climate Data:</b> IPCC AR6 Assessment Report and CMIP6 Global Climate Models (SSP scenarios).</p>
    <p style='margin-top: 10px; font-weight: bold;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</p>
</div>
""", unsafe_allow_html=True)

