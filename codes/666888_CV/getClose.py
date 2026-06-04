import DataAPI.DataToolkit as dtk
import pandas as pd

ss = pd.read_csv("/data/user/666888/AlgoGenzong/portfolios/500WeightsNew.csv")
cl = dtk.get_panel_daily_pv_df(ss["stock"].tolist(), 20200102, 20200102).loc[20200102]
ss = ss.set_index("stock")
ss["weight"] /= cl
ss.reset_index()
ss.to_excel("/data/user/666888/AlgoGenzong/portfolios/zz500.xlsx")