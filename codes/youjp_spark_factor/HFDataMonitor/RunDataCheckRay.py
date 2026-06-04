import ray
from HFDataLoader.Config import DAILY_SUFFIX, MINUTE_SUFFIX, TICK_SUFFIX, MOCK_TICK_SUFFIX
from FactorDataTool.Config import CITICS_I_CODE, CITICS_II_CODE, SW_I_CODE, SW_II_CODE, SHENWAN_I_CODE, SHENWAN_II_CODE
from Constants.INDEX_LIST import INDEX_LIST, SHENWAN_INDEX_LIST, THIRD_INDEX_LIST
from Constants.CBOND_LIST import CBOND_LIST
from Constants.FUND_LIST import ETF_LIST, LOF_LIST, FUND_LIST, FUND_T0_LIST, THIRD_ADD_STOCK_ETF_INDEX_LIST
from HFDataMonitor.DataCheck import DataCheck
import Utils.HelpFunc as Util

import os
import pickle
import pandas as pd
import datetime as dt
import itertools
from xquant.xqutils.xqfile import HDFSFile
from xquant.xqutils.helper import multicore_init
from xquant.factordata import FactorData
from xquant.bonddata import BondData


def main(marketDataLibrary, code, startDate, endDate, daily, minute, tick, mockTick, mockFreq, overwrite,
         monitor, hbase, saveFile, savePath, saveCheck, saveCheckPath, updateMissing, env):

    code_type = Util.get_code_type(code)

    ### Step 1： 检查缺失的数据， 保存到HDFS中
    from HFDataLoader.HFDataUpdate import HFDataUpdate

    dc = DataCheck(marketDataLibrary,
                   code,
                   startDate, endDate,
                   daily=daily, minute=minute, tick=tick, mock_tick=mockTick,
                   save=saveCheck, save_path=saveCheckPath,
                   env=env)

    dc.run_check()

    ### Step 2：从HDFS中读取缺失的数据，进行重新更新
    if updateMissing:
        hf = HDFSFile()
        if saveCheckPath is None:
            saveCheckPath = "HFDataCheck"
        root = os.path.join("", saveCheckPath)
        file_name = os.path.join(root, "{}_{}.pkl".format(code, "invalid_date_list"))
        if hf.exists(file_name):
            f = hf.open(file_name, "rb")
            invalid_dict = pickle.load(f)
            if invalid_dict:
                ### 日频缺失数据
                invalid_daily = invalid_dict.get(DAILY_SUFFIX, [])
                if invalid_daily:
                    for invalid_date in invalid_daily:
                        MissingStartDate = invalid_date
                        MissingEndDate = invalid_date

                        if code_type == "INDUSTRY" and Util.get_industry_type(code) != "SHENWAN":
                            pass

                        else:

                            hfd = HFDataUpdate(marketDataLibrary,
                                       code,
                                       MissingStartDate, MissingEndDate,
                                       daily=True, minute=False, tick=False,
                                       mock_tick=False, mock_freq=mockFreq,
                                       overwrite=overwrite,
                                       monitor=monitor,
                                       hbase=hbase,
                                       save_file=saveFile, save_path=savePath,
                                       env=env)

                            hfd.run_update()

                ### 分钟频缺失数据
                invalid_minute = invalid_dict.get(MINUTE_SUFFIX, [])
                if invalid_minute:
                    for invalid_date in invalid_minute:
                        MissingStartDate = invalid_date
                        MissingEndDate = invalid_date

                        if code_type == "INDUSTRY" and Util.get_industry_type(code) != "SHENWAN":
                            pass

                        else:
                            hfd = HFDataUpdate(marketDataLibrary,
                                           code,
                                           MissingStartDate, MissingEndDate,
                                           daily=False, minute=True, tick=False,
                                           mock_tick=False, mock_freq=mockFreq,
                                           overwrite=overwrite,
                                           monitor=monitor,
                                           hbase=hbase,
                                           save_file=saveFile, save_path=savePath,
                                           env=env)

                            hfd.run_update()

                ### TICK频缺失数据
                invalid_tick = invalid_dict.get(TICK_SUFFIX, [])
                if invalid_tick:
                    for invalid_date in invalid_tick:
                        MissingStartDate = invalid_date
                        MissingEndDate = invalid_date

                        if code_type == "INDUSTRY" and Util.get_industry_type(code) in ["CITICS", "SW"]:
                            from IndustrySynthetize.IndusSynthetizeDataUpdate import IndusSynthetizeDataUpdate
                            if code in CITICS_I_CODE + CITICS_II_CODE:
                                IndusName = "CITICS."
                            elif code in SW_I_CODE + SW_II_CODE:
                                IndusName = "SW."
                            idu = IndusSynthetizeDataUpdate(marketDataLibrary,
                                                            IndusName + code,
                                                            MissingStartDate, MissingEndDate,
                                                            False, False, tick,
                                                            overwrite,
                                                            hbase,
                                                            saveFile, savePath,
                                                            env)
                            idu.run_update()

                        else:
                            hfd = HFDataUpdate(marketDataLibrary,
                                           code,
                                           MissingStartDate, MissingEndDate,
                                           daily=False, minute=False, tick=True,
                                           mock_tick=False, mock_freq=mockFreq,
                                           overwrite=overwrite,
                                           monitor=monitor,
                                           hbase=hbase,
                                           save_file=saveFile, save_path=savePath,
                                           env=env)

                            hfd.run_update()

                ### MOCK TICK 缺失数据
                invalid_mock_tick = invalid_dict.get(MOCK_TICK_SUFFIX, [])
                if invalid_mock_tick:
                    for invalid_date in invalid_mock_tick:
                        MissingStartDate = invalid_date
                        MissingEndDate = invalid_date

                        if code_type != "STOCK":
                            pass

                        else:
                            hfd = HFDataUpdate(marketDataLibrary,
                                           code,
                                           MissingStartDate, MissingEndDate,
                                           daily=False, minute=False, tick=False,
                                           mock_tick=True, mock_freq=mockFreq,
                                           overwrite=overwrite,
                                           monitor=monitor,
                                           hbase=hbase,
                                           save_file=saveFile, save_path=savePath,
                                           env=env)

                            hfd.run_update()

