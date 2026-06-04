#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/9/1 8:52
from Constants.INDEX_LIST import INDEX_LIST, THIRD_INDEX_LIST
from Constants.CBOND_LIST import CBOND_LIST
from FactorDataTool.Config import SHENWAN_I_CODE, SHENWAN_II_CODE
from FactorDataTool.FDToolUpdate import run_meta_task
from RunUpdate import task_scheduler, run_spark
from RunCheck import task_scheduler as task_scheduler_check
from RunCheck import run_ray

import datetime as dt
from xquant.factordata import FactorData
from xquant.bonddata import BondData
from xquant.xqutils.xqfile import HDFSFile
from xquant.xqutils.helper import link


if __name__ == "__main__":
    today = dt.datetime.today().strftime("%Y%m%d")
    lm = link.LinkMessage()

    library = "ZeusDataLib"
    dataSource = "mdp"
    startDate = today
    endDate = today

    # Update DFTool
    run_meta_task(library, startDate, endDate)

    # Update Data
    daily = True
    minute = True
    tick = True
    tran = True
    order = True
    overwrite = True
    monitor = True
    hbase = True
    saveFile = True
    savePath = "ZeusDataDump"
    maxExecutorNum = 600

    stockList = sorted(FactorData().hset("MARKET", endDate, "ALLA_HIS")["stock"].tolist())
    stockCodeList = stockList + INDEX_LIST #+ SHENWAN_I_CODE + SHENWAN_II_CODE

    cbondPool = BondData().get_bond_set(endDate, "kzz")
    codeList = sorted(list(set(cbondPool).union(CBOND_LIST))) + THIRD_INDEX_LIST
    codeList = sorted(list(set(stockCodeList).union(codeList)))

    taskList = task_scheduler(library, codeList, dataSource, startDate, endDate, daily, minute, tick, tran, order,
                              overwrite, monitor, hbase, saveFile, savePath)
    run_spark(taskList, maxExecutorNum)
    lm.sendMessage(" Today Data Spark Updated Done: {} ".format(today))

    # Check Data
    saveCheck = True
    saveCheckPath = "ZeusDataCheck"
    updateMissing = True

    hf = HDFSFile()
    if hf.exists(saveCheckPath):
        hf.delete(saveCheckPath, recursive=True)
    hf.mkdir(saveCheckPath)

    checkTaskList = task_scheduler_check(library, codeList, dataSource, startDate, endDate, daily, minute, tick, tran, order,
                   overwrite, monitor, hbase, saveFile, savePath, saveCheck, saveCheckPath, updateMissing)
    run_ray(checkTaskList)

    all_files = hf.listdir("{}/".format(saveCheckPath))
    code_list = sorted(list(set([file.split("_")[0] for file in all_files])))
    lm.sendMessage(" Today Data Check Done: {}, Data Missing Codes: {} ".format(today, code_list))

    if len(code_list) > 10:
        if hf.exists(saveCheckPath):
            hf.delete(saveCheckPath, recursive=True)
        hf.mkdir(saveCheckPath)

        run_ray(checkTaskList)

        all_files = hf.listdir("{}/".format(saveCheckPath))
        code_list = sorted(list(set([file.split("_")[0] for file in all_files])))
        lm.sendMessage(" Today Data Double Check Done: {}, Data Missing Codes: {} ".format(today, code_list))


