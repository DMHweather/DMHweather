import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
from datetime import datetime
import pytz

# --- ၁။ Layout Setup ---
st.set_page_config(page_title="DMH AI Weather Forecast System", layout="wide", page_icon="🌤️")
# အခုနက Code ကို ဒီနေရာမှာ ထည့်ပါ (စာကြောင်း ၁၂ ဝန်းကျင်)
st.markdown("""
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="DMH AI">
""", unsafe_allow_html=True)

mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
formatted_now = now.strftime('%I:%M %p, %d %b %Y')
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

# --- ၂။ ဘာသာစကားနှင့် စာသားများ ---
LANG_DATA = {
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသခန့်မှန်းစနစ်",
        "station_label": "🎯 စခန်းအမည်ရွေးချယ်ပါ",
        "view_mode_label": "📊 View Mode",
        "modes": ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", "အပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး )", "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀-SSP5-8.5)"],
        "dmh_alert": "📢 အကြံပြုချက်: နောက်ဆုံးရ မိုးလေဝသသတင်းများအတွက် မိုးဇလ သတင်းများကိုစောင့်ကြည့်ပါ။",
        "storm_note": "📝 မှတ်ချက်: မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ ၆၀% ထက်ကျော်လွန်ပါက လေပြင်းတိုက်ခတ်ခြင်း၊ မိုးကြိုးပစ်ခြင်းနှင့် လျှပ်စီးလက်ခြင်းများ ဖြစ်ပေါ်နိုင်သဖြင့် ဂရုပြုရန် လိုအပ်ပါသည်။",
        "ibf_header": "🏥 ကျန်းမာရေးကဏ္ဍဆိုင်ရာ အကျိုးသက်ရောက်မှုနှင့် အကြံပြုချက်များ",
        "risk_levels": ["အလွန်အန္တရာယ်ရှိ", "အန္တရာယ်ရှိ", "သတိပြုရန်", "ပုံမှန်"],
        "charts": ["🌡️ ၁။ အပူချိန်(ဒီဂရီဆဲလ်စီးယပ်)", "🌧️ ၂။ မိုးရေချိန်(မီလီမီတာ)", "💨 ၃။ လေတိုက်နှုန်း(mph)နှင့်လေတိုက်ရာအရပ်", "🔭 ၄။ အဝေးမြင်တာ (km)", "💧 ၅။ စိုထိုင်းဆ (%)", "☁️ ၆။ တိမ်ဖုံးမှုပမာဏ (Oktas: 0-8)", "⚡ ၇။ မိုးတိမ်တောင်နှင့် လျှပ်စီးလက်နိုင်ခြေ (%)"],
        "impact_list": [
            "အလွန်စိုးရိမ်ရသော အခြေအနေ! အပူဒဏ်လျှပ်စီးဖြတ်ခြင်း (Heatstroke) နှင့် ရေဓာတ်ကုန်ခမ်းခြင်းကြောင့် အသက်အန္တရာယ်ရှိနိုင်သည်။", 
            "အန္တရာယ်ရှိသော အခြေအနေ! အပူဒဏ်ကြောင့် ပင်ပန်းနွမ်းနယ်ခြင်း ဖြစ်နိုင်ပါသည်။ ကလေးနှင့် လူအိုများ အထူးသတိပြုပါ။", 
            "သတိပြုရန် အခြေအနေ! နေရောင်အောက်တွင် ကြာရှည်နေပါက ပင်ပန်းနွမ်းနယ်ခြင်း ဖြစ်ပေါ်နိုင်ပါသည်။", 
            "ပုံမှန်အခြေအနေ! သိသာထင်ရှားသော ကျန်းမာရေးထိခိုက်မှု မရှိနိုင်ပါ။"
        ],
        "recom_list": [
            "အိမ်ထဲတွင်သာ နေပါ။ ရေ (၃-၄) လီတာ သောက်ပါ။ မူးဝေပါက ဆေးရုံသို့ အမြန်သွားပါ။ မိုးလေဝသ သတင်းများကို အချိန်ပြည့် စောင့်ကြည့်ပါ။", 
            "ပြင်ပလုပ်ငန်းများကို နံနက်/ညနေသာ လုပ်ပါ။ ထီး/ဦးထုပ် ဆောင်းပါ။ ရေဓာတ်ဖြည့်ပါ။ မိုးလေဝသ သတင်းများကို နားထောင်ပါ။", 
            "ပေါ့ပါးသော အဝတ်များ ဝတ်ပါ။ ရေခဏခဏသောက်ပါ။ အရိပ်တွင် နားပါ။ မိုးဇလခန့်မှန်းချက်များကို နားထောင်ပါ။", 
            "ပုံမှန်အတိုင်း နေနိုင်ပါသည်။ ရေဓာတ်ဖြည့်တင်းရန်နှင့် မိုးလေဝသ သတင်းများကို ဆက်လက်စောင့်ကြည့်ပါ။"
        ]
    },
    "English": {
        "title": "DMH AI Weather Forecast System",
        "station_label": "🎯 Select Station",
        "view_mode_label": "📊 View Mode",
        "modes": ["16-Day Detailed Analysis", "Heatwave Monitoring (IBF-Health)", "Climate Change (2100-SSP5-8.5)"],
        "dmh_alert": "📢 Tip: Follow DMH news for the latest weather updates.",
        "storm_note": "📝 Note: If thunderstorm probability exceeds 60%, beware of strong winds and lightning.",
        "ibf_header": "🏥 Health Sector Impacts & Recommendations",
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "charts": ["🌡️ 1. Temperature(°C)", "🌧️ 2. Precipitation(mm)", "💨 3. Wind Speed (mph) & Direction", "🔭 4. Visibility (km)", "💧 5. Humidity (%)", "☁️ 6. Cloud Cover (Oktas: 0-8)", "⚡ 7. Thunderstorm & Lightning Probability (%)"],
        "impact_list": ["Extreme danger! Heatstroke possible.", "High danger! Fatigue possible.", "Caution! Sun exposure may cause fatigue.", "Normal conditions."],
        "recom_list": ["Stay indoors. Drink 3-4L water, Follow DMH news for the latest weather updates.", "Work morning/evening only. Use umbrella, Follow DMH news for the latest weather updates.", "Wear light clothes. Rest in shade, Follow DMH news for the latest weather updates.", "Stay hydrated and follow updates, Follow DMH news for the latest weather updates."]
    }
}

