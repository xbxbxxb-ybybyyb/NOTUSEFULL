
import pandas as pd
import os
from artifacts.utils import save_winloss_data

# base_path = "/data/user/quanttest005/K0380021/winloss_data"
base_path = "/dfs/group/800657/COO/StrategyBacktest/winloss_data"
model_list = ["HS_l2p2","HS_tick2_new","HS_l2p","HS_tick2_add","hs300_px_lvl_45","hs300_px_lvl_123"]


for model in model_list:
    model_path = os.path.join(base_path, model)
    if not os.path.exists(model_path):
        continue
    for file in os.listdir(model_path):
        df_list = []
        if file.startswith("mid_signal_winloss_win1.5_loss2.0_pred") and file.endswith(".xlsx"):
            target_file = file[:-4] + "parquet"
            target_file_path = file_path = os.path.join(model_path, target_file)
            file_path = os.path.join(model_path, file)
            xls = pd.ExcelFile(file_path)
            stocks = xls.sheet_names
            data_dict = pd.read_excel(file_path, sheet_name=stocks)
            for symbol in data_dict.keys():
                df_p = data_dict[symbol]
                df_list.append(df_p)
        if df_list:
            df = pd.concat(df_list)
            save_winloss_data(df, save_parquet_path=target_file_path, sub_cols=["日期", "标的"])





