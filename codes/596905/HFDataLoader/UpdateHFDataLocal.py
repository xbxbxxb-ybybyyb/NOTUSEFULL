import datetime as dt
import pickle
import pandas as pd
from xquant.xqutils.helper import multicore_init
import multiprocessing as mp
from HFDataLoader.Config import MAX_FRAME_LENGTH
import Utils.HelpFunc as Util
from xquant.factordata import FactorData
from xquant.bonddata import BondData
from STOCK_LIST import STOCK_LIST
from Constants.INDEX_LIST import INDEX_LIST, THIRD_INDEX_LIST
from Constants.CBOND_LIST import CBOND_LIST
from Constants.FUND_LIST import ETF_LIST, LOF_LIST, FUND_LIST, THIRD_ADD_STOCK_ETF_INDEX_LIST
from FactorDataTool.Config import SHENWAN_I_CODE, SHENWAN_II_CODE


def main(marketDataLibrary, code, startDate, endDate, daily, minute, tick, mockTick, mockFreq, overwrite, monitor,
         hbase, saveFile, savePath, env):
    """ 日频和分钟数据起止日期一次更新，而TICK或MOCK_TICK频单个Task更新MAX_FRAME_LENGTH个交易日数据
    """
    from HFDataLoader.HFDataUpdate import HFDataUpdate

    hfd = HFDataUpdate(marketDataLibrary,
                        code,
                        startDate, endDate,
                        daily, minute, tick,
                        mockTick, mockFreq,
                        overwrite,
                        monitor,
                        hbase,
                        saveFile, savePath,
                        env)
    hfd.run_update()


if __name__ == "__main__":
    today = dt.datetime.today().strftime('%Y%m%d')

    marketDataLibrary = "XHFDataLib"
    startDate = "20200801"
    endDate = "20200804"
    daily = False
    minute = True
    tick = False
    mockTick = False
    mockFreq = None
    overwrite = True
    monitor = True
    hbase = True
    saveFile = "HDFS"
    savePath = "HFDataDump"
    env = "Docker"
    isMultiProcess = False

    stockList = sorted(FactorData().hset('MARKET', endDate, 'ALLA_HIS')['stock'].tolist())
    stockPool = pd.read_csv("/data/user/015629/MISC/stock_list.csv", header=None)[0].tolist()
    codeList = sorted(list(set(stockList).union(stockPool))) + INDEX_LIST + SHENWAN_I_CODE + SHENWAN_II_CODE

    cbondPool = BondData().get_bond_set(endDate, "kzz")
    codeList = sorted(list(set(cbondPool).union(CBOND_LIST))) + THIRD_INDEX_LIST

    # codeList = FUND_LIST + THIRD_ADD_STOCK_ETF_INDEX_LIST

    # future_code_list = ["IF"]
    # future_list = Util.get_index_future_list(startDate, endDate, future_code_list)
    # zl00_future_list = ["{}ZL00".format(future) for future in future_code_list]
    # zl01_future_list = ["{}ZL01".format(future) for future in future_code_list]
    # codeList = future_list + zl00_future_list + zl01_future_list

    if daily or minute:
        if not isMultiProcess:
            for code in codeList:
                main(marketDataLibrary, code, startDate, endDate, daily, minute, False, False, mockFreq, overwrite, monitor,
                     hbase, saveFile, savePath, env)
        else :
            task_list = []
            for code in codeList:
                task = (marketDataLibrary, code, startDate, endDate, daily, minute, False, False, mockFreq, overwrite, monitor,
                                                         hbase, saveFile, savePath, env, )
                task_list.append(task)

            if len(task_list) > 0:
                assert multicore_init() == True
                pool = mp.Pool(processes=min(20, len(task_list)))
                for task in task_list:
                    pool.apply_async(main, task)
                pool.close()
                pool.join()

    if tick or mockTick:
        if tick:
            DayUnit = MAX_FRAME_LENGTH
        elif mockTick:
            DayUnit = 1
        tradingDayList = Util.get_trading_day(startDate, endDate)
        dateGroups = Util.split_calc_date_into_group(tradingDayList, DayUnit)

        if not isMultiProcess:
            for code in codeList:
                for dateGroup in dateGroups:
                    subStartDate, subEndDate = dateGroup[0], dateGroup[-1]
                    main(marketDataLibrary, code, subStartDate, subEndDate, False, False, tick, mockTick, mockFreq, overwrite, monitor,
                         hbase, saveFile, savePath, env)

        else:
            task_list = []
            for code in codeList:
                for dateGroup in dateGroups:
                    subStartDate, subEndDate = dateGroup[0], dateGroup[-1]
                    task = (marketDataLibrary, code, subStartDate, subEndDate, False, False, tick, mockTick, mockFreq, overwrite, monitor,
                                                         hbase, saveFile, savePath, env, )
                    task_list.append(task)

            if len(task_list) > 0:
                assert multicore_init() == True
                pool = mp.Pool(processes=min(20, len(task_list)))
                for task in task_list:
                    pool.apply_async(main, task)
                pool.close()
                pool.join()
