import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

class DMHForecastVerification:
    def __init__(self, df_forecast, df_observed):
        """
        df_forecast: Mode ၇ ခုရဲ့ ခန့်မှန်းချက်ပါဝင်သော DataFrame (Columns: Date, Station, Mode_1, ..., Mode_7)
        df_observed: မြေပြင်တိုင်းထွာချက် DataFrame (Columns: Date, Station, Actual_Temp)
        """
        self.df_forecast = df_forecast
        self.df_observed = df_observed
        self.modes = [f"Mode_{i}" for i in range(1, 8)] # Mode_1 မှ Mode_7 အထိ

    def merge_data(self):
        """ ခန့်မှန်းချက်နှင့် မြေပြင်ဒေတာကို Date နှင့် Station အလိုက် ပေါင်းခြင်း """
        # Date format များကို စိတ်ချရအောင် datetime format ပြောင်းထားခြင်း
        self.df_forecast['Date'] = pd.to_datetime(self.df_forecast['Date'])
        self.df_observed['Date'] = pd.to_datetime(self.df_observed['Date'])
        return pd.merge(self.df_forecast, self.df_observed, on=['Date', 'Station'], how='inner')

    def calculate_all_modes(self):
        """ Mode ၇ ခုလုံးရဲ့ Metrics ကို တစ်ပြိုင်နက် တွက်ချက်ခြင်း """
        merged_df = self.merge_data()
        
        # တွက်ချက်မှုရလဒ် သိမ်းဆည်းရန် Dictionary
        results = {}
        
        if merged_df.empty:
            return pd.DataFrame() # ဒေတာမရှိပါက ဇယားကွက်အလွတ်ပြန်ပေးမည်

        for mode in self.modes:
            # Null value များကို ဖယ်ထုတ်ခြင်း (Robustness)
            valid_data = merged_df[[mode, 'Actual_Temp']].dropna()
            
            if len(valid_data) > 0:
                y_pred = valid_data[mode]
                y_true = valid_data['Actual_Temp']
                
                # Metrics များ တွက်ချက်ခြင်း
                mae = mean_absolute_error(y_true, y_pred)
                rmse = np.sqrt(mean_squared_error(y_true, y_pred))
                r2 = r2_score(y_true, y_pred)
                
                results[mode] = {
                    "MAE (°C)": round(mae, 2),
                    "RMSE (°C)": round(rmse, 2),
                    "R² Score": round(r2, 3),
                    "Data Count": int(len(valid_data))
                }
            else:
                results[mode] = {
                    "MAE (°C)": np.nan, 
                    "RMSE (°C)": np.nan, 
                    "R² Score": np.nan, 
                    "Data Count": 0
                }
                
        # DataFrame ပြောင်းလဲပြီး Return ပြန်ပေးခြင်း
        return pd.DataFrame(results).T
