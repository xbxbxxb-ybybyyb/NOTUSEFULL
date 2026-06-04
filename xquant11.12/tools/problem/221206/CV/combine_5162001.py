import os
import pickle
import json
import shutil
import pandas as pd
from multiprocessing import Pool
from DataAPI.GetTradingDay import trading_day
from xquant.pyfile import Pyfile

trade_path = "/data/user/666888/TradeData2/"
root_path = "/data/user/666888/BT_Trade_OrderCapacity2/"


def get_cv_data(target_code, volume, para_split, combine_path, start_date, end_date):
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


def combine(target_code, volume, start_date, end_date, next_trading_day, combine_name):
    combine_path = "{}/{}-{}_{}/{}/".format(root_path, start_date, end_date, next_trading_day, combine_name)
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
            get_cv_data,
            (target_code, volume, para_split[ii], combine_path, start_date, end_date)
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


def combine_trade_and_capacity(portfolio, start_date, end_date, next_trading_day):
    shutil.copyfile(
        "/data/user/006688/ApolloProduction/AdjustFiles/{}/Apollo_{}_{}.xlsx".format(next_trading_day, portfolio, next_trading_day),
        "/data/user/666888/Apollo/portfolios/{}/night/Apollo_{}_{}.xlsx".format(next_trading_day, portfolio, next_trading_day)
    )
    df = pd.read_excel("/data/user/666888/Apollo/portfolios/{}/night/Apollo_{}_{}.xlsx"
                       .format(next_trading_day, portfolio, next_trading_day))
    print("Combining {}'s trade and capacity".format(portfolio))
    codes = df.iloc[:, 0].tolist()
    print("{} stocks in total".format(len(codes)))
    volumes = [int(quantity) for quantity in df.iloc[:, 3] - df.iloc[:, 4]]
    combine(codes, volumes, start_date, end_date, next_trading_day, portfolio)


def main():
    portfolios = "5162001"
    start_date = "20191007"
    end_date = "20191220"
    next_trading_day = "20191223"

    combine_trade_and_capacity(portfolios, start_date, end_date, next_trading_day)

    py = Pyfile()
    src_path = "{}/{}-{}_{}/{}/".format(root_path, start_date, end_date, next_trading_day, portfolios)
    dst_path = "Apollo/cv_info/{}-{}_{}/{}/".format(start_date, end_date, next_trading_day, portfolios)
    py.upload(dst_path, src_path)


if __name__ == "__main__":
    main()