@ray.remote
def execute_task(task):
    main(task["marketDataLibrary"], task["code"], task["startDate"], task["endDate"],
         task["daily"], task["minute"], task["tick"], task["mockTick"], task["mockFreq"], task["overwrite"],
         task["monitor"], task["hbase"], task["saveFile"], task["savePath"],
         task["saveCheck"], task["saveCheckPath"], task["updateMissing"], task["env"])

def run_ray(task_list, execute_task, options={"ray.num_cpus": 20, "object_store_memory": 10 ** 9 * 20}):
    num_cpus = 4
    object_store_memory = 10**9*4
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
    startDate = "20200818"
    endDate = "20200818"
    ### 默认Check三个频率数据
    daily = True
    minute = True
    tick = True
    mockTick = False
    ### 以下更新数据参数
    mockFreq = None
    overwrite = True
    monitor = True
    hbase = True
    saveFile = "HDFS" # None
    savePath = None
    saveCheck = True
    saveCheckPath = "HFDataCheck"
    updateMissing = True
    env = "Docker"

    stockList = sorted(FactorData().hset('MARKET', endDate, 'ALLA_HIS')['stock'].tolist())
    stockCodeList = stockList + INDEX_LIST + SHENWAN_I_CODE + SHENWAN_II_CODE

    cbondPool = BondData().get_bond_set(endDate, "kzz")
    codeList = sorted(list(set(cbondPool).union(CBOND_LIST))) + THIRD_INDEX_LIST
    codeList = sorted(list(set(stockCodeList).union(codeList)))

    # codeList = FUND_LIST + THIRD_ADD_STOCK_ETF_INDEX_LIST

    task_list = []
    for code in codeList:
        task = dict()
        task["marketDataLibrary"] = marketDataLibrary
        task["code"] = code
        task["startDate"] = startDate
        task["endDate"] = endDate
        task["daily"] = daily
        task["minute"] = minute
        task["tick"] = tick
        task["mockTick"] = mockTick
        task["mockFreq"] = mockFreq
        task["overwrite"] = overwrite
        task["monitor"] = monitor
        task["hbase"] = hbase
        task["saveFile"] = saveFile
        task["savePath"] = savePath
        task["saveCheck"] = saveCheck
        task["saveCheckPath"] = saveCheckPath
        task["updateMissing"] = updateMissing
        task["env"] = env

        task_list.append(task)

    run_ray(task_list, execute_task)





