import sys
sys.path.append("../")
from L3FactorFrame.UpdateL3Data import UpdateL3Data
from L3FactorFrame.UpdateFlyingFactorFull import UpdateFlyingFactorFull
from UpdateVolQuantile import UpdateVolQuantile
from stock_pool import get_stock_pool
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

    symbols_all = get_stock_pool(["ALL"])
    symbols_factor = get_stock_pool(["HS300", "HS_tick_all"])
    now_date = datetime.now().strftime("%Y%m%d")
    try:
        dates = [sys.argv[1]]
        num_cpus = 15
    except:
        dates = fa.tradingday("20240929", "20241104")
        dates = [date for date in dates if now_date >= date]
        num_cpus = 25
    # symbols = ["688032.SH", "688041.SH", "688256.SH","688111.SH", "688271.SH","688012.SH", "688981.SH"]
    # dates = ["20220110"]#,"20240129", "20240130"]
    print(len(symbols_all), symbols_all)
    print(dates)
    ######################注意修改存储路径####################
    updateL3Data = True
    updateVolQuantile = True
    updateFlyingFactorFull = True
    save_base_dir = "/dfs/group/800657/library/l3_event/event_data/"
    factor_path = "../Factors"  # 事件触发计算因子目录
    event_path = "../Events"
    source_factor_config = json.load(open(os.path.join(factor_path, "./factor_config.json"), "r"))
    source_factor_config.update(json.load(open(os.path.join(event_path, "./factor_config.json"), "r")))
    print(json.dumps(source_factor_config, indent=4))
    time.sleep(5)
    ray.init(num_cpus=num_cpus, local_mode=False)
    ######################Task0####################
    if updateL3Data:
        tasks = []
        remote_func = UpdateL3Data
        for symbol in symbols_all:
            for date in dates[::-1]:
                tasks.append(remote_func.remote(symbol, date))
        error_date = ray.get(tasks)
        error_date = [i for i in error_date if not len(i)==0]
        print("UpdateL3Data finish ! error_date:", error_date)

    ######################Task1####################
    if updateVolQuantile:
        t1 = time.time()
        lookback_days = 5
        remote_func = UpdateVolQuantile
        event_params_dict = dict()
        tasks = [remote_func.remote(code, dates, lookback_days=lookback_days) for code in symbols_factor]
        results = ray.get(tasks)
        for result in results:
            event_params_dict[result[0]] = result[1]
        print("UpdateVolQuantile耗时：", time.time()-t1)

    ######################Task2、3####################
    if updateFlyingFactorFull:
        for task_func in [UpdateFlyingFactorFull]:
            t1 = time.time()
            tasks = []
            remote_func = UpdateFlyingFactorFull
            for symbol in symbols_factor:
                for date in dates[::-1]:
                    tasks.append(remote_func.remote(symbol, date, source_factor_config, factor_path, event_path, save_base_dir=save_base_dir))
            ray.get(tasks)
            print("{}耗时：".format(task_func), time.time() - t1)


