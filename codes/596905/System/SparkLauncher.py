import os
import uuid
import gc
import traceback
from System.TradingDay import getTradingDay
from System.ConfigAnalyzer import ConfigAnalyzer
from System.DataManager.StockDataManager import StockDataManager
from System.DataManager.CBDataManager import CBDataManager
from System.DataManager.ETFDataManager import ETFDataManager
from System.DataManager.FutureDataManager import FutureDataManager
from System.DataManager.IndexDataManager import IndexDataManager
from System.FactorManager import FactorManager
from xquant.compute.sparkmr import Configuration
from xquant.compute.sparkmr import Job
from xquant.compute.sparkmr import remote_print
from xquant.xqutils.xqfile import HDFSFile


class SparkLauncher:
    def __init__(self):
        self.__uuid = uuid.uuid1()

        self.__taskList = None
        self.__logFilePath = None

    def setTaskList(self, taskList):
        self.__taskList = taskList

    def setLogFilePath(self, logFilePath):
        self.__logFilePath = logFilePath

    def launch(self, maxExecutorNum):
        config = self.__getSparkConf(maxExecutorNum)
        job = Job(config, mode="OverWrite")
        job.add_tasks(self.__taskList)
        job.set_func(self.func)
        job.start()

        hf = HDFSFile()
        hf.delete(self.__getDstDir(removeID=True), recursive=True)

    @staticmethod
    def func(context, taskMeta):
        os.environ["OPENBLAS_NUM_THREADS"] = "1"
        os.environ["MKL_NUM_THREADS"] = "1"

        mdLibrary = taskMeta.getMarketDataLibrary()
        factorLibrary = taskMeta.getOutputLibrary()
        assetType = taskMeta.getAssetType()
        underlyingAssetType = taskMeta.getUnderlyingAssetType()
        factorConfig = taskMeta.getFactorConfig()
        sDate = taskMeta.getStartDate()
        eDate = taskMeta.getEndDate()
        stockSetTS = taskMeta.getStockSetTS()
        logFilePath = taskMeta.getLogFilePath()
        taskID = taskMeta.getTaskID()

        configAnalyzer = ConfigAnalyzer(mdLibrary, assetType, underlyingAssetType, factorConfig)
        configAnalyzer.analyzeConfig(sDate, eDate)

        stockSetAll = set()
        for stock in stockSetTS:
            stockSetAll = stockSetAll.union(configAnalyzer.getStockSetAll(stock, sDate, eDate))

        if assetType == "Stock":
            dataManager = StockDataManager(mdLibrary, assetType, underlyingAssetType, sDate, eDate, stockSetTS,
                                           stockSetAll, configAnalyzer)
        elif assetType == "CB":
            dataManager = CBDataManager(mdLibrary, assetType, underlyingAssetType, sDate, eDate, stockSetTS,
                                        stockSetAll, configAnalyzer)
        elif assetType == "ETF":
            dataManager = ETFDataManager(mdLibrary, assetType, underlyingAssetType, sDate, eDate, stockSetTS,
                                         stockSetAll, configAnalyzer)
        elif assetType == "Future":
            dataManager = FutureDataManager(mdLibrary, assetType, underlyingAssetType, sDate, eDate, stockSetTS,
                                         stockSetAll, configAnalyzer)
        elif assetType == "Index":
            dataManager = IndexDataManager(mdLibrary, assetType, underlyingAssetType, sDate, eDate, stockSetTS,
                                         stockSetAll, configAnalyzer)
        else:
            raise Exception("Unsupported Asset Type")

        try:
            dataManager.loadData()
        except:
            remote_print(traceback.format_exc())
            remote_print("ERROR: An unexpected error occurred when loading data for {} between {} and {}"
                         .format(stockSetTS, sDate, eDate))
            hf = HDFSFile()
            fileName = "{}/{}_{}_{}.log".format(logFilePath, sDate, eDate, taskID)
            with hf.open(fileName, "wb") as f:
                f.write("An unexpected error occurred when loading data for {} between {} and {}\r\n"
                        .format(stockSetTS, sDate, eDate))
                f.write("Traceback: {}".format(traceback.format_exc()))
            return

        factorManagerDict = {}
        for stock in stockSetTS:
            stockSetAllSingle = configAnalyzer.getStockSetAll(stock, sDate, eDate)
            factorManagerDict[stock] = FactorManager(assetType, stock, factorConfig, sDate, eDate, stockSetAllSingle,
                                                     factorLibrary, dataManager)
            factorManagerDict[stock].initFactors()

        tradingDayList = getTradingDay(sDate, eDate)
        for date in tradingDayList:
            if date > sDate:
                dataManager.updateTickData(date)

            for stock in stockSetTS:
                try:
                    factorManagerDict[stock].calculateFactors(date)
                except:
                    remote_print(traceback.format_exc())
                    remote_print("ERROR: An unexpected error occurred when calculating factors for {} on {}"
                                 .format(stock, date))
                    hf = HDFSFile()
                    fileName = "/{}/{}_{}_{}.log".format(logFilePath, date, stock, taskID)
                    with hf.open(fileName, "wb") as f:
                        f.write("ERROR: An unexpected error occurred when calculating factors for {} on {}; "
                                "Start Date {}, End Date {}\r\n"
                                .format(stock, date, sDate, eDate))
                        f.write("Traceback: {}".format(traceback.format_exc()))

            gc.collect()

    def __getSparkConf(self, maxExecutorNum):
        config = Configuration()
        config.set_app_name(str(self.__uuid))
        config.set_dst_dir(self.__getDstDir())
        config.set_env_dir(self.__getEnvDir())
        config.set_executor_instances(str(min(len(self.__taskList), maxExecutorNum)))
        config.set_executor_memory("4G")
        config.set_driver_memory("100G")

        return config

    def __getDstDir(self, removeID=False):
        if removeID:
            logFilePath = self.__logFilePath[self.__logFilePath.index("/") + 1:]
            return "{}/{}/".format(logFilePath, self.__uuid)
        else:
            return "{}/{}/".format(self.__logFilePath, self.__uuid)

    @staticmethod
    def __getEnvDir():
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
