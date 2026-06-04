from FactorManager import FactorManager
from MarketDataManager import MarketDataManager
import pandas as pd
import time
import os
import ray
import json
from datetime import datetime


# FULL全量计算模式

def UpdateFlyingFactorFull(symbol, date, source_factor_config, factor_path, event_path =None, save_base_dir = "/dfs/group/800657/library/l3_event/event_data/"):
    try:
        marketDataManager = MarketDataManager(symbol, date)
        runner = FactorManager(marketDataManager)
        runner.register_factor(source_factor_config, factor_path = factor_path)
        t1 = time.time()
        # 全量计算模式
        runner.calc_loop(mode="FULL")
        value_df = runner.get_all_factor_values(save_base_dir = save_base_dir, save_mode=False)
        # print(value_df)
        print("calculate time: ", time.time()-t1)
    except Exception as e:
        print("ERROR: UpdateFlyingFactorFull, ", e, symbol, date)

if __name__=="__main__":
    ######################注意设置标的和日期####################
    from xquant.factordata import FactorData
    fa = FactorData()
    symbols_all = fa.hset("INDEX", "20240130", "000688.SH")["stock"].tolist()
    symbols = symbols_all
    dates = fa.tradingday("20240301", "20240408")
    now_date = datetime.now().strftime("%Y%m%d")
    dates = [date for date in dates if now_date>=date]
    # symbols = ["688012.SH"]#["688032.SH", "688041.SH", "688256.SH","688111.SH", "688271.SH","688012.SH", "688981.SH"]
    # dates = ["20220107"]#,"20240129", "20240130"]
    print(symbols)
    print(dates)
    ######################注意修改存储路径####################
    save_base_dir = "/dfs/group/800657/library/l3_event/event_data/"
    factor_path = "./Factors" # 全量计算因子目录
    # factor_path = "./Events" # 全量计算事件目录
    source_factor_config = json.load(open(os.path.join(factor_path, "./factor_config_all.json"), "r"))
    print(json.dumps(source_factor_config, indent = 4))
    time.sleep(5)
    ##########################################################
    ray.init(num_cpus=25, local_mode=False)
    t1 = time.time()
    tasks = []
    remote_func = ray.remote(UpdateFlyingFactorFull)
    for symbol in symbols:
        for date in dates[::-1]:
            tasks.append(remote_func.remote(symbol, date, source_factor_config, factor_path, save_base_dir = save_base_dir))
    ray.get(tasks)
    print("耗时：", time.time()-t1)