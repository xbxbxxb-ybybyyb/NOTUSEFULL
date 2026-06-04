import gc
import traceback
import json
import datetime as dt
from copy import deepcopy
from System.TradingDay import getTradingDay
from System.ConfigAnalyzer import ConfigAnalyzer
from System.DataManager.StockDataManager import StockDataManager
from System.DataManager.CBDataManager import CBDataManager
from System.DataManager.ETFDataManager import ETFDataManager
from System.DataManager.FutureDataManager import FutureDataManager
from System.DataManager.IndexDataManager import IndexDataManager
from System.FactorManager import FactorManager
from System.TaskMeta import TaskMeta
from System.SparkLauncher import SparkLauncher
from System.SparkTaskMeta import SparkTaskMeta
from SystemRay.TaskSplitter import TaskSplitter
from SystemRay.RayLauncher import RayLauncher
from xquant.compute.aimr import AIMR


class CalculationScheduler:
    def __init__(self):
        self.__mdLibrary = None
        self.__factorLibrary = None
        self.__assetType = None
        self.__underlyingAssetType = None
        self.__sDate = None
        self.__eDate = None
        self.__factorConfig = None
        self.__stockSetToBeCalculated = None
        self.__mode = None
        self.__dayUnit = None
        self.__stockUnit = None
        self.__maxExecutorNum = None
        self.__AIMRNum = None
        self.__stockGroupNum = None
        self.__sparkLogFilePath = None

        self.__configAnalyzer = None
        self.__taskList = []

    def setMarketDataLibrary(self, mdLibrary):
        self.__mdLibrary = mdLibrary

    def setFactorLibrary(self, factorLibrary):
        self.__factorLibrary = factorLibrary

    def setAssetType(self, assetType):
        self.__assetType = assetType
        self.__underlyingAssetType = {"CB": "Stock", "ETF": "Index", "Future": "Index", "Index": "Index"}.get(assetType)

    def setStartDate(self, sDate):
        self.__sDate = sDate

    def setEndDate(self, eDate):
        self.__eDate = eDate

    def setFactorConfig(self, factorConfig):
        self.__factorConfig = deepcopy(factorConfig)

    def setStockListToBeCalculated(self, stockList):
        self.__stockSetToBeCalculated = set(stockList)

    def setMode(self, mode):
        self.__mode = mode

    def setMaxExecutorNum(self, maxExecutorNum):
        self.__maxExecutorNum = maxExecutorNum

    def setUnit(self, dayUnit, stockUnit):
        self.__dayUnit = dayUnit
        self.__stockUnit = stockUnit

    def setAIMRNum(self, AIMRNum):
        self.__AIMRNum = AIMRNum

    def setStockGroupNum(self, stockGroupNum):
        self.__stockGroupNum = stockGroupNum

    def setSparkLogFilePath(self, sparkLogFilePath):
        self.__sparkLogFilePath = sparkLogFilePath

    def startCalculation(self):
        if self.__mode == "Ray":
            if self.__AIMRNum > 0:
                self.__runTasksRayUsingAIMR()
            else:
                dt1 = dt.datetime.now()
                self.__initConfigAnalyzer()
                dt2 = dt.datetime.now()
                print("INFO: Time cost for config analysis: {} min".format(round((dt2 - dt1).total_seconds() / 60, 2)))
                self.__splitTasksRay()
                dt3 = dt.datetime.now()
                print("INFO: Time cost for splitting tasks: {} min".format(round((dt3 - dt2).total_seconds() / 60, 2)))

                self.__runTasksRay()
        else:
            dt1 = dt.datetime.now()
            self.__initConfigAnalyzer()
            dt2 = dt.datetime.now()
            print("INFO: Time cost for config analysis: {} min".format(round((dt2 - dt1).total_seconds() / 60, 2)))
            self.__splitTasks()
            dt3 = dt.datetime.now()
            print("INFO: Time cost for splitting tasks: {} min".format(round((dt3 - dt2).total_seconds() / 60, 2)))

            if self.__mode == "Local":
                self.__runTasksLocal()
            elif self.__mode == "Spark":
                self.__runTasksSpark()
            else:
                raise Exception("ERROR: Wrong Mode for CalculationScheduler")

    def __initConfigAnalyzer(self):
        self.__configAnalyzer = ConfigAnalyzer(self.__mdLibrary, self.__assetType, self.__underlyingAssetType,
                                               self.__factorConfig)
        self.__configAnalyzer.analyzeConfig(self.__sDate, self.__eDate)

    def __splitTasks(self):
        tradingDayList = getTradingDay(self.__sDate, self.__eDate)
        startDateList = tradingDayList[::self.__dayUnit]
        endDateList = tradingDayList[self.__dayUnit - 1:-1:self.__dayUnit] + [tradingDayList[-1]]

        for sDate, eDate in zip(startDateList, endDateList):
            stockSetCalculated = set()
            for stock in self.__stockSetToBeCalculated:
                if stock in stockSetCalculated:
                    continue

                stockSetTS = {stock}
                stockSetAll = self.__configAnalyzer.getStockSetAll(stock, sDate, eDate)

                for stockSameGroup in stockSetAll:
                    if len(stockSetTS) == self.__stockUnit:
                        self.__taskList.append(TaskMeta(sDate, eDate, stockSetTS))
                        break

                    if stockSameGroup not in self.__stockSetToBeCalculated or stockSameGroup in stockSetCalculated:
                        continue

                    stockSetAllSameGroup = self.__configAnalyzer.getStockSetAll(stockSameGroup, sDate, eDate)

                    if len(stockSetAllSameGroup - stockSetAll) <= 1:
                        stockSetCalculated.add(stockSameGroup)
                        stockSetTS.add(stockSameGroup)
                else:
                    self.__taskList.append(TaskMeta(sDate, eDate, stockSetTS))

    def __splitTasksRay(self):
        taskSplitter = TaskSplitter(self.__stockSetToBeCalculated, self.__sDate, self.__eDate, self.__dayUnit,
                                    self.__stockGroupNum, self.__configAnalyzer)
        taskSplitter.splitTask()
        self.__taskList = taskSplitter.getTaskList()

    def __runTasksLocal(self):
        startDatetime = dt.datetime.now()

        for taskMeta in self.__taskList:
            sDate = taskMeta.getStartDate()
            eDate = taskMeta.getEndDate()
            stockSetTS = taskMeta.getStockSetTS()

            stockSetAll = set()
            for stock in stockSetTS:
                stockSetAll = stockSetAll.union(self.__configAnalyzer.getStockSetAll(stock, sDate, eDate))

            t1 = dt.datetime.now()
            if self.__assetType == "Stock":
                dataManager = StockDataManager(self.__mdLibrary, self.__assetType, self.__underlyingAssetType, sDate,
                                               eDate, stockSetTS, stockSetAll, self.__configAnalyzer)
            elif self.__assetType == "CB":
                dataManager = CBDataManager(self.__mdLibrary, self.__assetType, self.__underlyingAssetType, sDate,
                                            eDate, stockSetTS, stockSetAll, self.__configAnalyzer)
            elif self.__assetType == "ETF":
                dataManager = ETFDataManager(self.__mdLibrary, self.__assetType, self.__underlyingAssetType, sDate,
                                             eDate, stockSetTS, stockSetAll, self.__configAnalyzer)
            elif self.__assetType == "Future":
                dataManager = FutureDataManager(self.__mdLibrary, self.__assetType, self.__underlyingAssetType, sDate,
                                             eDate, stockSetTS, stockSetAll, self.__configAnalyzer)
            elif self.__assetType == "Index":
                dataManager = IndexDataManager(self.__mdLibrary, self.__assetType, self.__underlyingAssetType, sDate,
                                             eDate, stockSetTS, stockSetAll, self.__configAnalyzer)
            else:
                raise Exception("Unsupported Asset Type")

            try:
                dataManager.loadData()
            except:
                print(traceback.print_exc())
                raise Exception("ERROR: An unexpected error occurred when loading data for {} between {} and {}"
                                .format(stockSetTS, sDate, eDate))
            t2 = dt.datetime.now()

            factorManagerDict = {}
            for stock in stockSetTS:
                stockSetAllSingle = self.__configAnalyzer.getStockSetAll(stock, sDate, eDate)
                factorManagerDict[stock] = FactorManager(self.__assetType, stock, self.__factorConfig, sDate, eDate,
                                                         stockSetAllSingle, self.__factorLibrary, dataManager)
                factorManagerDict[stock].initFactors()

            t3 = dt.datetime.now()
            tradingDayList = getTradingDay(sDate, eDate)
            for date in tradingDayList:
                if date > sDate:
                    dataManager.updateTickData(date)

                for stock in stockSetTS:
                    try:
                        factorManagerDict[stock].calculateFactors(date)
                    except:
                        print(traceback.print_exc())
                        raise Exception("ERROR: An unexpected error occurred when calculating factors for {} on {}"
                                        .format(stock, date))

            t4 = dt.datetime.now()
            print("Data Loading Time:", t2 - t1, "Factor Computing Time:", t4 - t3)

            del factorManagerDict
            del dataManager

            gc.collect()

        endDatetime = dt.datetime.now()
        print("INFO: Time cost for factor calculation: {} min"
              .format(round((endDatetime - startDatetime).total_seconds() / 60, 2)))

    def __runTasksSpark(self):
        startDatetime = dt.datetime.now()

        taskList = []
        for i, taskMeta in enumerate(self.__taskList):
            sDate = taskMeta.getStartDate()
            eDate = taskMeta.getEndDate()
            stockSetTS = taskMeta.getStockSetTS()

            taskList.append(
                SparkTaskMeta(self.__mdLibrary, self.__factorLibrary, self.__assetType, self.__underlyingAssetType,
                              self.__factorConfig, sDate, eDate, stockSetTS, self.__sparkLogFilePath, i)
            )

        sparkLauncher = SparkLauncher()
        sparkLauncher.setTaskList(taskList)
        sparkLauncher.setLogFilePath(self.__sparkLogFilePath)
        sparkLauncher.launch(self.__maxExecutorNum)

        endDatetime = dt.datetime.now()
        print("INFO: Time cost for factor calculation: {} min"
              .format(round((endDatetime - startDatetime).total_seconds() / 60, 2)))

    def __runTasksRay(self):
        startDatetime = dt.datetime.now()

        rayLauncher = RayLauncher(self.__mdLibrary, self.__factorLibrary, self.__factorConfig)
        rayLauncher.setTaskList(self.__taskList)
        rayLauncher.launch(self.__sDate, self.__eDate, self.__stockSetToBeCalculated)

        endDatetime = dt.datetime.now()
        print("INFO: Time cost for factor calculation: {} min"
              .format(round((endDatetime - startDatetime).total_seconds() / 60, 2)))

    def __runTasksRayUsingAIMR(self):
        tradingDayList = getTradingDay(self.__sDate, self.__eDate)
        tradingDayNum = len(tradingDayList)
        aimrNum = min(self.__AIMRNum, tradingDayNum)
        tradingDayNumPerGroup, residual = divmod(tradingDayNum, aimrNum)
        tradingDayNumPerGroupList = ([tradingDayNumPerGroup] * (aimrNum - residual)
                                     + [tradingDayNumPerGroup + 1] * residual)
        startIndexList = [sum(tradingDayNumPerGroupList[:i]) for i in range(len(tradingDayNumPerGroupList))]
        endIndexList = startIndexList[1:] + [tradingDayNum]

        parallelList = ["{}-{}-{}-{}-{}-{}".format(self.__mdLibrary, self.__factorLibrary, tradingDayList[sIndex],
                                                   tradingDayList[eIndex - 1], self.__dayUnit, self.__stockGroupNum)
                        for sIndex, eIndex in zip(startIndexList, endIndexList)]
        params = {
            "parallel_list": parallelList,
            "docker_version": "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:prd_v3.0",
            "tag": "xquant",
            "cpu": self.__stockGroupNum + 1,
            "gpu": 0,
            "memory": 200 * 1000
        }
        print(params)

        AIMR.runTasks("/SystemRay/AIMRWorker.py", json.dumps(params))
