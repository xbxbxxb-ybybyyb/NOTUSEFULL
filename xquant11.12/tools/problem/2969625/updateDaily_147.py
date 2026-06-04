import ray
from System.CalculationScheduler import CalculationScheduler
from System.TradingDay import getTradingDay, getNDaysOff
from CommonUtils.CalculationMonitor import CalculationMonitor, check_completeness
import datetime as dt


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
    marketDataLibrary = "ZeusNewDataLib"
    tickLibrary = "Channel147STickDataLib"
    tranOrderLibrary ="OrderTradeDataSZ2023"
    l2pTickLibrary = ""
    l2pTranOrderLibrary = ""
    INFLibrary = "INFactor"

    tickOutputLibrary = "Factor_147_Channel_SZ"
    l2pTickOutputLibrary = ""
    minuteOutputLibrary = ""

    tickCleanMode = "StartNotEnd"  # ["StartEnd", "StartNotEnd]

    mode = "Spark"
    # For Local, Spark & Ray
    dayUnit = 1
    # For Local & Spark
    stockUnit = 1
    # For Spark
    maxExecutorNum = 600
    userID = "018106"
    sparkLogFilePath = "{}/sparkMain/".format(userID)
    # For Ray
    stockGroupNum = 1
    AIMRNum = 0

    startDate = int(dt.datetime.strftime(dt.datetime.now(), "%Y%m%d"))
    if dt.datetime.now().weekday() < 5:
        if dt.datetime.now().hour < 19:
            startDate = getNDaysOff(startDate, 1)
    else:
        startDate = getNDaysOff(startDate, 1)
    endDate = startDate
#    startDate = 20230717
#    endDate = 20230720


    assetType = "Stock"

    stockL2PList = []

    from xquant.factordata import FactorData
    s = FactorData()

    dateList = getTradingDay(startDate, endDate)
    stockList = set()
    for date in dateList:
        tmpStockList = s.hset("MARKET", str(date), "ALLA")["stock"].to_list()
        stockList = set(stockList).union(set(tmpStockList))
    stockList = sorted([each for each in stockList if each.endswith("SZ")])

    # path = '/data/user/018106/TrendFactor/StockList/CBstockList.txt'
    # factor_path = open(path, 'r')
    # factor_data = factor_path.readlines()
    # stockList = eval(factor_data[0])


#    import pandas as pd
#    import pickle
#    data = pd.read_excel('/data/user/018106/TrendFactor/FactorList/036147factorList/Everest_1S_Factor_Info_20220524.xlsx')
#    everestFactorList = sorted(set(data["Exist"].dropna().to_list() + data["New"].dropna().to_list()))
#    with open("/data/user/018106/TrendFactor/FactorList/036147factorList/KunlunFactorList1S_20220701.pickle", "rb") as f:
#        kunlunFactorList = pickle.load(f)["stockFactorNames"]
#    factorList_cal = sorted(set(everestFactorList + kunlunFactorList))

#    import pandas as pd
#    df_factor = pd.read_excel('/data/user/018106/TrendFactor/factor_pass/final_0907_1.xlsx')
#    factorList_old_1 = df_factor['oldNotOrder'][~df_factor['oldNotOrder'].isnull()].tolist() + df_factor['oldOrder'][~df_factor['oldOrder'].isnull()].tolist() + df_factor['SPNotOrder'][~df_factor['SPNotOrder'].isnull()].tolist() + df_factor['SPOrder'][~df_factor['SPOrder'].isnull()].tolist() + \
#                 df_factor['CB'][~df_factor['CB'].isnull()].tolist()
#    factorList_new = df_factor['newNotOrder'][~df_factor['newNotOrder'].isnull()].tolist() + df_factor['newOrder'][~df_factor['newOrder'].isnull()].tolist()

##    factorList_old = [i for i in factorList_old_1 if i not in factorList_cal]
#    factorList_old = factorList_old_1 
#    ####################################################
#    # factorList_HXJ = pd.read_excel('/data/user/018106/TrendFactor/FactorList/CBHXJ/cbstockfactor_list_20220916.xlsx')['FactorName'].tolist()
#    # factorList_old = [i for i in factorList_HXJ if i in factorList_old]
#    # factorList_new = [i for i in factorList_HXJ if i in factorList_new]
#    ####################################################

#    factorList = factorList_old + factorList_new


#    from FactorConfig.FACTOR_CONFIG import FACTOR_CONFIG_ZEUS, FACTOR_CONFIG_ALGO, FACTOR_CONFIG_EASY, FACTOR_CONFIG_MDF
#    from FactorConfig.FACTOR_CONFIG_New import FACTOR_CONFIG
#    from FactorConfig.TAG_CONFIG import TAG_CONFIG
#    FACTOR_CONFIG_ALL = FACTOR_CONFIG_ZEUS + FACTOR_CONFIG_ALGO + FACTOR_CONFIG_EASY + FACTOR_CONFIG_MDF

#    taskList = None

