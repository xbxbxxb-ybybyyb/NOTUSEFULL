from HFDataLoader.Config import DAILY_SUFFIX, MINUTE_SUFFIX, TICK_SUFFIX, MOCK_TICK_SUFFIX
from FactorDataTool.Config import CITICS_I_CODE, CITICS_II_CODE, SW_I_CODE, SW_II_CODE, SHENWAN_I_CODE, SHENWAN_II_CODE
from Constants.INDEX_LIST import INDEX_LIST, THIRD_INDEX_LIST
from Constants.CBOND_LIST import CBOND_LIST
from Constants.FUND_LIST import ETF_LIST, LOF_LIST, FUND_LIST
from HFDataMonitor.DataCheck import DataCheck
import Utils.HelpFunc as Util

import os
import pickle
import pandas as pd
import datetime as dt
from xquant.xqutils.xqfile import HDFSFile
from xquant.xqutils.helper import multicore_init
from xquant.factordata import FactorData
from xquant.bonddata import BondData
import multiprocessing as mp


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


if __name__ == "__main__":
    today = dt.datetime.today().strftime('%Y%m%d')

    marketDataLibrary = "XHFDataLib"
    startDate = "20200814"
    endDate = "20200814"
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
    saveFile = "HDFS" # None #
    savePath = None
    saveCheck = True
    saveCheckPath = "HFDataCheck"
    updateMissing = True
    env = "Docker"
    isMultiProcess = True

    stockList = sorted(FactorData().hset('MARKET', endDate, 'ALLA_HIS')['stock'].tolist())
    stockCodeList = stockList + INDEX_LIST + SHENWAN_I_CODE + SHENWAN_II_CODE

    cbondPool = BondData().get_bond_set(endDate, "kzz")
    codeList = sorted(list(set(cbondPool).union(CBOND_LIST))) + THIRD_INDEX_LIST
    codeList = sorted(list(set(stockCodeList).union(codeList)))

    # codeList = FUND_LIST

    if not isMultiProcess:
        for code in codeList:
            main(marketDataLibrary, code, startDate, endDate, daily, minute, tick, mockTick, mockFreq, overwrite, monitor,
                 hbase, saveFile, savePath, saveCheck, saveCheckPath, updateMissing, env)
    else:
        task_list = []
        for code in codeList:
            task = (marketDataLibrary, code, startDate, endDate, daily, minute, tick, mockTick, mockFreq, overwrite, monitor,
                 hbase, saveFile, savePath, saveCheck, saveCheckPath, updateMissing, env, )
            task_list.append(task)

        if len(task_list) > 0:
            assert multicore_init() == True
            pool = mp.Pool(processes=min(20, len(task_list)))
            for task in task_list:
                pool.apply_async(main, task)
            pool.close()
            pool.join()




