import ray
from System.CalculationScheduler import CalculationScheduler
from System.TradingDay import getTradingDay, getNDaysOff
from CommonUtils.CalculationMonitor import CalculationMonitor, check_completeness
import datetime as dt
from CalcBaseTask import get_cal_base_task_list
from xquant.factordata import FactorData

def addFactors(libraryName, factorNames):
    fd = FactorData()

    for factorName in factorNames:
        try:
            fd.add_factor(libraryName, [factorName])
        except Exception as e:
            print(e)


def main(mdLibrary, tickLibrary, tranOrderLibrary, l2pTickLibrary, l2pTranOrderLibrary, infLibrary, tickCleanMode,
         tickFactorLibrary, l2pTickFactorLibrary, minuteFactorLibrary, assetType, factorConfig, sDate, eDate, stockList,
         stockL2PList, mode, dayUnit, stockUnit, maxExecutorNum, stockGroupNum, AIMRNum, sparkLogFilePath,
         taskList=None, checkMode=None):
    if assetType == "INF":
        extraFactorNameList = ["timestamp", "symbols"]
    else:
        extraFactorNameList = ["timestamp"]
    tickFactorNameList = [config["FactorName"] for config in factorConfig if "FactorName" in config and config.get("BType", "Tick") == "Tick"]
    minuteFactorNameList = [config["FactorName"] for config in factorConfig if "FactorName" in config and config.get("BType", "Tick") == "Minute"]
    if tickFactorNameList:
        addFactors(tickFactorLibrary, tickFactorNameList + extraFactorNameList)
        if l2pTickFactorLibrary != "":
            addFactors(l2pTickFactorLibrary, tickFactorNameList + extraFactorNameList)
    if minuteFactorNameList:
        addFactors(minuteFactorLibrary, minuteFactorNameList + extraFactorNameList)

    calculationScheduler = CalculationScheduler()

    calculationScheduler.setMarketDataLibrary(mdLibrary)
    calculationScheduler.setTickLibrary(tickLibrary)
    calculationScheduler.setTranOrderLibrary(tranOrderLibrary)
    calculationScheduler.setL2PTickLibrary(l2pTickLibrary)
    calculationScheduler.setL2PTranOrderLibrary(l2pTranOrderLibrary)
    calculationScheduler.setINFLibrary(infLibrary)
    calculationScheduler.setTickCleanMode(tickCleanMode)
    calculationScheduler.setFactorLibrary(tickFactorLibrary, l2pTickFactorLibrary, minuteFactorLibrary)
    calculationScheduler.setAssetType(assetType)
    calculationScheduler.setFactorConfig(factorConfig)
    calculationScheduler.setStartDate(sDate)
    calculationScheduler.setEndDate(eDate)
    calculationScheduler.setStockListToBeCalculated(stockList)
    calculationScheduler.setStockL2PList(stockL2PList)
    calculationScheduler.setMode(mode)
    calculationScheduler.setUnit(dayUnit=dayUnit, stockUnit=stockUnit)
    calculationScheduler.setMaxExecutorNum(maxExecutorNum)
    calculationScheduler.setStockGroupNum(stockGroupNum)
    calculationScheduler.setAIMRNum(AIMRNum)
    calculationScheduler.setSparkLogFilePath(sparkLogFilePath)

    if checkMode in ["Local", "Spark"]:
        tickFactorNameList, taskList = check_completeness(
            checkMode, userID, assetType, tickFactorLibrary, mdLibrary, stockList, tickFactorNameList, factorConfig, str(sDate),
            str(eDate), taskList, tickLibrary, anchor_to_tick=True)
        print(len(taskList))
        if len(taskList) > 0:
            factorConfig = [each for each in factorConfig if each["FactorName"] in tickFactorNameList]
            calculationScheduler.setFactorConfig(factorConfig)
            calculationScheduler.setTaskList(taskList)
            calculationScheduler.startCalculation()
        else:
            return True
    else:
        calculationScheduler.setTaskList(taskList)
        calculationScheduler.startCalculation()


