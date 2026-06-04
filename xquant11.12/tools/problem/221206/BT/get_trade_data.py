import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/.."))
import gc
import pickle
import datetime as dt
import System.GetXQuantData2 as GD
from Logger.Logger import Logger
from DataAPI.DataToolkit import get_complete_stock_list


def get_trade(outTradeDataPath, signal_dates, log_file_path="/data/user/666888/Logging/TradeData2", stock_list=None):
    if stock_list is None:
        code = os.listdir(outTradeDataPath)
        code.sort()
    else:
        code = stock_list
    log_err_file = log_file_path + "/" + "error.txt"
    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)
    log_error_fd = Logger(log_err_file, level='debug')

    stock_num = len(code)
    for i in range(stock_num):
        backTestUnderlying = code[i]
        print("Getting trade {}; Stage {}/{}".format(backTestUnderlying, i + 1, stock_num))
        stock_code = backTestUnderlying

        time1 = dt.datetime.now()
        trade_data_path = outTradeDataPath + '/' + stock_code + "/"
        if not os.path.exists(trade_data_path):
            os.makedirs(trade_data_path)

        signal_dates.sort()
        log_error_fd.logger.debug("stock_code: %s, signal_dates: %s", stock_code, signal_dates)
        startTime = dt.datetime.strptime(signal_dates[0], "%Y%m%d")
        endTime = dt.datetime.strptime(signal_dates[-1], "%Y%m%d")

        try:
            tickData = GD.getXQuantTickData2(stock_code, startTime, endTime, timeMode=3,
                                             tradingPhaseCode=["0", "1", "2", "3", "4", "5", "6", "7"])
            transactionData = GD.getXQuantTransactionData2(stock_code, startTime, endTime, True, True, timeMode=3)

        except Exception as e:
            print(repr(e))
            log_error_fd.logger.debug("train code: %s Failed", code[i], repr(e))
            continue

        if tickData[0] is None or transactionData[0] is None:
            continue

        d = tickData[0]['Date'][0]

        trans_data_path = trade_data_path + "/" + str(d)
        trans_data_name = trans_data_path + '/Data.pickle'

        if not os.path.exists(trans_data_path):
            os.makedirs(trans_data_path)
        with open(trans_data_name, 'wb') as f:
            pickle.dump((tickData[0], transactionData[0]), f)

        del tickData
        del transactionData

        time2 = dt.datetime.now()
        log_error_fd.logger.debug("total train time: %s", time2 - time1)
        print("Time cost: {}s.".format(time2 - time1))

        gc.collect()


def main():
    today = [dt.datetime.now().strftime("%Y%m%d")]
    # today = []
    outTradeDataPath = "/data/user/666888/TradeData2/"
    get_trade(outTradeDataPath, today, stock_list=get_complete_stock_list(drop_delisted_stocks=True))


if __name__ == "__main__":
    main()
