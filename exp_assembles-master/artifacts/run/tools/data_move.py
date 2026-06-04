# 数据迁移，把止盈止损的评价数据定时同步到指定的目录，用于streamlit项目
import os
import time
import shutil
from artifacts.utils import load_model_config


def data_sync():
    t0 = time.time()
    target_dir = "/dfs/group/800657/COO/StrategyBacktest/winloss_data/"
    source_dir = "/dfs/group/800657/exp_results/"
    model_config = load_model_config()
    for _, exp_name, model_name, _, _ in model_config:
        print(exp_name, model_name)
        model_path = os.path.join(source_dir, exp_name, model_name)
        target_path = os.path.join(target_dir, model_name)
        os.makedirs(target_path, exist_ok=True)
        for file in os.listdir(model_path):
            if (file.startswith("mid_signal_winloss_win") or file.startswith(
                    "agg_mid_signal_winloss_win")) and file.endswith(".xlsx"):
                shutil.copy(os.path.join(model_path, file), target_path)
            if file == "winloss_detail_all.parquet":
                shutil.copy(os.path.join(model_path, file), target_path)
    print(f"评价数据同步到{target_dir}耗时{time.time()-t0} s")


if __name__ == '__main__':
    data_sync()
