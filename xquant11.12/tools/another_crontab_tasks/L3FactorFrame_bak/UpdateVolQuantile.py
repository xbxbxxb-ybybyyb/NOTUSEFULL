import json
import os
import pickle
import numpy as np
import pandas as pd
from xquant.factordata import FactorData
from MarketDataManager import get_l3_trade_order_date
import traceback
from tqdm import tqdm
import ray
import time
import sys
from datetime import datetime


def get_day_stock_list(date = "20240130"):
    fa = FactorData()
    symbols = fa.hset("INDEX", date, "000688.SH")["stock"].tolist()
    return symbols

def get_valid_trading_days(symbol, start_date, end_date, lookback_days = 5):
    fa = FactorData()
    stat_days = fa.tradingday("20191202", end_date)
    updw_limit = 0.195 if symbol.startswith("68") else 0.095
    try:
        trade_status = fa.get_factor_value("Basic_factor", stock=[symbol], mddate=stat_days,
                                                  factor_names=["trade_status", "volume", "pre_close", "high", "low"])
        trade_status = trade_status.droplevel(1)
        trade_status["hvpc"] = (trade_status["high"] / trade_status["pre_close"] - 1).abs()
        trade_status["lvpc"] = (trade_status["low"] / trade_status["pre_close"] - 1).abs()
        trade_status["TradeFlag"] = ((~trade_status["trade_status"].isnull())
                                     & (trade_status["trade_status"] != "待核查")
                                     & (trade_status["trade_status"] != "停牌")
                                     & (trade_status["volume"] != 0)
                                     & (trade_status["hvpc"] < updw_limit)
                                     & (trade_status["lvpc"] < updw_limit))
        trade_status = trade_status[trade_status["TradeFlag"] == True]
        ## 忽略20221206行情
        chosen_stat_days = sorted(trade_status.index.tolist())
        for idx,i in enumerate(chosen_stat_days):
            if i >= start_date:
                break
        chosen_stat_days = chosen_stat_days[max(idx-lookback_days, 0):]
    except Exception as e:
        print(f"Cannot find any valid stat trading days for {symbol} before {end_date}!\n")
        chosen_stat_days = []
    return chosen_stat_days

def get_daily_vol_df(symbol, date, use_pandas = False):
    try:
        local_vol_df, _, _, _ = get_l3_trade_order_date(symbol, date, use_pandas = use_pandas)
        local_vol_df = local_vol_df.to_pandas()
        local_vol_df.index = range(len(local_vol_df))
        local_vol_df = local_vol_df[local_vol_df["LevelOneChange"] != False]
        local_vol_df = local_vol_df[["AskV0", "BidV0"]]
        local_vol_df = local_vol_df.replace([-np.inf, np.inf], np.nan)
        local_vol_df = local_vol_df.dropna()
    except Exception as e:
        print("get_daily_vol_df ERROR:", traceback.print_exc())
        # raise Exception()
        local_vol_df = pd.DataFrame(columns = ["AskV0", "BidV0"])
    return local_vol_df

def get_daily_vol_quantile(l3_df_list, quantile = [50]):
    if len(l3_df_list) == 0:
        l3_df = pd.DataFrame()
    else:
        l3_df = pd.concat(l3_df_list, axis=0)
    vol_quantile_dict = dict()
    if l3_df.empty:
        return None
    else:
        for q in quantile:
            ask_v0_q = np.floor(l3_df["AskV0"].quantile(q / 100))
            bid_v0_q = np.floor(l3_df["BidV0"].quantile(q / 100))
            vol_quantile_dict.update({f"PM_TAV0Q{q}": ask_v0_q, f"PM_TBV0Q{q}": bid_v0_q})
    return vol_quantile_dict

def calc_daily_vol_quantlile(symbol, start_date, end_date, quantile = [50, 70], lookback_days=5, quantlie_save_path = None):
    fa = FactorData()
    # 注意：end_date开始查询前一天的数据
    valid_trading_days = get_valid_trading_days(symbol, start_date=start_date, end_date=end_date,
                                                lookback_days=lookback_days)
    dates = fa.tradingday(start_date, end_date)
    next_date = fa.tradingday(end_date, 5)[1]#获取未来的一天
    l3_df_list = []
    param_list = []

    # for tidx, trading_day in tqdm(enumerate(dates)):
    for tidx, trading_day in enumerate(dates):
        if tidx == 0:
            for d in valid_trading_days[:5]:
                l3_df_list.append(get_daily_vol_df(symbol, d))
        new_row = [trading_day]
        for qt in quantile:
            daily_vol_quantile_dict = get_daily_vol_quantile(l3_df_list, quantile = [qt])
            if daily_vol_quantile_dict is not None:
                new_row = new_row + [daily_vol_quantile_dict[key] for key in daily_vol_quantile_dict.keys()]
        param_list.append(new_row)
        if trading_day in valid_trading_days:
            l3_df = get_daily_vol_df(symbol, trading_day)
            l3_df_list.pop(0)
            l3_df_list.append(l3_df)
    columns = ["Date"]
    for qt in quantile:
        columns+=["AskV0Q"+str(qt), "BidV0Q"+str(qt)]
    param_df = pd.DataFrame(param_list, columns = columns)
    #################注意：前一天的成交分位数，用于后一天的实盘参数###################
    param_df["Date"] = param_df["Date"].shift(-1)
    param_df.iloc[-1,0]=next_date
    param_df = param_df.sort_values(by = ["Date"])
    print(param_df)
    ####################################
    if not os.path.exists(quantlie_save_path):
        print("save quantlie success! Path ", quantlie_save_path)
        param_df.to_parquet(quantlie_save_path)
    else:
        old_param_df = pd.read_parquet(quantlie_save_path)
        param_df = pd.concat([old_param_df, param_df]).drop_duplicates(subset=['Date'],keep='last').sort_values("Date")
        param_df.to_parquet(quantlie_save_path)
    print(param_df)
    return param_df

