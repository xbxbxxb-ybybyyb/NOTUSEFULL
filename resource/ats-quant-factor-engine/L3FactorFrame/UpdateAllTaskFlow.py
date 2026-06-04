from UpdateL3Data import UpdateL3Data
from UpdateVolQuantile import UpdateVolQuantile
from UpdateFlyingFactorEsample import UpdateFlyingFactorEsample
from UpdateFlyingFactorFull import UpdateFlyingFactorFull
import time
import ray
import os
import json
import pandas as pd
from datetime import datetime
from xquant.factordata import FactorData

if __name__=="__main__":
    ######################注意设置标的和日期####################
    fa = FactorData()
    symbols_all = fa.hset("INDEX", "20240130", "000688.SH")["stock"].tolist()
    symbols = symbols_all
    hs300_flag = False
    if not hs300_flag:
        symbols = pd.read_csv("kc_amt_swing.csv", header=None)[0].tolist()
        # symbols = pd.read_csv("kc50.csv", header=None)[0].tolist()
        symbols1 = pd.read_csv("zz500_select74.csv", header=None)[0].tolist()
        symbols = list(set(symbols + symbols1))
    else:
        symbols = pd.read_csv("/dfs/group/800657/exp_results/zz500_dataset/hs300_sh.csv", header=None)[0].tolist()
        symbols1 = pd.read_csv("/dfs/group/800657/exp_results/zz500_dataset/hs300_sz.csv", header=None)[0].tolist()
        symbols = sorted(list(set(symbols + symbols1)))
    # symbols = ["688981.SH"]
    # dates = fa.tradingday("20220101", "20240610")
    dates = fa.tradingday("20220101", "20240711")
    # dates = ["20240516"]
    now_date = datetime.now().strftime("%Y%m%d")
    dates = [date for date in dates if now_date>=date]
    # symbols = ["688041.SH"]#["688032.SH", "688041.SH", "688256.SH","688111.SH", "688271.SH","688012.SH", "688981.SH"]
    # dates = ["20220107"]#,"20240129", "20240130"]
    print(symbols)
    print(dates)
    ######################注意修改存储路径####################
    updateL3Data = True
    updateFlyingFactorEsample = True
    save_base_dir = "/dfs/group/800657/library/l3_event/event_data/"
    factor_path = "./Factors"  # 事件触发计算因子目录
    event_path = "./Events"
    source_factor_config = json.load(open(os.path.join(factor_path, "./factor_config_all.json"), "r"))
    source_factor_config.update(json.load(open(os.path.join(event_path, "./factor_config_all.json"), "r")))
    print(json.dumps(source_factor_config, indent=4))
    time.sleep(5)
    ray.init(num_cpus=30, local_mode=False)
    ######################Task0####################
    if updateL3Data:
        tasks = []
        remote_func = UpdateL3Data
        for symbol in symbols:
            for date in dates[::-1]:
                tasks.append(remote_func.remote(symbol, date))
        error_date = ray.get(tasks)
        error_date = [i for i in error_date if not len(i)==0]
        print("UpdateL3Data finish ! error_date:", error_date)


    ######################Task2、3####################
    if updateFlyingFactorEsample:
        for task_func in [UpdateFlyingFactorEsample]:#[UpdateFlyingFactorFull]:
            t1 = time.time()
            tasks = []
            remote_func = UpdateFlyingFactorEsample#ray.remote(task_func)
            for symbol in symbols:
                for date in dates[::-1]:
                    tasks.append(remote_func.remote(symbol, date, source_factor_config, factor_path, event_path, save_base_dir=save_base_dir))
            ray.get(tasks)
            print("{}耗时：".format(task_func.__name__), time.time() - t1)

