import datetime as dt
import pandas as pd
from SparkUtils.DataPreparationUtils.SparkLauncher import SparkLauncher
from SparkUtils.DataPreparationUtils.TaskMeta import TaskMeta
from HFDataLoader.Config import MAX_FRAME_LENGTH
import Utils.HelpFunc as Util
from STOCK_LIST import STOCK_LIST
from Constants.INDEX_LIST import INDEX_LIST, SHENWAN_INDEX_LIST, THIRD_INDEX_LIST
from Constants.CBOND_LIST import CBOND_LIST
from Constants.FUND_LIST import ETF_LIST, LOF_LIST, FUND_LIST, THIRD_ADD_STOCK_ETF_INDEX_LIST
from FactorDataTool.Config import SHENWAN_I_CODE, SHENWAN_II_CODE
from xquant.factordata import FactorData
from xquant.bonddata import BondData


def main(marketDataLibrary, codeList, startDate, endDate, daily, minute, tick, mockTick, mockFreq, overwrite, monitor,
         hbase, saveFile, savePath, env, maxExecutorNum):
    """ 日频和分钟数据起止日期一次更新，而TICK或MOCK_TICK频单个Task更新MAX_FRAME_LENGTH个交易日数据
    """

    taskList = []

    if daily or minute:
        for code in codeList:
            taskList.append(
                TaskMeta(marketDataLibrary,
                         code,
                         startDate, endDate,
                         daily, minute, False,
                         False, mockFreq,
                         overwrite,
                         monitor,
                         hbase,
                         saveFile, savePath,
                         env)
            )

    if tick or mockTick:
        if tick:
            DayUnit = MAX_FRAME_LENGTH
        elif mockTick:
            DayUnit = 1
        tradingDayList = Util.get_trading_day(startDate, endDate)
        dateGroups = Util.split_calc_date_into_group(tradingDayList, DayUnit)

        for code in codeList:
            for dateGroup in dateGroups:
                subStartDate, subEndDate = dateGroup[0], dateGroup[-1]
                taskList.append(
                    TaskMeta( marketDataLibrary,
                              code,
                              subStartDate, subEndDate,
                              False, False, tick,
                              mockTick, mockFreq,
                              overwrite,
                              monitor,
                              hbase,
                              saveFile, savePath,
                              env)
                    )

    sparkLauncher = SparkLauncher()
    sparkLauncher.setTaskList(taskList)
    sparkLauncher.launch(maxExecutorNum)


if __name__ == "__main__":
    today = dt.datetime.today().strftime('%Y%m%d')

    marketDataLibrary = "XHFDataLib"
    startDate = "20200818"
    endDate = "20200818"
    daily = True
    minute = True
    tick = True
    mockTick = False
    mockFreq = 3
    overwrite = True
    monitor = True
    hbase = False
    saveFile = "HDFS"
    savePath = None
    env = "Spark"
    maxExecutorNum = 600

    stockList = sorted(FactorData().hset('MARKET', endDate, 'ALLA_HIS')['stock'].tolist())
    stockCodeList = stockList + INDEX_LIST + SHENWAN_I_CODE + SHENWAN_II_CODE

    cbondPool = BondData().get_bond_set(endDate, "kzz")
    codeList = sorted(list(set(cbondPool).union(CBOND_LIST))) + THIRD_INDEX_LIST
    codeList = list(set(stockCodeList).union(codeList))

    # codeList = FUND_LIST + THIRD_ADD_STOCK_ETF_INDEX_LIST

    # future_code_list = ["IF", "IC", "IH"]
    # future_list = Util.get_index_future_list(startDate, endDate, future_code_list)
    # zl00_future_list = ["{}ZL00".format(future) for future in future_code_list]
    # zl01_future_list = ["{}ZL01".format(future) for future in future_code_list]
    # codeList = future_list + zl00_future_list + zl01_future_list

    main(marketDataLibrary, codeList, startDate, endDate, daily, minute, tick, mockTick, mockFreq, overwrite, monitor,
            hbase, saveFile, savePath, env, maxExecutorNum)

