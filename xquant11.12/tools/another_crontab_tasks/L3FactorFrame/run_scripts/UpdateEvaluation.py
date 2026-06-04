from L3FactorFrame.FactorManager import FactorManager
from L3FactorFrame.MarketDataManager import MarketDataManager
import pandas as pd
import time
import ray
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from L3FactorFrame.MarketDataManager import get_l3_data
from tqdm import tqdm
from datetime import datetime
import pickle
import copy
import os
import json

def evaluate(label_df, event_df):
    label_name = label_df.columns[0]
    factor_list = [col for col in event_df.columns.tolist() if col !="Timestamp"]
    event_df["timestamp"] = event_df["Timestamp"].apply(lambda x: datetime.fromtimestamp(x - 3600 * 8))
    edf = event_df.set_index('timestamp')

    how_method_dict = {
        'ActivePriceVolume': "sum",
        'BreakingP0NumOrders': 'sum',
        'OneBigOrder': 'sum',
        'CumOrdersNetVolOverV0': 'sum',
        'PriceSpread': 'sum',
        'P0V0Change': 'sum',
        "FacActivePVBuy": "sum",
        "FacActivePVSell": "sum",
        "Timestamp":"last"
    }
    how_method_dict = {k:v for k,v in how_method_dict.items() if k in factor_list}
    edf_resample = edf.resample(rule='1s', closed='left', label='right').agg(
        how_method_dict)
    merge_df = pd.merge(edf_resample, label_df, left_index=True, right_index=True)
    merge_df["MDTime"] = merge_df.index
    merge_df["MDTime"] = merge_df["MDTime"].apply(lambda x: x.strftime("%H%M%S%f")[:-3])
    merge_df = merge_df[(merge_df["MDTime"] >= "093303000") & (merge_df["MDTime"] <= "113003000") | (
                merge_df["MDTime"] >= "130003000") & (merge_df["MDTime"] <= "145700000")]
    merge_df[label_name].mean()

    # print("NOTE!!!注意确保Buy方向事件为正值，Sell方向事件为负值")
    result11 = {}

    for factor in factor_list:
        result_buy = merge_df[merge_df[factor] > 0][label_name].describe()
        result_sell = merge_df[merge_df[factor] < 0][label_name].describe()
        for key in result_buy.to_dict():
            if key in ["count", "mean", "50%"]:
                result11[factor + "-pos_label_"+key] = result_buy[key]
        for key in result_sell.to_dict():
            if key in ["count", "mean", "50%"]:
                result11[factor+"-neg_label_"+key] = result_sell[key]

    return result11

def func_inner(label_df, factor_config, symbol, date, **kwargs):
    marketDataManager = MarketDataManager(symbol, date)
    runner = FactorManager(marketDataManager)
    runner.register_factor(factor_config)
    t1 = time.time()
    runner.calc_loop()
    print("calculate time: ", time.time() - t1)

    error_list = runner.get_error_instance()
    if error_list:
        print("ERROR INSTANCE:", error_list)
    value_df = runner.get_all_factor_values()
    try:
        if not value_df.empty:
            result = evaluate(label_df, value_df)
            result.update(**kwargs)
            result.update({"symbol":symbol, "date":date})
        else:
            result = {}
    except:
        result ={}
    return result

def modify_factor_config(source_factor_config, factor_name, **kwargs):
    factor_config = copy.deepcopy(source_factor_config)
    factor_config[factor_name][0].update(**kwargs)
    return factor_config

