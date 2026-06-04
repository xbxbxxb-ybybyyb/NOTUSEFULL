import sys
sys.path.append("/data/user/quanttest007/013150/self-ats-quant-factor-engine/ats-quant-factor-engine")
from L3FactorFrame.FactorManager import FactorManager
from L3FactorFrame.MarketDataManager import MarketDataManager
import pandas as pd
import time
import os
import ray
from datetime import datetime


def UpdateFlyingFactorEsample(symbol, date, source_factor_config, factor_path, event_path, nonfactor_path = None, 
                              input_base_dir = "/dfs/group/800657/library/l3_data/",
                              save_base_dir = "/dfs/group/800657/library/l3_event/event_data/"):
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
symbol = "688981.SH"
date = "20240617"

event_path = "./L3FactorFrame/Events" # l3事件触发计算事件目录
factor_path = "./L3FactorFrame/Factors" # 因子触发计算事件目录
nonfactor_path = "./L3FactorFrame/NonFactors" # 依赖因子触发计算事件目录

input_base_dir = "/data/user/quanttest007/013150/self-ats-quant-factor-engine/ats-quant-factor-engine/dataset"
save_base_dir = "/data/user/quanttest007/013150/self-ats-quant-factor-engine/ats-quant-factor-engine/tmp/"

py_value_df = UpdateFlyingFactorEsample(symbol, date, source_factor_config, factor_path, event_path, nonfactor_path,
                           input_base_dir = input_base_dir, save_base_dir = save_base_dir)
print(py_value_df)