if __name__ == "__main__":
    marketDataLibrary = "ZeusDataLib"
    tickLibrary_SH = "Channel1STickDataLib"#"Channel036STickDataLib"
    tickLibrary_SZ = "Channel036STickDataLib"
    tranOrderLibrary = "OrderTradeData"
    l2pTickLibrary = ""
    l2pTranOrderLibrary = ""
    INFLibrary = "INFactor"

    tickOutputLibrary = "Factor_test_1s_lyh"
    l2pTickOutputLibrary = ""
    minuteOutputLibrary = ""

    tickCleanMode_SH = "StartNotEnd"  # ["StartEnd", "StartNotEnd", "NotClean"]
    # tickCleanMode_SZ = "StartNotEnd"

    mode = "Local"
    # For Local, Spark & Ray
    dayUnit = 1
    # For Local & Spark
    stockUnit = 1
    # For Spark
    maxExecutorNum = 400
    userID = "018106"
    sparkLogFilePath = "{}/sparkMain/".format(userID)
    # For Ray
    stockGroupNum = 1
    AIMRNum = 0

    startDate = 20221025
    endDate = 20221025

    assetType = "Stock"

    stockL2PList = []



    #股票因子
    stockList = []
    import pandas as pd
    factorList = pd.read_excel('/data/user/018106/TrendFactor/FactorList/系统团队已开发因子/factorList_20230620.xlsx')[0].tolist()
    factorList = factorList
#    factorList = ['factorBuyPowerModified','factorBuyPowerModified','factorAskDepthTrend',"factorBidDepth","factorPriceVolumeRatioScale"]


    from FactorConfig.FACTOR_CONFIG import FACTOR_CONFIG_ZEUS, FACTOR_CONFIG_ALGO, FACTOR_CONFIG_EASY, FACTOR_CONFIG_MDF
    from FactorConfig.FACTOR_CONFIG_New import FACTOR_CONFIG
    from FactorConfig.TAG_CONFIG import TAG_CONFIG
    from FactorConfig.CBFACTOR_CONFIG_New import factor_config
    
    FACTOR_CONFIG_ALL = FACTOR_CONFIG_ZEUS + FACTOR_CONFIG_ALGO + FACTOR_CONFIG_EASY + FACTOR_CONFIG_MDF + factor_config

    taskList = None
    taskList_all = get_cal_base_task_list()
    taskList = taskList_all
    taskList = [('000058.SZ','20210701')]
#    taskList = []
#    for task in taskList_all:
#        if task[0][-1] == 'Z':
#            taskList.append(task)
#    print(taskList)

    TICK_FACTOR_CONFIG_1 = [each for each in FACTOR_CONFIG_ALL if each["FactorName"] in factorList]
    # TICK_FACTOR_CONFIG_2 = [each for each in FACTOR_CONFIG if each['FactorName'] in factorList_new]
    TICK_TAG_CONFIG = []#TAG_CONFIG
    TICK_FACTOR_CONFIG = TICK_FACTOR_CONFIG_1
    factorConfig = TICK_FACTOR_CONFIG_1

    cm = CalculationMonitor(assetType, "Daily", startDate, endDate, stockList, tickOutputLibrary, TICK_FACTOR_CONFIG,
                            tick_tag_list=TICK_TAG_CONFIG)

    try:

        cm.print_launch_info()

        flag_1 = cm.load_update_flag('SH')
#        flag_2 = cm.load_update_flag('SZ')

        if 0 <= dt.datetime.now().hour < 19:
            try_times = 1
        else:
            try_times = 0

#        while not flag_1 or not flag_2:
        try_times = 0
        while not flag_1:

            try_times += 1
            if try_times == 1:
                checkMode = None
            else:
                checkMode = "Spark"

            flag_1 = main(marketDataLibrary, tickLibrary_SH, tranOrderLibrary, l2pTickLibrary, l2pTranOrderLibrary, INFLibrary,
                        tickCleanMode_SH, tickOutputLibrary, l2pTickOutputLibrary, minuteOutputLibrary, assetType, factorConfig,
                        startDate, endDate, stockList, stockL2PList, mode, dayUnit, stockUnit, maxExecutorNum, stockGroupNum,
                        AIMRNum, sparkLogFilePath, taskList, checkMode=checkMode)
#            flag_2 = main(marketDataLibrary, tickLibrary_SZ, tranOrderLibrary, l2pTickLibrary, l2pTranOrderLibrary,
#                          INFLibrary,
#                          tickCleanMode_SZ, tickOutputLibrary, l2pTickOutputLibrary, minuteOutputLibrary, assetType,
#                          factorConfig,
#                          startDate, endDate, stockList_SZ, stockL2PList, mode, dayUnit, stockUnit, maxExecutorNum,
#                          stockGroupNum,
#                          AIMRNum, sparkLogFilePath, taskList, checkMode=checkMode)
                       
            if checkMode is not None:
                cm.print_check_info("Tick", flag_1,"SH", try_times)
#                cm.print_check_info("Tick", flag_2,"SZ", try_times)

        cm.print_finish_info()
        cm.print_update_flag(flag_1, 'SH')
#        cm.print_update_flag(flag_2, 'SZ')

    except:

        cm.print_unexpected_info()



