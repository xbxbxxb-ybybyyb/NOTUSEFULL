import sys
sys.path.append("/data/user/quanttest007/013150/self-ats-quant-factor-engine/ats-quant-factor-engine")
from L3FactorFrame.FactorManager import FactorManager
from L3FactorFrame.MarketDataManager import MarketDataManager
import pandas as pd
import time
import os
import ray
from datetime import datetime


def UpdateFlyingFactor(symbol, date, source_factor_config, factor_path, event_path, nonfactor_path = None,
                              input_base_dir = "/dfs/group/800657/library/l3_data/",
                              save_base_dir = "/dfs/group/800657/library/l3_data/l3_factor"):
    marketDataManager = MarketDataManager(symbol, date, base_dir=input_base_dir)
    runner = FactorManager(marketDataManager)
    runner.register_factor(source_factor_config, factor_path=factor_path, event_path = event_path, nonfactor_path =nonfactor_path)
    t1 = time.time()
    # SAMPLE_1S计算模式：仅在该标的下一秒第一条数据到来时，开始计算
    runner.calc_loop(mode = "SAMPLE_1S")
    value_df = runner.get_all_factor_values(save_base_dir = save_base_dir, save_mode=True)
    factor_list = runner.get_all_factor_names()
    print(factor_list)
    print("calculate time: ", time.time()-t1)
    return value_df


if __name__=="__main__":
    ######################注意修改存储路径####################
    dates =["20240116"]
    now_date = datetime.now().strftime("%Y%m%d")
    dates = [date for date in dates if now_date>=date]
    symbols = ["688012.SH"]
    input_base_dir = "/dfs/group/800657/library/l3_data/"
    save_base_dir = "/home/appadmin/l3_factor"
    ray.init(num_cpus=2, local_mode=True)
    ######################注意修改因子配置####################

    t1 = time.time()
    source_factor_config = {
    "MDTime": [
        {}
    ],
    "Timestamp": [
        {}
    ],
    "SeqNo": [
        {}
    ],
    "Sample1sFlag":[{}],
    "ActivePriceVolume": [
        {
            "interval": 3,
            "price_spread": 0.05,
            "active_volume": 400
        }
    ],
    "FactorBuyWillingByPrice": [
        {}
    ],
    "DateTime": [
        {}
    ],
    "LevelOneChange": [
        {}
    ],
    "OneBigOrderExtend": [
        {}
    ],
    "FactorSecTradeAgg": [
        {}
    ],
    "FactorSecOrderBook": [
        {}
    ],
    "FactorSecBuySellNum": [
        {}
    ]
    }
    event_path = "./Events"  # l3因子触发计算事件目录
    factor_path = "./Factors"  # 因子计算目录
    nonfactor_path = "./NonFactors"  # 依赖因子触发目录
    tasks = []
    remote_func = ray.remote(UpdateFlyingFactor)
    for symbol in symbols:
        for date in dates[::-1]:
            tasks.append(remote_func.remote(symbol, date, source_factor_config, factor_path, event_path, nonfactor_path, 
                                            input_base_dir = input_base_dir, save_base_dir = save_base_dir))
    ray.get(tasks)
    print("耗时：", time.time()-t1)