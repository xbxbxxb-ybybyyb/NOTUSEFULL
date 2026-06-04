import os
import pickle
import json
import pandas as pd
from multiprocessing import Pool
from DataAPI.GetTradingDay import trading_day
from xquant.pyfile import Pyfile

trade_path = "/data/user/666888/TradeData2/"
root_path = "/data/user/666888/BT_Trade_OrderCapacity2/"


def get_bt_data(target_code, volume, para_split, combine_path, start_date, end_date):
    quantity = {}
    value = {}
    for index in para_split:
        symbol = target_code[index]

        dates = list(map(str, trading_day(int(start_date), int(end_date))))
        if len(dates) == 0:
            print("No trade dates for {}".format(symbol))
            continue

        tickData = []
        transactionData = []

        for date in dates:
            if not os.path.exists(trade_path + "/" + symbol + "/" + date + "/Data.pickle"):
                print("Data.pickle for {} not found on {}".format(symbol, date))
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

        with open(out_path + '/Dates.json', "w") as f:
            json.dump({"Dates": dates}, f)

        quantity[symbol] = volume[index]
        value[symbol] = quantity[symbol] * 0

    return quantity, value


def combine(target_code, volume, today, combine_name):
    bt_date_path = root_path + "/" + today + "/"
    combine_path = bt_date_path + "/" + combine_name + "/"
    if not os.path.exists(combine_path):
        os.makedirs(combine_path)

    quantity = {}
    value = {}
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
            (target_code, volume, para_split[ii], combine_path, today, today)
        )
        multiProcessResult.append(result)
    pool.close()
    pool.join()

    for result in multiProcessResult:
        quantity.update(result.get()[0])
    for result in multiProcessResult:
        value.update(result.get()[1])

    with open(combine_path + '/' + combine_name + '_quantity.json', "w") as f:
        json.dump({"Combine": combine_name, "quantity": quantity, "value": value}, f)


def combine_trade_and_capacity(portfolio, today):
    df = pd.read_excel("/data/user/666888/Apollo/portfolios/{}/morning/Apollo_{}_{}.xlsx"
                       .format(today, portfolio, today))
    print("Combining {}'s trade and capacity".format(portfolio))
    codes = df.iloc[:, 0].tolist()
    print("{} stocks in total".format(len(codes)))
    volumes = [int(quantity) for quantity in df.iloc[:, 3] - df.iloc[:, 4]]
    combine(codes, volumes, today, portfolio)


def main(today):
    portfolios = ["5162001", "5161101"]

    for portfolio in portfolios:
        combine_trade_and_capacity(portfolio, today)

        py = Pyfile()
        src_path = "{}/{}/{}/".format(root_path, today, portfolio)
        dst_path = "Apollo/bt_info/{}/{}/".format(today, portfolio)
        print("Uploading {}'s bt info...".format(portfolio))
        py.upload(dst_path, src_path)
    print("Done")


if __name__ == "__main__":
    today = "20191209"
    main(today)
