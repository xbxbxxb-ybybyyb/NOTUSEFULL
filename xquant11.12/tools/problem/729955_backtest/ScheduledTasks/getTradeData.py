import os
import sys

sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
import gc
import pickle
import datetime as dt
from System.TradingDay import getTradingDay
from System.getCBSet import cbond_set
from System.getCBData import getCBTickData, getCBTransactionData
from System.Logger import Logger

OUTPUT_PATH = "/data/user/666888/TradeDataCB3/"
LOG_FILE_PATH = "{}/Log/".format(OUTPUT_PATH)


def getTradeData(outputPath, startDate, endDate, stockList, logFilePath):
    logFilePath = "{}/{}_{}.log".format(logFilePath, startDate, endDate)
    logger = Logger(logFilePath, level="debug")

    logger.log("Stock List: {}".format(stockList))
    stockNum = len(stockList)
    for i, stock in enumerate(stockList):
        print("Getting {}'s trade data; Stage {}/{}".format(stock, i + 1, stockNum))

        time1 = dt.datetime.now()

        logger.log("Start to get {}'s trade data from {} to {}".format(stock, startDate, endDate))
        try:
            tickDataDict = getCBTickData(stock, startDate, endDate)
            transactionDataDict = getCBTransactionData(stock, startDate, endDate)
        except Exception as e:
            logger.log("Failed to get {}'s trade data, Reason: {}".format(stock, repr(e)), level="error")
            continue

        noDataDates = []
        tradingDayList = getTradingDay(int(startDate), int(endDate))
        for date in tradingDayList:
            if date not in tickDataDict or date not in transactionDataDict:
                noDataDates.append(date)
                continue

            stockOutputPath = "{}/{}/{}/".format(outputPath, stock, date)
            if not os.path.exists(stockOutputPath):
                os.makedirs(stockOutputPath)

            with open("{}/Data.pickle".format(stockOutputPath), "wb") as f:
                pickle.dump((tickDataDict[date], transactionDataDict[date]), f)

        del tickDataDict
        del transactionDataDict

        gc.collect()

        time2 = dt.datetime.now()

        if noDataDates:
            logger.log("Dates with no trade data for {}: {}".format(stock, noDataDates))
        logger.log("Getting {}'s trade data finished; Time cost: {}s".format(stock, time2 - time1))

        print("Time cost: {}s.".format(time2 - time1))


def main():
    outputPath = OUTPUT_PATH
    logFilePath = LOG_FILE_PATH

    today = int(dt.datetime.now().strftime("%Y%m%d"))
#    today = 20200714
    startDate = today
    endDate = today
    # startDate = 20200420
    # endDate = 20200420

    # stock_list = cbond_set(endDate, "ALL")
    from xquant.bonddata import BondData
    bd = BondData()
    stock_list = bd.get_bond_set(str(endDate), "kzz")
    # stock_list = ["123047.SZ"]

    getTradeData(outputPath, startDate, endDate, stock_list, logFilePath)


if __name__ == "__main__":
    main()