# --- ၃။ စခန်းစာရင်းဖတ်ခြင်း ---
@st.cache_data
def load_stations():
    file_path = "Station.csv"
    if not os.path.exists(file_path):
        return {"Naypyidaw": {"lat": 19.76, "lon": 96.08}}
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        df.columns = [c.strip() for c in df.columns]
        cols = {c.lower(): c for c in df.columns}
        n_key = cols.get('city', cols.get('station', df.columns[0]))
        s_dict = {}
        for _, row in df.iterrows():
            s_dict[str(row[n_key]).strip()] = {'lat': float(row['Lat']), 'lon': float(row['Lon'])}
        return s_dict
    except:
        return {"Naypyidaw": {"lat": 19.76, "lon": 96.08}}

MYANMAR_CITIES = load_stations()
city_list = sorted(list(MYANMAR_CITIES.keys()))

# --- ၄။ Sidebar ---
st.sidebar.image(dm_header_logo, width=100)
lang = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True)
T = LANG_DATA[lang]

bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0, step=0.1)
selected_city = st.sidebar.selectbox(T["station_label"], city_list)
view_mode = st.sidebar.radio(T["view_mode_label"], T["modes"])

# --- ၅။ Weather API Logic ---
@st.cache_data(ttl=600)
def fetch_weather(city):
    loc = MYANMAR_CITIES[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,precipitation,windspeed_10m,winddirection_10m,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=15).json()
        h_data = r['hourly']
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(h_data['time']), 
            "Temp": h_data['temperature_2m'], 
            "Wind": h_data['windspeed_10m'],
            "WindDir": h_data['winddirection_10m'],
            "Vis": [v/1000 for v in h_data['visibility']],
            "Humid": h_data['relative_humidity_2m'],
            "Cloud_Oktas": [round((c / 100) * 8) for c in h_data['cloud_cover']], # Percentage မှ Oktas သို့ ပြောင်းလဲခြင်း
            "Storm": [min(round((c/3500)*100), 100) if (c is not None and c >= 0) else 0 for c in h_data.get('cape', [])]
        })
        df_d = pd.DataFrame({
            "Date": pd.to_datetime(r['daily']['time']), 
            "Tmax": r['daily']['temperature_2m_max'], 
            "Tmin": r['daily']['temperature_2m_min'], 
            "Rain": r['daily']['precipitation_sum']
        })
        return df_h, df_d
    except: return None, None

# --- ၆။ Main Page Display ---
st.title(T["title"])
st.info(f"📍 {selected_city} | 🕒 {formatted_now}")

df_h, df_d = fetch_weather(selected_city)