#    TICK_FACTOR_CONFIG_1 = [each for each in FACTOR_CONFIG_ALL if each["FactorName"] in factorList_old]
#    TICK_FACTOR_CONFIG_2 = [each for each in FACTOR_CONFIG if each['FactorName'] in factorList_new]
#    TICK_FACTOR_CONFIG = TICK_FACTOR_CONFIG_1 + TICK_FACTOR_CONFIG_2
#    TICK_TAG_CONFIG = TAG_CONFIG
#    factorConfig = TICK_FACTOR_CONFIG_1 + TICK_FACTOR_CONFIG_2 + TICK_TAG_CONFIG
    import json
    with open('/data/user/018106/TrendFactor/FactorList/AlbestFactorList/ray_albest_20220201_20220414_new.json', 'rb') as output:
        Albest = json.load(output)
    #读因子
    path = '/data/user/018106/TrendFactor/FactorList/EverestStockList/everest_use_factors.txt'
    factor_path = open(path,'r')
    factor_data = factor_path.readlines()
    Everest = eval(factor_data[0])
    import pickle
    with open('/data/user/017023/share/CB_Sample/zg_lyh_115_20230320.pkl', 'rb') as output:
        CB = pickle.load(output)
    with open('/data/user/018106/TrendFactor/FactorList/EverestStockList/everest_use_factors_new.pickle','rb') as output:
        Everest_new = pickle.load(output)
    factorList = list((set(Albest).union(set(Everest))).union(set(CB)).union(set(Everest_new)))
    
#    path = '/data/user/018106/TrendFactor/FactorList/HXJTiaoCang/factorList.txt'
#    factor_path = open(path,'r')
#    factor_data = factor_path.readlines()
#    TC = eval(factor_data[0])
#    factorList = list(set(TC).union(set(factorList)))


    from FactorConfig.FACTOR_CONFIG import FACTOR_CONFIG_ZEUS, FACTOR_CONFIG_ALGO, FACTOR_CONFIG_EASY, FACTOR_CONFIG_MDF
    from FactorConfig.FACTOR_CONFIG_New import FACTOR_CONFIG
    from FactorConfig.TAG_CONFIG import TAG_CONFIG
    FACTOR_CONFIG_ALL = FACTOR_CONFIG_ZEUS + FACTOR_CONFIG_ALGO + FACTOR_CONFIG_EASY + FACTOR_CONFIG_MDF

    taskList = None

#    TICK_FACTOR_CONFIG_1 = [each for each in FACTOR_CONFIG_ALL if each["FactorName"] in factorList_old]
#    TICK_FACTOR_CONFIG_2 = [each for each in FACTOR_CONFIG if each['FactorName'] in factorList_new]
    TICK_TAG_CONFIG = TAG_CONFIG
#    TICK_FACTOR_CONFIG = TICK_FACTOR_CONFIG_1 + TICK_FACTOR_CONFIG_2
#    factorConfig = TICK_FACTOR_CONFIG_1 + TICK_FACTOR_CONFIG_2 + TICK_TAG_CONFIG
    TICK_FACTOR_CONFIG = [each for each in FACTOR_CONFIG_ALL if each["FactorName"] in factorList]
    factorConfig = TICK_FACTOR_CONFIG + TICK_TAG_CONFIG
    taskList = None

    # factorList = ['FactorActiveTradeBidAmtDoD']
    # TICK_FACTOR_CONFIG = [{'FactorName': 'factorActiveTradeBidAmtDoD', 'ClassName': 'FactorActiveTradeBidAmtDoD', 'MinuteLength': 10, 'FactorType': 'TS', 'DataSource': ['TR', 'T', 'M'], 'Owner': '015619(LST)'}]
    # factorConfig = TICK_FACTOR_CONFIG + TICK_TAG_CONFIG

    cm = CalculationMonitor(assetType, "Daily", startDate, endDate, stockList, tickOutputLibrary, TICK_FACTOR_CONFIG,
                            tick_tag_list=TICK_TAG_CONFIG)

    try:

        cm.print_launch_info()

        flag = cm.load_update_flag('SZ')
        
        if 0 <= dt.datetime.now().hour < 19:
            try_times = 1
        else:
            try_times = 0

        while not flag:

            try_times += 1
            if try_times == 1:
                checkMode = None
            else:
                checkMode = "Spark"
            flag = main(marketDataLibrary, tickLibrary, tranOrderLibrary, l2pTickLibrary, l2pTranOrderLibrary, INFLibrary,
                        tickCleanMode, tickOutputLibrary, l2pTickOutputLibrary, minuteOutputLibrary, assetType, factorConfig,
                        startDate, endDate, stockList, stockL2PList, mode, dayUnit, stockUnit, maxExecutorNum, stockGroupNum,
                        AIMRNum, sparkLogFilePath, taskList, checkMode=checkMode)
                        
            if checkMode is not None:
                cm.print_check_info("Tick", flag,'SZ', try_times)

        cm.print_finish_info()
        cm.print_update_flag(flag, 'SZ')

    except:

        cm.print_unexpected_info()



