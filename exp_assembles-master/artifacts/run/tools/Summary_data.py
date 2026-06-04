from artifacts.utils import save_winloss_data_xlsx
import pandas as pd
import os
import re
import time


def summary_data(source_path, target_path, model_name):
    model_path_src = os.path.join(source_path, model_name)
    model_path_dst = os.path.join(target_path, model_name)
    os.makedirs(model_path_dst, exist_ok=True)
    file_pattern = f"mid_signal_winloss_win(\d+(\.\d+)?)_loss(\d+(\.\d+)?)_pred(\d+(\.\d+)?)" + ".xlsx"
    file_pattern_percent = f"mid_signal_winloss_win(\d+(\.\d+)?)_loss(\d+(\.\d+)?)_pred_percent(\d+)" + ".xlsx"
    for f in os.listdir(model_path_src):
        match1 = re.match(file_pattern, f)
        match2 = re.match(file_pattern_percent, f)
        res_df_list = []
        if match1 or match2:
            winloss_file = os.path.join(model_path_src, f)
            xls = pd.ExcelFile(winloss_file)
            sheet_names = xls.sheet_names
            res_df_dict = pd.read_excel(winloss_file, sheet_name=sheet_names)
            for sheet in sheet_names:
                res_df_s = res_df_dict[sheet]
                res_df_list.append(res_df_s)
        if res_df_list:
            res_df = pd.concat(res_df_list)
            res_out_path = os.path.join(model_path_dst, f)
            save_winloss_data_xlsx(res_df, sign_col="标的", output_path=res_out_path, overwrite_col="日期")


if __name__ == '__main__':
    t0 = time.time()
    source_path = "/dfs/group/800657/exp_results/KG101_model"
    target_path = "/dfs/group/800657/COO/StrategyBacktest/winloss_data"
    model_list = ["HS_l2p", "HS_l2p2", "HS_tick2_add", "HS_tick2_new"]
    for version_alias in model_list:
        print(version_alias)
        summary_data(source_path, target_path, version_alias)
    # version_alias = "hs300_px_lvl_123"
    # summary_data(source_path, target_path, version_alias)
    print(f"汇总数据耗时：{ time.time() - t0} s")


