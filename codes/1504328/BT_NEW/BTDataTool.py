#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/3/9 13:07
import os
import json
import shutil
from xquant.xqutils.helper import multicore_init
from multiprocessing import Pool
from CONFIG import USER_ID


def combine_trade_and_capacity(target_code, volume, start_date, end_date, portfolio, high_vol_dict, process_num=20):
    combine_path = '{}{}-{}-{}'.format("/data/user/{}/BT_Trade_OrderCapacity/Stock/".format(USER_ID), start_date, end_date, portfolio)
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
    quantity = dict()

    for ii in para_split:
        symbol = target_code[ii]
        order_capacity = dict()
        order_capacity["OrderCapacity"] = dict()
        order_capacity["HighVol"] = dict()
        order_capacity["Code"] = symbol
        if 300000 <= int(symbol[0:6]) <= 399999: ### 是否为创业板股票
            order_capacity["Holo"] = "false"
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

        for date in dates:
            order_capacity["OrderCapacity"][date] = capacity["OrderCapacity"][date] * 0.3
            order_capacity["HighVol"][date] = high_vol_dict[symbol].get(date, 0.)

        out_path = combine_path + '/' + symbol + "/"
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        with open(out_path + '/OrderCapacity.json', "w") as f:
            json.dump(order_capacity, f)
        with open(out_path + '/Dates.json', "w") as f:
            json.dump({"Dates": dates}, f)
        quantity[symbol] = volume[ii]
    return quantity