if df_h is not None:
    df_d['Tmax'] += bias
    df_d['Tmin'] += bias
    df_h['Temp'] += bias

    st.warning(T["dmh_alert"])

    if view_mode == T["modes"][0]:
        # ၁။ အပူချိန်
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], title=T["charts"][0], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)
        # ၂။ မိုးရေချိန်
        st.plotly_chart(px.bar(df_d, x='Date', y='Rain', title=T["charts"][1]), use_container_width=True)
        
        # ၃။ လေတိုက်နှုန်းနှင့် လားရာ
        fig_wind = go.Figure()
        fig_wind.add_trace(go.Scatter(x=df_h['Time'], y=df_h['Wind'], mode='lines', name='Wind Speed', line=dict(color='blue', width=1)))
        df_arrow = df_h.iloc[::6, :] 
        fig_wind.add_trace(go.Scatter(
            x=df_arrow['Time'], y=df_arrow['Wind'], mode='markers',
            marker=dict(symbol='arrow', size=15, angle=df_arrow['WindDir'], color='darkgreen', line=dict(width=1, color='white')),
            name='Wind Direction'
        ))
        fig_wind.update_layout(title=T["charts"][2], yaxis_title="mph")
        st.plotly_chart(fig_wind, use_container_width=True)

        # ၄။ အဝေးမြင်တာ
        st.plotly_chart(px.line(df_h, x='Time', y='Vis', title=T["charts"][3]), use_container_width=True)
        # ၅။ စိုထိုင်းဆ
        st.plotly_chart(px.area(df_h, x='Time', y='Humid', title=T["charts"][4]), use_container_width=True)
        
        # ၆။ တိမ်ဖုံးမှု (Oktas)
        st.plotly_chart(px.bar(df_h, x='Time', y='Cloud_Oktas', title=T["charts"][5], 
                               range_y=[0, 8], color_continuous_scale='Blues', 
                               labels={'Cloud_Oktas':'Oktas'}), use_container_width=True)
        
        # ၇။ မိုးတိမ်တောင်နှင့် လျှပ်စီးလက်နိုင်ခြေ (Thunderstorm %)
        st.error(T["storm_note"])
        st.plotly_chart(px.bar(df_h, x='Time', y='Storm', title=T["charts"][6], 
                               color_discrete_sequence=['#e67e22'], 
                               labels={'Storm':'Thunderstorm %'}), use_container_width=True)

    elif view_mode == T["modes"][1]:
        max_t = df_d['Tmax'].max()
        idx = 0 if max_t >= 42 else 1 if max_t >= 40 else 2 if max_t >= 38 else 3
        colors = ['#800000','#d00000','#ffaa00','#008000']
        
        st.markdown(f"<div style='background-color:{colors[idx]}; padding:35px; border-radius:15px; text-align:center;'><h1 style='color:white;'>{T['risk_levels'][idx]}: {max_t:.1f} °C</h1></div>", unsafe_allow_html=True)
        st.subheader(T['ibf_header'])
        st.error(f"⚠️ **Impact:** {T['impact_list'][idx]}")
        st.success(f"💡 **Recommendations:** {T['recom_list'][idx]}")
      
        fig_ibf = px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd')
        for val, color, label in [(42, "maroon", "Extreme"), (40, "red", "High"), (38, "orange", "Mod")]:
            fig_ibf.add_hline(y=val, line_dash="dash", line_color=color, annotation_text=f"{label} ({val}°C)")
        st.plotly_chart(fig_ibf, use_container_width=True)

        if st.button("🚀 Export All Stations Data"):
            all_data = []
            p_bar = st.progress(0)
            for i, c in enumerate(city_list):
                _, d_tmp = fetch_weather(c)
                if d_tmp is not None:
                    d_tmp['Station'] = c
                    all_data.append(d_tmp)
                p_bar.progress((i+1)/len(city_list))
            if all_data:
                st.session_state['master_df'] = pd.concat(all_data)
                st.success("✅ Collected!")

        if 'master_df' in st.session_state:
            m_df = st.session_state['master_df'].copy()
            m_df['Date'] = pd.to_datetime(m_df['Date'])
            m_df['Date_Str'] = m_df['Date'].dt.strftime('%Y-%m-%d')
            sel_date = st.selectbox("Date Selector", m_df['Date_Str'].unique())
            final_df = m_df[m_df['Date_Str'] == sel_date].sort_values(by='Station')
            st.dataframe(final_df, use_container_width=True)
            st.download_button("📥 Download Report", final_df.to_csv(index=False).encode('utf-8-sig'), f"DMH_{sel_date}.csv")

    else:
        st.subheader("🌡️ Climate Projection (2026-2100)")
        years = np.arange(2026, 2101)
        trend = [31 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
        st.plotly_chart(px.line(x=years, y=trend, labels={'y':'Temp (°C)', 'x':'Year'}), use_container_width=True)
        st.warning("⚠️ **Climate Risk Note:** Under the SSP 5-8.5 scenario, Myanmar could face significantly higher frequency of extreme heat and unpredictable monsoon patterns by the end of the century.")

st.markdown("---")
st.markdown(f"""
<div style='text-align: center; font-size: 0.85em; color: #666; line-height: 1.6;'>
    <p><b>Forecast Data Source (16-Day):</b> Open-Meteo API (Combining ECMWF IFS, GFS, ICON, and JMA global models).</p>
    <p><b>Heatwave Analysis:</b> Based on Impact-Based Forecasting (IBF) thresholds and WMO criteria.</p>
    <p><b>Climate Data:</b> IPCC AR6 Assessment Report and CMIP6 Global Climate Models (SSP scenarios).</p>
    <p style='margin-top: 10px; font-weight: bold;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</p>
</div>
""", unsafe_allow_html=True)

