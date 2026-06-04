import sys
sys.path.append("/data/user/quanttest007/013150/self-ats-quant-factor-engine/ats-quant-factor-engin/build")
import time
import os
import ray
from datetime import datetime
import polars as pl
import json
import pandas as pd
import pyarrow as pa

# @ray.remote(max_calls = 1)
# @ray.remote
def UpdateFlyingFactor(symbol, date, factor_config, input_base_dir = "/root/codes/ats-quant-factor-engine/dataset", 
                       save_base_dir = "/dfs/group/800657/library/l3_event/event_data/"):
    sys.path.append("/data/user/quanttest007/013150/self-ats-quant-factor-engine/ats-quant-factor-engine")
    sys.path.append("/data/user/quanttest007/013150/self-ats-quant-factor-engine/ats-quant-factor-engine/build")
    from atsfactor import FactorManager, MarketDataManagerOption, ArrowTableMarketDataManager
    from L3FactorFrame.MarketDataManager import get_l3_data_cpp
    import time
    option = MarketDataManagerOption()
    option.type = MarketDataManagerOption.MarketDataManagerType.ARROW_TABLE
    # factor_config["name"] = symbol+date+str(int(time.time()*10000//10000))
    param = json.dumps(factor_config)
    print(param)
    fm = FactorManager(param, option)

    tick_df = get_l3_data_cpp(symbol, date, base_dir=input_base_dir)
    table = pa.table(tick_df.to_pandas())
    mdm = ArrowTableMarketDataManager(table)

    t1 = time.time()
    l = []
    while not mdm.is_end():
        mdm.next()
        fm.caculate()
        l.append(fm.values())
    value_df = pd.DataFrame(l, columns = [i["type"] for i in factor_config["factors"]])
    value_df = pl.from_pandas(value_df)
    print("calculate time: ", time.time()-t1)
    # print(fm)
    return value_df


if __name__=="__main__":
    symbol = "688981.SH"
    date = "20240617"
    factor_config = {
    "factors":  [
            {"type": "FactorBuyWillingByPrice", "dependencies":["FactorSecTradeAgg"]},
            {"type":"FactorSecTradeAgg"},                                
            {'type': 'FactorNSWSellMaxPriceCurCum','dependencies':['FactorSecOrderBook']},
            {'type': "FactorSecOrderBook"},
            {'type':'FactorSecBuySellNum'},
            {'type': 'FactorSellNumCorr3','dependencies':['FactorSecBuySellNum']},
            {'type':'FactorSeqNo'},
    ],
            "sample_1s" : True #是否只在该标的，每秒的第一条计算
    }

    input_base_dir = "/data/user/quanttest007/013150/self-ats-quant-factor-engine/ats-quant-factor-engine/dataset/"
    save_base_dir = "/data/user/quanttest007/013150/self-ats-quant-factor-engine/ats-quant-factor-engine/tmp/"
    value_df = UpdateFlyingFactor(symbol, date, factor_config,input_base_dir=input_base_dir,
                            save_base_dir = save_base_dir)
    print(value_df)