def main(symbol, date, factor_list = ["ActivePriceVolume"]):
    fd = FactorProvider("016869")
    data_type = "tick_l2p"
    label_name = "LabelFirstPeak_th10_120s"
    start_date, end_date = date, date

    label_df = fd.load_public_data_from_dfs(symbol=[symbol], factor_list=[label_name],
                                            start_time=start_date, end_time=end_date, factor_type="label", data_type = data_type)
    label_df = label_df.set_index("timestamp")[[label_name]]
    label_df_id = ray.put(label_df)
    get_l3_data(symbol, date, use_pandas=False, base_dir="/dfs/group/800657/library/l3_data")

    source_factor_config = {
          "Timestamp": [
            {}
          ],
           "SeqNo": [
            {}
          ],
          "ActivePriceVolume": [
            {"interval": 3,
             "price_spread": 0.0012,
             "active_volume": 400
            }
          ],
          "BreakingP0NumOrders": [
            {"interval": 0.055,
            "continuous_num": 5
            }
          ],
          "OneBigOrder": [
            {}
          ],
          "CumOrdersNetVolOverV0": [
            {
              "interval": 0.055
            }
          ],
          "PriceSpread": [
            {"spread_ratio": 0.1}
          ],
           "P0V0Change": [
            {}
          ],
        "FacActivePVBuy": [
            {"interval": 3,
             "price_spread": 0.0012,
             "active_volume": 400,
             "active_trade_price": 0.0008,
             }
        ],
        "FacActivePVSell": [
            {"interval": 3,
             "price_spread": 0.0012,
             "active_volume": 400,
             "active_trade_price": 0.0008,
             }
        ],
    }

    min_a = -100
    min_b = -100

    remote_func = ray.remote(func_inner)
    tasks = []
    source_factor_config = {k: v for (k, v) in source_factor_config.items() if k in factor_list+["Timestamp"]}
    if sorted(factor_list) == sorted(["ActivePriceVolume"]):
        for interval in [3, 5, 10]:
            for price_spread in [0.0012, 0.001]:
                for active_volume in [400, 800, 1200, 2000]:
                    kwargs = dict(zip(["interval", "price_spread", "active_volume"], [interval, price_spread, active_volume]))
                    sub_factor_config = modify_factor_config(source_factor_config, "ActivePriceVolume", **kwargs)
                    tasks.append(remote_func.remote(label_df_id, sub_factor_config, symbol, date, **kwargs))
    if sorted(factor_list) == sorted(["FacActivePVBuy", "FacActivePVSell"]):
        for interval in [3, 5, 10]:
            for price_spread in [0.0012, 0.001]:
                for active_volume in [400, 600]:
                    for active_trade_price in [0.0008, 0.0006]:
                        kwargs = dict(zip(["interval", "price_spread", "active_volume", "active_trade_price"], [interval, price_spread, active_volume, active_trade_price]))
                        sub_factor_config = modify_factor_config(source_factor_config, "FacActivePVBuy", **kwargs)
                        sub_factor_config = modify_factor_config(sub_factor_config, "FacActivePVSell", **kwargs)
                        tasks.append(remote_func.remote(label_df_id, sub_factor_config, symbol, date, **kwargs))
    elif sorted(factor_list) == sorted(["BreakingP0NumOrders", "CumOrdersNetVolOverV0"]):
        for interval in [0.055, 0.1, 0.2, 0.4]:
            for continuous_num in [4, 6, 8]:
                kwargs = dict(zip(["interval", "continuous_num"],[interval, continuous_num]))
                sub_factor_config = modify_factor_config(source_factor_config, "BreakingP0NumOrders", **kwargs)
                sub_factor_config = modify_factor_config(sub_factor_config, "CumOrdersNetVolOverV0", **kwargs)
                tasks.append(remote_func.remote(label_df_id, sub_factor_config, symbol, date, **kwargs))
    elif sorted(factor_list) == sorted(["PriceSpread"]):
        for spread_ratio in [0.05, 0.08, 0.1, 0.2]:
            kwargs = {"spread_ratio": spread_ratio}
            sub_factor_config = source_factor_config
            tasks.append(remote_func.remote(label_df_id, sub_factor_config, symbol, date, **kwargs))
    elif set(factor_list).issubset(["OneBigOrder"]):
        kwargs = {}
        sub_factor_config = source_factor_config
        tasks.append(remote_func.remote(label_df_id, sub_factor_config, symbol, date, **kwargs))
    else:
        raise Exception()

    result_dict_list = ray.get(tasks)
    result_dict_list = [i for i in result_dict_list if len(i)!=0]
    result_df = pd.DataFrame(result_dict_list)
    if kwargs:
        result_df = result_df.sort_values(by = list(kwargs.keys()))
    return result_df

def get_dates(start_date = "20231201", end_date = "20240229"):
    from xquant.factordata import FactorData
    fa = FactorData()
    dates = fa.tradingday(start_date, end_date)
    return dates

if __name__=="__main__":
    tasks = []
    ray.init(num_cpus = 25, _system_config={
        "object_spilling_config": json.dumps(
            {"type": "filesystem", "params": {"directory_path": "/dfs/user/013150/tmp"}},
        )})

    remote_func = ray.remote(main)
    symbols = ["688032.SH", "688041.SH", "688256.SH", "688012.SH", "688981.SH", "688111.SH", "688271.SH"]
    dates = ['20231201', '20231204', '20231205', '20231206', '20231207', '20231208', '20231211', '20231212', '20231213', '20231214', '20231215', '20231218', '20231219', '20231220', '20231221', '20231222', '20231225', '20231226', '20231227', '20231228', '20231229', '20240102', '20240103', '20240104', '20240105', '20240108', '20240109', '20240110', '20240111', '20240112', '20240115', '20240116', '20240117', '20240118', '20240119', '20240122', '20240123', '20240124', '20240125', '20240126', '20240129', '20240130', '20240131', '20240201', '20240202', '20240205', '20240206', '20240207', '20240208', '20240219', '20240220', '20240221', '20240222', '20240223', '20240226', '20240227', '20240228', '20240229']

    print(dates)
    # print(symbols, dates)

    for fidx, factor_list in [
        # (0, ["ActivePriceVolume"]),
        # (1, ["BreakingP0NumOrders", "CumOrdersNetVolOverV0"]),
        # (2, ["PriceSpread"]),
        # (3, ["OneBigOrder"])
        (4, ["FacActivePVBuy", "FacActivePVSell"])

    ]:

        for symbol in symbols:
            tasks = []
            for date in dates:
                tasks.append(remote_func.remote(symbol, date, factor_list = factor_list))

            result_list = ray.get(tasks)
            result_df = pd.concat(result_list)
            param_basedir = "/dfs/group/800657/library/l3_event/event_params"

            sub_df = result_df[result_df["symbol"]==symbol]
            sub_df = sub_df.sort_values(by="date")
            sub_df.to_parquet(os.path.join(param_basedir, "{}_{}.parquet".format(symbol, fidx)))
