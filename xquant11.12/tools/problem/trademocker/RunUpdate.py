#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/4/1 21:27
#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/3/17 12:10
import ray
import gc
import json
import datetime as dt
import pandas as pd
import multiprocessing as mp
from xquant.xqutils.helper import multicore_init
from DataUpdate.Executor import Executor
from DataUpdate.TaskMeta import TaskMeta
from DataUpdate.ExecutorSpark import SparkLauncher
from Constants.INDEX_LIST import INDEX_LIST, SHENWAN_INDEX_LIST, THIRD_INDEX_LIST
from Constants.CBOND_LIST import CBOND_LIST
from Constants.FUND_LIST import ETF_LIST, LOF_LIST, FUND_LIST, THIRD_ADD_STOCK_ETF_INDEX_LIST
from FactorDataTool.Config import SHENWAN_I_CODE, SHENWAN_II_CODE
from xquant.factordata import FactorData
from Utils.HelpFunc import get_trading_day, split_calc_date_into_group, get_full_cbond_list, get_index_future_list


def task_scheduler(library, codeList, dataSource, startDate, endDate, daily, minute, tick, tran, order,
                   overwrite, monitor, hbase, saveFile, savePath):

    taskList = []

    if daily or minute:
        for code in codeList:
            taskList.append(
                TaskMeta(
                    library,
                    code,
                    dataSource,
                    startDate,
                    endDate,
                    daily,
                    minute,
                    False,
                    False,
                    False,
                    overwrite,
                    monitor,
                    hbase,
                    saveFile,
                    savePath
                    )
                )

    if tick or tran or order:

        DayUnit = 5
        tradingDayList = get_trading_day(startDate, endDate)
        dateGroups = split_calc_date_into_group(tradingDayList, DayUnit)

#        with open("/data/user/015629/MISC/tick_tran_order_check_result.json", "rb") as f:
#            data = f.read()
#            data = json.loads(data)

#        for code, missingDateDict in data.items():
#            for dataType, missingDates in missingDateDict.items():
#                if dataType == "TR":
#                    tick = False
#                    tran = True
#                    order = False
#                elif dataType == "O":
#                    tick = False
#                    order = True
#                    tran = False
#                elif dataType == "T":
#                    tick = True
#                    order = False
#                    tran = False
#                for missingDate in missingDates:
#                    subStartDate, subEndDate = missingDate, missingDate
#                    taskList.append(
#                        TaskMeta(
#                            library,
#                            code,
#                            dataSource,
#                            subStartDate,
#                            subEndDate,
#                            False,
#                            False,
#                            tick,
#                            tran,
#                            order,
#                            overwrite,
#                            monitor,
#                            hbase,
#                            saveFile,
#                            savePath
#                    )
#                )
                
        for code in codeList:
            for dateGroup in dateGroups:
                subStartDate, subEndDate = dateGroup[0], dateGroup[-1]
                taskList.append(
                    TaskMeta(
                        library,
                        code,
                        dataSource,
                        subStartDate,
                        subEndDate,
                        False,
                        False,
                        tick,
                        tran,
                        order,
                        overwrite,
                        monitor,
                        hbase,
                        saveFile,
                        savePath
                )
            )

    return taskList

def run_meta_task(taskMeta):
    library = taskMeta.getLibrary()
    code = taskMeta.getCode()
    dataSource = taskMeta.getDataSource()
    startDate = taskMeta.getStartDate()
    endDate = taskMeta.getEndDate()
    daily = taskMeta.getDaily()
    minute = taskMeta.getMinute()
    tick = taskMeta.getTick()
    tran = taskMeta.getTran()
    order = taskMeta.getOrder()
    overwrite = taskMeta.getOverwrite()
    monitor = taskMeta.getMonitor()
    hbase = taskMeta.getHbase()
    saveFile = taskMeta.getSaveFile()
    savePath = taskMeta.getSavePath()

    exe = Executor(library, code, dataSource, startDate, endDate, daily, minute, tick, tran, order,
                   overwrite, monitor, hbase, saveFile, savePath)
    exe.run()

    gc.collect()

def run_ray(task_list, options={"ray.num_cpus": 20, "object_store_memory": 10 ** 9 * 20}):
    num_cpus = 8
    object_store_memory = 10 ** 9 * 8
    task_num = len(task_list)
    if options is not None:
        if "ray.num_cpus" in options:
            num_cpus = min(int(options["ray.num_cpus"]), task_num)
        if "ray.object_store_memory" in options:
            object_store_memory = min(options["ray.object_store_memory"], 10 ** 9 * num_cpus)

    assert multicore_init() == True
    ray.init(num_cpus=num_cpus, object_store_memory=object_store_memory)
    execute_task = ray.remote(run_meta_task)
    ray.get([execute_task.remote(task) for task in task_list])

    ray.shutdown()

def run_spark(taskList, maxExecutorNum):
    sparkLauncher = SparkLauncher()
    sparkLauncher.setTaskList(taskList)
    sparkLauncher.launch(maxExecutorNum)


if __name__ == "__main__":
    today = dt.datetime.today().strftime("%Y%m%d")
    library = "ZeusDataLib"
    dataSource = "third"
    startDate = "20210923"
    endDate = "20210923"
    daily = True
    minute = True
    tick = True
    tran = True
    order = True
    overwrite = True
    monitor = False
    hbase = True
    saveFile = True
    savePath = "ZeusDataDump"
    mode = "Spark"
    maxExecutorNum = 500

    stockList = sorted(FactorData().hset("MARKET", endDate, "ALLA_HIS")["stock"].tolist())
    stockCodeList = stockList + INDEX_LIST #+ SHENWAN_I_CODE + SHENWAN_II_CODE

    cbondCodeList =  get_full_cbond_list(startDate, endDate) + THIRD_INDEX_LIST
    codeList = sorted(list(set(stockCodeList).union(cbondCodeList)))
    
    codeList = ["002381.SZ"]

    # codeList = FUND_LIST + THIRD_ADD_STOCK_ETF_INDEX_LIST

    # future_code_list = ["IF", "IC", "IH"]
    # future_list = get_index_future_list(startDate, endDate, future_code_list)
    # zl00_future_list = ["{}ZL00".format(future) for future in future_code_list]
    # zl01_future_list = ["{}ZL01".format(future) for future in future_code_list]
    # codeList = future_list + zl00_future_list + zl01_future_list

    taskList = task_scheduler(library, codeList, dataSource, startDate, endDate, daily, minute, tick, tran, order,
                              overwrite, monitor, hbase, saveFile, savePath)
    print(" Total Task Num: {} ".format(len(taskList)))

    if mode == "Local":
        for task in taskList:
            run_meta_task(task)

    elif mode == "MultiProcess":
        if len(taskList) > 0:
            assert multicore_init() == True
            pool = mp.Pool(processes=min(20, len(taskList)))
            for task in taskList:
                pool.apply_async(run_meta_task, (task, ))
            pool.close()
            pool.join()

    elif mode == "Ray":
        run_ray(taskList)

    elif mode == "Spark":
        run_spark(taskList, maxExecutorNum)



