import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from verification_engine import DMHForecastVerification

def render_verification_page():
    st.title("📊 DMH AI Forecast Automation Audit")
    st.write("Mode ၇ ခုလုံး၏ ခန့်မှန်းချက် တိကျမှု အရည်အသွေးကို တစ်ပြိုင်နက် စစ်ဆေးခြင်း။")
    
    # --- ဒေတာ Load လုပ်ခြင်း နမူနာ (မိမိတို့ Database/CSV နှင့် ချိတ်ဆက်ရန်) ---
    # df_forecast = load_forecast_data()
    # df_observed = load_observed_data()
    
    # ယာယီစမ်းသပ်ရန် Mock Data (ဥပမာပြရန်သာ)
    df_forecast = st.session_state.get('df_forecast', pd.DataFrame())
    df_observed = st.session_state.get('df_observed', pd.DataFrame())

    if df_forecast.empty or df_observed.empty:
        st.warning("⚠️ စစ်ဆေးရန် ခန့်မှန်းချက်ဒေတာ နှင့် မြေပြင်ဒေတာများ မရှိသေးပါ။")
        return

    # --- 1. Global Metrics Summary (Mode အားလုံးကို တစ်ပြိုင်နက်ပြသခြင်း) ---
    st.subheader("📋 ခြုံငုံသုံးသပ်ချက် Accuracy Matrix (All 7 Modes)")
    
    verifier = DMHForecastVerification(df_forecast, df_observed)
    summary_df = verifier.calculate_all_modes()
    
    if not summary_df.empty:
        # အရောင်ဖြင့် ခွဲခြားပြသခြင်း (Style Gradient)
        st.dataframe(summary_df.style.background_gradient(cmap='Blues', subset=['MAE (°C)', 'RMSE (°C)']))
        
        # CSV အဖြစ် Export ထုတ်ရန် Button
        csv = summary_df.to_csv().encode('utf-8')
        st.download_button("📥 Export Audit Report (CSV)", csv, "DMH_Model_Audit_Report.csv", "text/csv")
    else:
        st.error("ဒေတာများ ပေါင်းစပ်ရာတွင် လွဲချော်မှုရှိနေပါသည်။ Date နှင့် Station Format ကို စစ်ဆေးပါ။")

    st.markdown("---")

    # --- 2. Single Mode Deep-Dive (ရွေးချယ်ထားသော Mode တစ်ခုချင်းစီကို Graph ဖြင့် ယှဉ်ကြည့်ခြင်း) ---
    st.subheader("🔍 Mode တစ်ခုချင်းစီအလိုက် Time-Series တိုက်ဆိုင်စစ်ဆေးခြင်း")
    
    selected_mode = st.selectbox("စစ်ဆေးလိုသော Mode ကို ရွေးချယ်ပါ -", [f"Mode_{i}" for i in range(1, 8)])
    
    merged_data = verifier.merge_data()
    
    if not merged_data.empty:
        # Plotly Time-series Chart တည်ဆောက်ခြင်း
        fig = go.Figure()
        
        # AI Forecast Line
        fig.add_trace(go.Scatter(
            x=merged_data['Date'], y=merged_data[selected_mode],
            mode='lines+markers', name=f'AI Forecast ({selected_mode})',
            line=dict(color='#1f77b4', width=2)
        ))
        
        # Actual Observed Line
        fig.add_trace(go.Scatter(
            x=merged_data['Date'], y=merged_data['Actual_Temp'],
            mode='lines+markers', name='Actual Observed (မြေပြင်)',
            line=dict(color='#ff7f0e', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title=f"{selected_mode} ခန့်မှန်းချက်နှင့် မြေပြင်တိုင်းထွာချက် နှိုင်းယှဉ်မှု ဂရပ်",
            xaxis_title="နေ့စွဲ (Date)",
            yaxis_title="အပူချိန် (Temperature °C)",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
