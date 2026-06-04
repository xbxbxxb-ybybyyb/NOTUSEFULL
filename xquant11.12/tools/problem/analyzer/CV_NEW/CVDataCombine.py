import os
import pickle
import json
import shutil
import datetime as dt
import pandas as pd
from multiprocessing import Pool
from xquant.xqutils.helper import multicore_init
from xquant.xqutils.xqfile import HDFSFile
from xquant.factordata import FactorData
from CV_NEW.GetHighVol import get_high_vol_speed
from CV_NEW.GetOptShift import get_optimal_shift_speed
from ScheduledTask.DailyLiveStockList import DailyLiveStockList

def get_index_weights(index="HS300", date="20201231", size=5*10**8):
    fa = FactorData()
    stock_weight = fa.hset("INDEX", date, index)
    stock_weight = stock_weight[["stock", "weight"]]  ## note the sum of weights equals 100
    stock_list = stock_weight["stock"].tolist()

    close = fa.get_factor_value("Basic_factor", stock_list, [date], ["close"]).droplevel(0)
    close.index.name = None
    close["stock"] = close.index.tolist()

    weights = pd.merge(stock_weight, close, on="stock")
    weights["weight"] = weights["weight"] / weights["close"] / 100 * size
    weights = weights[["stock", "weight"]]

    return weights

def get_kcb_code(base_date, n=60):
    """获取科创板股票样本，选择原则：必须在base_date前n日以前上市"""
    if not isinstance(base_date, str):
        base_date = str(base_date)
    fa = FactorData()
    market_stock_list = fa.hset("MARKET", "20210127", "ALLA_HIS")['stock'].to_list()
    kcb_stock_list = list(filter(lambda x: x.startswith('68'), market_stock_list))
    factor_df = fa.get_factor_value("Basic_factor", kcb_stock_list, [base_date], ['listing_date'])['listing_date']
    key_date = fa.tradingday(base_date, -(n+1))[0]
    kcb_code = list(factor_df[factor_df <= int(key_date)].index)
    return kcb_code

def combine_trade_and_capacity(market_lib, signal_lib, portfolio, start_date, end_date, next_trading_day, process_num=20, is_copy_to_share=True):
    if portfolio in ["hs300", "zz500"]:
        local_path = "/data/user/666888/AlgoGenzong2/portfolios/"
        file_name = "{}.xlsx".format(portfolio)
        df = pd.read_excel(local_path + file_name)
        codes = list([code for code in df.iloc[:, 0]])
        volumes = list([volume for volume in df.iloc[:, 1]])

    elif portfolio in ["hs300_Track", "zz500_Track"]:
        base_date = "20201231"
        size = 5 * 10**8
        index = portfolio.split("_")[0].upper()
        weights = get_index_weights(index, base_date, size)
        codes = weights["stock"].tolist()
        volumes = [int(x) for x in weights["weight"].tolist()]

    elif portfolio == "easy":
        dls = DailyLiveStockList(next_trading_day, 0.2, small_model=False)
        live_stock_list, net_add_stock_list = dls.get_live_stock_list()
        if len(net_add_stock_list) == 0:
            return
        file_name = "{}_{}.xlsx".format(next_trading_day, portfolio)
        local_path = "/data/user/015629/EasyInferSignal/portfolioInfo/portfolios/"
        df = pd.read_excel(local_path + file_name)
        add_df = df[df["证券代码"].isin(net_add_stock_list)]
        codes = add_df["证券代码"].tolist()
        volumes = add_df["证券额度"].tolist()

    ### 上传 Trade & Capacity 和 活跃度参数到 HDFS
    print("Combining {}'s Trade and Capacity: {} Stocks ".format(portfolio, len(codes)))
    run_combine_trade_and_capacity(market_lib, codes, volumes, start_date, end_date, portfolio, process_num)

    hf = HDFSFile()
    combine_path = '{}{}-{}_{}-{}-{}'.format("cv/Stock/ds-", start_date, end_date, next_trading_day, portfolio, signal_lib)
    if is_copy_to_share:
        print(dt.datetime.now(), "Uploading {}'s Trade and Capacity to HDFS...".format(portfolio))
        hf.upload( combine_path,
                   '{}{}-{}-{}'.format("/data/user/015629/BT_Trade_OrderCapacity/Stock/", start_date, end_date, portfolio)
        )

    ### 生成信号阈值最优偏移量指标
    print(" Generating Optimal Shift Data ... ")
    opt_shift_dict = get_optimal_shift_speed(signal_lib, codes, start_date, end_date, lookback=20, process_num=process_num)
    with hf.open(combine_path + '/' + portfolio + '_optshift.json', "wb") as f:
        json.dump({"Portfolio": portfolio, "OptShift": opt_shift_dict}, f)

