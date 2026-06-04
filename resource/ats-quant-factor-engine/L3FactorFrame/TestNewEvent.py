from L3FactorFrame.FactorManager import FactorManager
from L3FactorFrame.MarketDataManager import MarketDataManager
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
    runner.calc_loop(mode = "ESAMPLE")
    value_df = runner.get_all_factor_values(save_base_dir = save_base_dir, save_mode=True)
    print(value_df.columns)
    print("calculate time: ", time.time()-t1)

if __name__=="__main__":
    ######################注意设置标的和日期####################
    from xquant.factordata import FactorData
    fa = FactorData()
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
    dates = fa.tradingday("20240301", "20240631")
    now_date = datetime.now().strftime("%Y%m%d")
    dates = [date for date in dates if now_date>=date]
    print(symbols)
    print(dates)
    ######################注意修改存储路径####################
    save_base_dir = "/dfs/group/800657/library/tmp_l3_event/event_data/"
    factor_path = "./Factors"  # 事件触发计算因子目录
    event_path = "./Events" # 事件触发计算事件目录
    source_factor_config = {
        "DateTime": [
            {}
        ],
        "Timestamp": [
            {}
        ],
        "SeqNo": [
            {}
        ],
        "MDTime": [
            {}
        ],
        # "BreakingThinVol": [
        #     {"interval": 0.055,
        #      "breaking_num": 3,
        #      }
        # ],
        # "BuySellReverse": [
        #     {"interval": 0.055,
        #      "ob_vol_multi":10,
        #      "spread_ratio": 0.5
        #      },
        # ],
        "OneBigOrderExtend": [
            {
                "spread_ratio": 0.5
            }
        ]
    }
    # for pressure_multi in [10, 20, 30]:
    #     for net_multi in  [2, 3, 5]:
    #         source_factor_config["BuySellReverse"].append(
    #          {"interval": 0.1,
    #          "pressure_multi":pressure_multi,
    #          "net_multi": net_multi
    #          },)
    # for spread in  [0.2, 0.3, 0.5]:
    #     source_factor_config["OneBigOrderExtend"].append(
    #      {
    #      "spread_ratio": spread
    #      },)

    for a in  [1, 2]:
        for b in [0.5, 0.75, 1.5]:
            source_factor_config["OneBigOrderExtend"].append(
             {
                 "a": a,
                 "b": b
             },)
    print(json.dumps(source_factor_config, indent=4))
    ray.init(num_cpus=35, local_mode=False)
    ##########################################################
    t1 = time.time()
    tasks = []
    remote_func = ray.remote(UpdateFlyingFactorEsample)
    for symbol in symbols:
        for date in dates[::-1]:
            tasks.append(remote_func.remote(symbol, date, source_factor_config, factor_path, event_path, save_base_dir = save_base_dir))
    ray.get(tasks)
    print("耗时：", time.time()-t1)