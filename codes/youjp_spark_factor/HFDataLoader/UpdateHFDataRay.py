import ray
import datetime as dt
import itertools
import pandas as pd
from HFDataLoader.Config import MAX_FRAME_LENGTH
from STOCK_LIST import STOCK_LIST
from Constants.INDEX_LIST import INDEX_LIST, SHENWAN_INDEX_LIST, THIRD_INDEX_LIST
from Constants.CBOND_LIST import CBOND_LIST
from Constants.FUND_LIST import ETF_LIST, LOF_LIST, FUND_LIST, THIRD_ADD_STOCK_ETF_INDEX_LIST
from FactorDataTool.Config import SHENWAN_I_CODE, SHENWAN_II_CODE
from xquant.xqutils.helper import multicore_init
from xquant.factordata import FactorData
from xquant.bonddata import BondData
import Utils.HelpFunc as Util


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


@ray.remote
def execute_task(task):
    main(task["marketDataLibrary"],  task["code"], task["startDate"], task["endDate"],
         task["daily"], task["minute"], task["tick"], task["mockTick"], task["mockFreq"], task["overwrite"],
         task["monitor"], task["hbase"], task["saveFile"], task["savePath"], task["env"])


def run_ray(task_list, execute_task, options={"ray.num_cpus": 20, "object_store_memory": 10 ** 9 * 20}):
    num_cpus = 8
    object_store_memory = 10**9*8
    task_num = len(task_list)
    if options is not None:
        if "ray.num_cpus" in options:
            num_cpus = min(int(options["ray.num_cpus"]), task_num)
        if "ray.object_store_memory" in options:
            object_store_memory = min(options["ray.object_store_memory"], 10**9*num_cpus)

    assert multicore_init() == True
    ray.init(num_cpus=num_cpus, object_store_memory=object_store_memory)
    ray.get([execute_task.remote(task) for task in task_list])

    # id_lists = ray.get([execute_task.remote(task) for task in task_list])

    # undo_ids = list(itertools.chain(*id_lists))
    # print("Total tiny task num:", len(undo_ids))
    #
    # while len(undo_ids):
    #     done_ids, undo_ids = ray.wait(undo_ids, min(200, len(undo_ids)))
    #     ray.get(done_ids)

    ray.shutdown()


if __name__ == "__main__":
    today = dt.datetime.today().strftime('%Y%m%d')

    marketDataLibrary = "XHFDataLib"
    startDate = "20200814"
    endDate = "20200814"
    daily = True
    minute = True
    tick = True
    mockTick = False
    mockFreq = 3
    overwrite = True
    monitor = True
    hbase = True
    saveFile = "HDFS"
    savePath = None
    env = "Docker"

    stockList = sorted(FactorData().hset('MARKET', endDate, 'ALLA_HIS')['stock'].tolist())
    stockCodeList = stockList + INDEX_LIST + SHENWAN_I_CODE + SHENWAN_II_CODE

    cbondPool = BondData().get_bond_set(endDate, "kzz")
    codeList = list(set(cbondPool).union(CBOND_LIST)) + THIRD_INDEX_LIST
    codeList = sorted(list(set(stockCodeList).union(codeList)))

    # codeList = FUND_LIST + THIRD_ADD_STOCK_ETF_INDEX_LIST

    # future_code_list = ["IF", "IC", "IH"]
    # future_list = Util.get_index_future_list(startDate, endDate, future_code_list)
    # zl00_future_list = ["{}ZL00".format(future) for future in future_code_list]
    # zl01_future_list = ["{}ZL01".format(future) for future in future_code_list]
    # codeList = future_list + zl00_future_list + zl01_future_list

    if daily or minute:
        task_list = []
        for code in codeList:
            task = dict()
            task["marketDataLibrary"] = marketDataLibrary
            task["code"] = code
            task["startDate"] = startDate
            task["endDate"] = endDate
            task["daily"] = daily
            task["minute"] = minute
            task["tick"] = False
            task["mockTick"] = False
            task["mockFreq"] = mockFreq
            task["overwrite"] = overwrite
            task["monitor"] = monitor
            task["hbase"] = hbase
            task["saveFile"] = saveFile
            task["savePath"] = savePath
            task["env"] = env

            task_list.append(task)

        run_ray(task_list, execute_task)

    if tick or mockTick:
        if tick:
            DayUnit = MAX_FRAME_LENGTH
        elif mockTick:
            DayUnit = 1
        tradingDayList = Util.get_trading_day(startDate, endDate)
        dateGroups = Util.split_calc_date_into_group(tradingDayList, DayUnit)

        task_list = []
        for code in codeList:
            for dateGroup in dateGroups:
                subStartDate, subEndDate = dateGroup[0], dateGroup[-1]
                task = dict()
                task["marketDataLibrary"] = marketDataLibrary
                task["code"] = code
                task["startDate"] = subStartDate
                task["endDate"] = subEndDate
                task["daily"] = False
                task["minute"] = False
                task["tick"] = tick
                task["mockTick"] = mockTick
                task["mockFreq"] = mockFreq
                task["overwrite"] = overwrite
                task["monitor"] = monitor
                task["hbase"] = hbase
                task["saveFile"] = saveFile
                task["savePath"] = savePath
                task["env"] = env

                task_list.append(task)

        run_ray(task_list, execute_task)