def run_combine_trade_and_capacity(market_lib, target_code, volume, start_date, end_date, portfolio, process_num):
    ###  生成股票活跃度指标, 其中参数可以根据需要设置start_date, end_date, lookback
    print(" Generating High Vol Data ... ")
    high_vol_dict = get_high_vol_speed(market_lib, target_code, start_date, end_date, lookback=20, process_num=process_num)

    combine_path = '{}{}-{}-{}'.format("/data/user/015629/BT_Trade_OrderCapacity/Stock/", start_date, end_date, portfolio)
    if os.path.exists(combine_path):
        shutil.rmtree(combine_path)
    if not os.path.exists(combine_path):
        os.makedirs(combine_path)

    quantity = {}
    para_split = []
    for index in range(process_num):
        para_split.append([])

    count = 0
    for ii in range(len(target_code)):
        para_split[count].append(ii)
        count = count + 1
        if count >= process_num:
            count = 0

    assert multicore_init() == True
    pool = Pool(processes=process_num)

    multiProcessResult = []
    for ii in range(para_split.__len__()):
        result = pool.apply_async(
            get_bt_data,
            (target_code, volume, para_split[ii], combine_path, start_date, end_date, high_vol_dict, )
        )
        multiProcessResult.append(result)
    pool.close()
    pool.join()

    for ii in multiProcessResult:
        quantity.update(ii.get())

    with open(combine_path + '/' + portfolio + '_quantity.json', "w") as f:
        json.dump({"Portfolio": portfolio, "Quantity": quantity}, f)


def get_bt_data(target_code, volume, para_split, combine_path, start_date, end_date, high_vol_dict):

    quantity = {}
    for ii in para_split:
        symbol = target_code[ii]
        order_capacity = dict()
        order_capacity["OrderCapacity"] = {}
        order_capacity["HighVol"] = {}
        order_capacity["Code"] = symbol
        if 300000 <= int(symbol[0:6]) <= 399999: ### 是否为创业板股票
            order_capacity["Holo"] = "true"
        else:
            order_capacity["Holo"] = "false"

        order_capacity_file = "/data/user/666888/OrderCapacity/" + symbol + '/OrderCapacity.json'

        if not os.path.exists(order_capacity_file):
            print("Order Capacity NOT Found: {}".format(order_capacity_file))
            continue
        with open(order_capacity_file, "rb") as f:
            capacity = json.load(f)

        dates = []
        for date in capacity["OrderCapacity"]:
            if start_date <= date <= end_date and date != '20190112' and date != '20190405' and date != "20200131":
                dates.append(date)

        if len(dates) == 0:
            print("no trade dates", symbol)
            continue

        dates.sort()

        tickData = []
        transactionData = []
        for date in dates:
            order_capacity["OrderCapacity"][date] = capacity["OrderCapacity"][date] * 0.3
            order_capacity["HighVol"][date] = high_vol_dict[symbol].get(date, 0)
            if not os.path.exists("/data/user/666888/TradeData2/" + symbol + "/" + date + "/Data.pickle"):
                print("Data.pickle not found for {} on {}.".format(symbol, date))
                continue
            with open("/data/user/666888/TradeData2/" + symbol + "/" + date + "/Data.pickle", 'rb') as f:
                data = pickle.load(f)
            tickData.append(data[0])
            transactionData.append(data[1])

        out_path = combine_path + '/' + symbol + "/"
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        with open(out_path + "/Data.pickle", 'wb') as f:
            pickle.dump((tickData, transactionData), f)
        with open(out_path + '/OrderCapacity.json', "w") as f:
            json.dump(order_capacity, f)
        with open(out_path + '/Dates.json', "w") as f:
            json.dump({"Dates": dates}, f)

        quantity[symbol] = volume[ii]
    return quantity


def main():
    market_lib = "ZeusDataLib"
    signal_lib = "Everest20210201_20210515" 
    start_date = "20210719"
    end_date = "20210917"
    next_trading_day = "20210924"
    portfolios = ["easy"]
    for portfolio in portfolios:
        combine_trade_and_capacity(market_lib, signal_lib, portfolio, start_date, end_date, next_trading_day, process_num=20, is_copy_to_share=True)


if __name__ == '__main__':
    main()