def prepare_event_params(symbol, date, event_quantile_df):
    ##################
    trigger_spread_ratio = 1# 表示千分之一
    Q1 = 50
    Q2 = 70
    interval = 0.055
    N_num = 5
    ##################
    event_quantile_df = event_quantile_df[event_quantile_df["Date"] == date].sort_values("Date")
    if event_quantile_df.empty:
        raise Exception("{} 分位数据为空！".format(symbol))
    askv0_quantile1 = event_quantile_df[f"AskV0Q{Q1}"].tolist()[-1]
    bidv0_quantile1 = event_quantile_df[f"BidV0Q{Q1}"].tolist()[-1]
    askv0_quantile2 = event_quantile_df[f"AskV0Q{Q1}"].tolist()[-1]
    bidv0_quantile2 = event_quantile_df[f"BidV0Q{Q1}"].tolist()[-1]
    code_event_params_dict = dict()
    code_event_params_dict["FacActivePVSell"] = {"interval":10.0, "gap": 0.0012, "active_volume": 400.0}
    code_event_params_dict["FacActivePVBuy"] = {"interval":10.0, "gap": 0.0012, "active_volume": 400.0}
    code_event_params_dict["PriceGapTaken"] = {"gap": trigger_spread_ratio}
    code_event_params_dict["OneBigOrder"] = {"askvq": askv0_quantile2, "bidvq": bidv0_quantile2}
    code_event_params_dict["CumOrdersNetVolOverV0"] = {"interval": interval, "askvq": askv0_quantile1,
                                                   "bidvq": bidv0_quantile1}
    code_event_params_dict["BreakingP0NumOrders"] = {"interval": interval, "num": N_num}
    return code_event_params_dict

@ray.remote(max_calls=5)
def UpdateVolQuantile(code, dates, lookback_days = 5):
    try:
        save_dir = "/dfs/group/800657/library/l3_event/event_params"
        start_date, end_date = sorted(dates)[0], sorted(dates)[-1]
        event_save_path = os.path.join(save_dir, f"{code}.parquet")
        event_quantile_df = calc_daily_vol_quantlile(code, start_date, end_date, quantlie_save_path=event_save_path, lookback_days=lookback_days)
        fa = FactorData()
        next_date = fa.tradingday(end_date, 5)[1]  # 获取未来的一天
        code_event_params_dict = prepare_event_params(code, next_date, event_quantile_df)
        print("finish! ", code)
    except:
        print(traceback.print_exc())
        code_event_params_dict = {}
    return code, code_event_params_dict


if __name__=="__main__":
    # date = "20240102"
    # code_list = get_day_stock_list(date)
    lookback_days = 5
    fa = FactorData()
    # symbols_all = fa.hset("INDEX", "20240228", "000688.SH")["stock"].tolist()
    # code_list = symbols_all
    # code_list = pd.read_csv("zz500.csv", header=None)[0].tolist()
    code_list = pd.read_csv("kc_amt_swing.csv", header=None)[0].tolist()
    code_list1 = pd.read_csv("zz500_sample_old.csv", header=None)[0].tolist()
    code_list = code_list+code_list1
    # dates = fa.tradingday("20220101", "20240331")
    # code_list = ["688032.SH", "688041.SH", "688256.SH", "688012.SH", "688981.SH", "688111.SH", "688271.SH"]
    # code_list = sorted(set(symbols_all)-set(code_list))
    # start_date, end_date = "20200101", "20240229"
    now_date = "20240703"#datetime.now().strftime("%Y%m%d")
    dates = fa.tradingday(now_date, now_date)#fa.tradingday("20240516", "20240516")
    try:
        dates = [sys.argv[1]]
    except:
        dates = [date for date in dates if now_date>=date]

    t1 = time.time()
    ray.init(num_cpus=20, local_mode=False)
    remote_func = UpdateVolQuantile
    event_params_dict = dict()
    tasks = [remote_func.remote(code, dates, lookback_days = lookback_days) for code in code_list]
    results = ray.get(tasks)
    for result in results:
        event_params_dict[result[0]] = result[1]
    json.dump(event_params_dict, open("/dfs/user/013150/tmp/event/online/eventParams.json", "w"))
    os.system("curl ftp://168.8.2.68/XQuant/013150/xquant_online/Update/ -T /dfs/user/013150/tmp/event/online/eventParams.json -u 'xquant:Xquant-32'")
    print("event_params_dict:", event_params_dict)
    print("耗时：", time.time()-t1)

