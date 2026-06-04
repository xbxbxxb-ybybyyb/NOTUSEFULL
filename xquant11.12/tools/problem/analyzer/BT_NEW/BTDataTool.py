#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/3/9 13:07

import os
import pickle
import json
import shutil
import pandas as pd
from Logger.Logger import Logger
from xquant.xqutils.xqfile import HDFSFile
from xquant.xqutils.helper import multicore_init
from multiprocessing import Pool


def combine_trade_and_capacity(target_code, volume, start_date, end_date, portfolio, high_vol_dict, process_num=20):
    combine_path = '{}{}-{}-{}'.format("/data/user/015629/BT_Trade_OrderCapacity/Stock/", start_date, end_date, portfolio)
    if os.path.exists(combine_path):
        shutil.rmtree(combine_path)
        
    if not os.path.exists(combine_path):
        os.makedirs(combine_path)

    quantity = {}
    para_split = []

    for ii in range(process_num):
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
            (target_code, volume, para_split[ii], start_date, end_date, combine_path, high_vol_dict, portfolio, )
        )
        multiProcessResult.append(result)
    pool.close()
    pool.join()

    for result in multiProcessResult:
        quantity.update(result.get())

    with open(combine_path + '/' + portfolio + '_quantity.json', "w") as f:
        json.dump({"Portfolio": portfolio, "Quantity": quantity}, f)

def get_bt_data(target_code, volume, para_split, start_date, end_date, combine_path, high_vol_dict, portfolio):
    """"""
    if portfolio == "EasyTrack":
        live_params_file = "/data/user/015629/EasyInferSignal/portfolioInfo/parameters/easy_live_params_{}.csv".format(end_date)
        live_params = pd.read_csv(live_params_file).dropna(how='any', axis=0)
        live_order_capacity = live_params.set_index("symbol")["perOrderAmountLimit"].to_dict()

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
            print("OrderCapacity file {} not found.".format(order_capacity_file))
            continue
        with open(order_capacity_file, "rb") as f:
            capacity = json.load(f)

        dates = []
        for date in capacity["OrderCapacity"]:
            if start_date <= date <= end_date and date != '20190112' and date != '20190405' and date != "20200131":
                dates.append(date)
        if len(dates) == 0:
            print("No trade dates for {}.".format(symbol))
            continue

        dates.sort()

        tickData = []
        transactionData = []
        for date in dates:
            order_capacity["OrderCapacity"][date] = capacity["OrderCapacity"][date] * 0.3
            if portfolio == "EasyTrack":
                order_capacity["OrderCapacity"][date] = live_order_capacity.get(symbol)
            order_capacity["HighVol"][date] = high_vol_dict[symbol].get(date, 0.)
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

def copy_signals_to_share(upload_date, symbols, src_path, dst_path, end_date, is_big):
    log_file_path = "{}{}/".format("/data/user/015629/Logging/bt/" ,str(end_date))
    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)

    if is_big:
        file_name = "debug_big.txt"
    else:
        file_name = "debug.txt"
    log_debug_file = log_file_path + file_name
    log_fd = Logger(log_debug_file, level='debug')
    log_fd.logger.debug("Start to copy signal...")

    hf = HDFSFile()
    i = 0
    for symbol in symbols:
        for date in upload_date:
            source_file_dir = src_path + "/" + symbol + "/" + date + "/"
            dst_file_dir = dst_path + "/" + symbol + "/"
            print(source_file_dir, dst_file_dir)
            try:
                hf.copyToShare(dst_file_dir, source_file_dir + '/')
            except:
                print("error copy {}, successfully copy {} stocks".format(symbol, i))
                log_fd.logger.debug("error copy {}".format(symbol))
                continue
            log_fd.logger.debug("successfully copied {} symbols".format(i))
            i = i + 1
            print("Copied {} stocks".format(i))


