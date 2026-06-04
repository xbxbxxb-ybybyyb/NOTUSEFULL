import datetime as dt
import pandas as pd
from xquant.factordata import FactorData
from xquant.bonddata import BondData
from Constants.INDEX_LIST import INDEX_LIST, THIRD_INDEX_LIST
from Constants.CBOND_LIST import CBOND_LIST
from Constants.FUND_LIST import ETF_LIST, LOF_LIST, FUND_LIST
from FactorDataTool.Config import SHENWAN_I_CODE, SHENWAN_II_CODE
from SparkUtils.DataCheckUtils.SparkLauncher import SparkLauncher
from SparkUtils.DataCheckUtils.TaskMeta import TaskMeta


def main(marketDataLibrary, codeList, startDate, endDate, daily, minute, tick, mockTick, mockFreq, overwrite,
         monitor, hbase, saveFile, savePath, saveCheck, saveCheckPath, updateMissing, env, maxExecutorNum):

    taskList = []

    for code in codeList:
        taskList.append(
            TaskMeta( marketDataLibrary,
                      code,
                      startDate, endDate,
                      daily, minute, tick, mockTick, mockFreq,
                      overwrite,
                      monitor,
                      hbase,
                      saveFile, savePath,
                      saveCheck, saveCheckPath,
                      updateMissing,
                      env)
        )

    sparkLauncher = SparkLauncher()
    sparkLauncher.setTaskList(taskList)
    sparkLauncher.launch(maxExecutorNum)


if __name__ == "__main__":
    today = dt.datetime.today().strftime('%Y%m%d')

    marketDataLibrary = "ETFDataLib"
    startDate = "20200430"
    endDate = "20200327"
    ### 默认Check三个频率数据
    daily = False
    minute = False
    tick = True
    mockTick = False

    ### 以下更新数据参数
    mockFreq = None
    overwrite = True
    monitor = True
    hbase = False
    saveFile = "HDFS" # None #
    savePath = None
    saveCheck = True
    saveCheckPath = "HFDataCheck"
    updateMissing = True
    env = "Spark"
    maxExecutorNum = 300

    # stockList = sorted(FactorData().hset('MARKET', endDate, 'ALLA_HIS')['stock'].tolist())
    # stockPool = pd.read_csv("/data/user/015629/MISC/stock_list.csv", header=None)[0].tolist()
    # codeList = sorted(list(set(stockList).union(stockPool))) + INDEX_LIST + SHENWAN_I_CODE + SHENWAN_II_CODE

    # cbondPool = BondData().get_bond_set(endDate, "kzz")
    # codeList = sorted(list(set(cbondPool).union(CBOND_LIST))) + THIRD_INDEX_LIST

    codeList = ETF_LIST #FUND_LIST

    main(marketDataLibrary, codeList, startDate, endDate, daily, minute, tick, mockTick, mockFreq, overwrite, monitor,
         hbase, saveFile, savePath, saveCheck, saveCheckPath, updateMissing, env, maxExecutorNum)