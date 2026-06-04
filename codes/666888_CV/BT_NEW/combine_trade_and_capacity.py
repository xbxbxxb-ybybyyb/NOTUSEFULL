import os
import pickle
import json
from multiprocessing import Pool


order_capacity_path = "/data/user/666888/OrderCapacity2/"
trade_path = "/data/user/666888/TradeData2/"
root_path = "/data/user/666888/BT_Trade_OrderCapacity/"


def get_bt_data(target_code, volume, para_split, combine_path, start_date, end_date):
    quantity = {}
    for index in para_split:
        symbol = target_code[index]

        order_capacity = dict()
        order_capacity["OrderCapacity"] = {}
        order_capacity["code"] = symbol
        if 300000 <= int(symbol[0: 6]) <= 399999:
            order_capacity["Holo"] = "true"
        else:
            order_capacity["Holo"] = "false"

        order_capacity_file = order_capacity_path + symbol + '/OrderCapacity.json'
        if not os.path.exists(order_capacity_file):
            print("OrderCapacity file {} not found.".format(order_capacity_file))
            continue

        with open(order_capacity_file, "r") as f:
            capacity = json.load(f)

        dates = []
        for date in capacity["OrderCapacity"]:
            if start_date <= date <= end_date:
                dates.append(date)
        if len(dates) == 0:
            print("No trade dates for {}.".format(symbol))
            continue
        dates.sort()

        tickData = []
        transactionData = []

        for date in dates:
            order_capacity["OrderCapacity"][date] = capacity["OrderCapacity"][date]

            if not os.path.exists(trade_path + "/" + symbol + "/" + date + "/Data.pickle"):
                print("Data.pickle not found for {} on {}.".format(symbol, date))
                continue
            with open(trade_path + "/" + symbol + "/" + date + "/Data.pickle", 'rb') as f:
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

        quantity[symbol] = volume[index]
    return quantity


def combine(target_code, volume, start_date, end_date, combine_name):
    bt_date_path = root_path + "/" + start_date + "-" + end_date + "/"
    combine_path = bt_date_path + "/" + combine_name
    if not os.path.exists(combine_path):
        os.makedirs(combine_path)

    quantity = {}
    processNum = 6
    para_split = []

    for index in range(processNum):
        para_split.append([])

    count = 0
    for index in range(len(target_code)):
        para_split[count].append(index)
        count = count + 1
        if count >= processNum:
            count = 0

    pool = Pool(processes=processNum)
    multiProcessResult = []
    for ii in range(para_split.__len__()):
        result = pool.apply_async(
            get_bt_data,
            (target_code, volume, para_split[ii], combine_path, start_date, end_date)
        )
        multiProcessResult.append(result)
    pool.close()
    pool.join()
    for result in multiProcessResult:
        quantity.update(result.get())
    with open(combine_path + '/' + combine_name + '_quantity.json', "w") as f:
        json.dump({"Combine": combine_name, "quantity": quantity}, f)
