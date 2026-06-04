import pandas as pd
from xquant.xqutils.xqfile import HDFSFile
import os 
from Logger.Logger import Logger
     
log_file =         "/app/data/666888/FactorSummary//test_bu/315-324.txt"
# if not os.path.exists("/app/data/666888/Logging/delete_trade/"):
    # os.makedirs("/app/data/666888/Logging/delete_trade/")
log_fd = Logger(log_file, level='info')



data = pd.read_csv("/app/data/666888/FactorSummary/test_bu/2019test_.csv", header=0, index_col=0)
print(data.shape)
cnt_stocks, cnt_dates = data.shape[0], data.shape[1]
stocks = list(data.index)
dates = list(data.columns)


# Task1: 统计因子个数不相等以及数据文件破坏的情况
if True:
    for stock_index in range(cnt_stocks):
        for date_index in range(cnt_dates):
            if data.iloc[stock_index, date_index] == -1:
                print(stocks[stock_index], dates[date_index])
                log_fd.logger.info("Find Abnormal stock {} on date {}".format(stocks[stock_index], dates[date_index]))


# Task2: 统计每天正常股票数
if True:
    for date_index in range(cnt_dates):
        valid_stock_number = 0
        for stock_index in range(cnt_stocks):
            if data.iloc[stock_index, date_index] > 0:
                valid_stock_number = valid_stock_number + 1
        log_fd.logger.info("valid_stock_number of date {} is {}/{} ".format(dates[date_index], valid_stock_number, len(stocks)))
        
# Task3: 统计丢失的交易日

if True:    
    import System.GetTradingDay as get_trading_day
    trading_day = get_trading_day.getTradingDay(int(dates[0]), int(dates[-1]))
    for day in trading_day:
        if str(day) not in dates:
            print("We lost trading day {} in our AppleData".format(day))
            log_fd.logger.info("We lost trading day {} in our AppleData".format(day))
        
        
        