import os
import pickle
import json
import pandas as pd
from multiprocessing import Pool
from System.TradingDay import getTradingDay
from xquant.pyfile import Pyfile

order_capacity_path = "/data/user/666888/CBOrderCapacity2/"
trade_path = "/data/user/666888/TradeDataCB3/"
root_path = "/data/user/666888/BT_Trade_OrderCapacity2/"


def get_bt_data(target_code, volume, para_split, combine_path, start_date, end_date):
    quantity = {}
    for index in para_split:
        c = target_code[index]
        order_capacity = {"OrderCapacity": {}}
        __fpath = order_capacity_path + "/" + c + '/OrderCapacity.json'

        # if not os.path.exists(__fpath):
            # print("order capacity not found", c)
            # print(__fpath)
            # continue

        # with open(order_capacity_path + "/" + c + '/OrderCapacity.json', "r") as f:
            # capacity = json.load(f)
        capacity = {"code": c, "OrderCapacity": {str(x): 10000000 for x in getTradingDay(int(start_date), int(end_date))}}

        code = capacity["code"]
        order_capacity["code"] = code

        if 300000 <= int(code[0: 6]) <= 399999:
            order_capacity["Holo"] = "true"
        else:
            order_capacity["Holo"] = "false"

        dates = []
        for d in capacity["OrderCapacity"]:
            if start_date <= d <= end_date and d != '20190112' and d != '20190405':
                dates.append(d)

        if len(dates) == 0:
            print("no trade dates", c)
            continue

        dates.sort()
        for d in dates:
            order_capacity["OrderCapacity"][d] = capacity["OrderCapacity"][d]
        tickData = []
        transactionData = []
        for d in dates:
            if not os.path.exists(trade_path + "/" + c + "/" + d + "/Data.pickle"):
                print(c, d, "not found")
                continue
            with open(trade_path + "/" + c + "/" + d + "/Data.pickle", 'rb') as f:
                data = pickle.load(f)
            tickData.append(data[0])
            transactionData.append(data[1])
        out_path = combine_path + '/' + c + "/"
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        with open(out_path + "/Data.pickle", 'wb') as f:
            pickle.dump((tickData, transactionData), f)

        with open(out_path + '/OrderCapacity.json', "w") as f:
            json.dump(order_capacity, f)

        with open(out_path + '/Dates.json', "w") as f:
            json.dump({"Dates": dates}, f)

        quantity[c] = volume[index]
    return quantity


def combine(target_code, volume, start_date, end_date, curr_date, combine_name):
    bt_date_path = root_path + "/" + start_date + "-" + end_date + '_' + curr_date + "/"
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

    for kk in multiProcessResult:
        quantity.update(kk.get())
    with open(combine_path + '/' + combine_name + '_quantity.json', "w") as f:
        json.dump({"Combine": combine_name, "quantity": quantity}, f)


def combine_trade_and_capacity(portfolio, start_date, end_date, next_trading_day):
    df = pd.read_excel("/data/user/666888/WuKong/portfolios/{}_{}.xlsx".format(portfolio, next_trading_day))
    print("Combining {}'s trade and capacity".format(portfolio))
    codes = df.iloc[:, 0].tolist()
    print("{} stocks in total".format(len(codes)))
    volumes = [int(quantity) for quantity in df.iloc[:, 3]]
    combine(codes, volumes, start_date, end_date, next_trading_day, portfolio)


def main():
    portfolios = "WuKong"
    today = "20200730"
    start_date = today
    end_date = today
    next_trading_day = today

    start_date = "20200901"
    end_date = "20200930"
    next_trading_day = "20200831"

    combine_trade_and_capacity(portfolios, start_date, end_date, next_trading_day)

    py = Pyfile()
    src_path = "{}/{}-{}_{}/{}/".format(root_path, start_date, end_date, next_trading_day, portfolios)
    dst_path = "WuKong/bt_info/{}-{}/{}/".format(start_date, end_date, portfolios)
    py.upload(dst_path, src_path)


if __name__ == "__main__":
    main()
