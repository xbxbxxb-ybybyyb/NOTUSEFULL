from FactorManager import FactorManager
from MarketDataManager import MarketDataManager
import pandas as pd
import time
import os
import ray
from datetime import datetime
import json

# ESAMPLE事件触发计算模式
def UpdateFlyingFactorEsample(symbol, date, source_factor_config, factor_path, event_path, save_base_dir = "/dfs/group/800657/library/l3_event/event_data/"):
    marketDataManager = MarketDataManager(symbol, date)
    runner = FactorManager(marketDataManager)
    runner.register_factor(source_factor_config, factor_path=factor_path, event_path = event_path)
    t1 = time.time()
    runner.calc_loop(mode = "FULL")
    value_df = runner.get_all_factor_values(save_base_dir = save_base_dir, save_mode=True)
    factor_list = runner.get_all_factor_names()
    print(factor_list)
    print(value_df)
    print("calculate time: ", time.time()-t1)

if __name__=="__main__":
    ######################注意设置标的和日期####################
    from xquant.factordata import FactorData
    fa = FactorData()
    # symbols_all = fa.hset("INDEX", "20240130", "000688.SH")["stock"].tolist()
    # symbols = set(symbols_all) - set(symbols)
    # symbols = symbols_all
    # symbols = ["688032.SH", "688041.SH", "688256.SH","688111.SH", "688271.SH","688012.SH", "688981.SH"]
    # symbols = pd.read_csv("zz500.csv", header=None)[0].tolist()
    symbols = pd.read_csv("kc_amt_swing.csv", header=None)[0].tolist()
    # symbols = pd.read_csv("kc50.csv", header=None)[0].tolist()
    symbols1 = pd.read_csv("zz500_select74.csv", header=None)[0].tolist()
    symbols = list(set(symbols + symbols1))[:1]
    dates = fa.tradingday("20220101", "20240710")[-10:]
    now_date = datetime.now().strftime("%Y%m%d")
    dates = [date for date in dates if now_date>=date]
    dates = fa.tradingday("20240715", "20240723")
    symbols = [
        #  '300073.SZ',
        # # "300114.SZ",
        # #   '300724.SZ',
        # #   '002432.SZ',
        '688047.SH',
        # '688390.SH',
        '688506.SH',
        # '688032.SH',
        # '600038.SH',
        # '688301.SH',
        '688041.SH',
        '688256.SH',
        '688271.SH',
        '688981.SH',
        # '603688.SH',
        '688498.SH',
        '688012.SH',
        "688981.SH"
    ]
    symbols = ["688981.SH"]
    # dates = ["20240614"]#,"20240129", "20240130"]
    print(symbols)
    print(dates)
    ######################注意修改存储路径####################
    save_base_dir = "/dfs/group/800657/library/l3_event/tmp_event_data1/"
    os.makedirs(save_base_dir, exist_ok= True)
    factor_path = "./FactorsTest"  # 事件触发计算因子目录
    event_path = "./Events" # 事件触发计算事件目录
    source_factor_config = json.load(open(os.path.join(factor_path, "./factor_config_sample.json"), "r"))
    source_factor_config.update(json.load(open(os.path.join(event_path, "./factor_config_tmp.json"), "r")))
    print(json.dumps(source_factor_config, indent=4))
    time.sleep(5)
    ray.init(num_cpus=15, local_mode=True)
    ##########################################################
    t1 = time.time()
    tasks = []
    remote_func = ray.remote(UpdateFlyingFactorEsample)
    for symbol in symbols:
        for date in dates[::-1]:
            tasks.append(remote_func.remote(symbol, date, source_factor_config, factor_path, event_path, save_base_dir = save_base_dir))
    ray.get(tasks)
    print("耗时：", time.time()-t1)