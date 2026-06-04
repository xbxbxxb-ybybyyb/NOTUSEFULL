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
from System.DataManager.INFDataManager import INFDataManager
from System.DataManager.StockDataManagerAfternoon import StockDataManagerAfternoon
from System.FactorManager import FactorManager
from CommonUtils.MyPrint import myPrint
from xquant.compute.sparkmr import Configuration
from xquant.compute.sparkmr import Job
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
        job._Job__executor_task_num = 1
        job.add_tasks(self.__taskList)
        job.set_func(self.func)
        job.start()

        hf = HDFSFile()
        hf.delete(self.__getDstDir(removeID=True), recursive=True)

    @staticmethod
    def func(context, taskMeta):
        os.environ["OPENBLAS_NUM_THREADS"] = "1"
        os.environ["MKL_NUM_THREADS"] = "1"

        mdLibrary = taskMeta.marketDataLibrary
        tickLibrary = taskMeta.tickLibrary
        tranOrderLibrary = taskMeta.tranOrderLibrary
        l2pTickLibrary = taskMeta.l2pTickLibrary
        l2pTranOrderLibrary = taskMeta.l2pTranOrderLibrary
        infLibrary = taskMeta.infLibrary
        tickCleanMode = taskMeta.tickCleanMode
        tickFactorLibrary = taskMeta.tickOutputLibrary
        l2pTickFactorLibrary = taskMeta.l2pTickOutputLibrary
        minuteFactorLibrary = taskMeta.minuteOutputLibrary
        assetType = taskMeta.assetType
        underlyingAssetType = taskMeta.underlyingAssetType
        factorConfig = taskMeta.factorConfig
        sDate = taskMeta.startDate
        eDate = taskMeta.endDate
        stockSetTS = taskMeta.stockSetTS
        stockSetL2P = taskMeta.stockSetL2P
        logFilePath = taskMeta.logFilePath
        taskID = taskMeta.taskID

        configAnalyzer = ConfigAnalyzer(mdLibrary, assetType, underlyingAssetType, factorConfig)
        configAnalyzer.analyzeConfig(sDate, eDate)

        stockSetCS = set()
        stockSetAll = set()
        for stock in stockSetTS:
            stockSetAllSingle = configAnalyzer.getStockSetAll(stock, sDate, eDate)
            stockSetCS = stockSetCS.union(stockSetAllSingle - {stock})
            stockSetAll = stockSetAll.union(stockSetAllSingle)

        if assetType == "Stock":
            dataManager = StockDataManager(mdLibrary, tickLibrary, tranOrderLibrary, l2pTickLibrary, l2pTranOrderLibrary,
                                           infLibrary, tickCleanMode, assetType, underlyingAssetType, sDate,
                                           eDate, stockSetTS, stockSetCS, stockSetAll, stockSetL2P, configAnalyzer)
        elif assetType == "CB":
            dataManager = CBDataManager(mdLibrary, tickLibrary, tranOrderLibrary, l2pTickLibrary, l2pTranOrderLibrary,
                                        tickCleanMode, assetType, underlyingAssetType, sDate, eDate, stockSetTS,
                                        stockSetCS, stockSetAll, stockSetL2P, configAnalyzer)
        elif assetType == "ETF":
            dataManager = ETFDataManager(mdLibrary, assetType, underlyingAssetType, sDate, eDate, stockSetTS,
                                         stockSetCS, stockSetAll, configAnalyzer)
        elif assetType == "Future":
            dataManager = FutureDataManager(mdLibrary, assetType, underlyingAssetType, sDate, eDate, stockSetTS,
                                            stockSetAll, configAnalyzer)
        elif assetType == "Index":
            dataManager = IndexDataManager(mdLibrary, assetType, underlyingAssetType, sDate, eDate, stockSetTS,
                                           stockSetAll, configAnalyzer)
        elif assetType == "INF":
            dataManager = INFDataManager(mdLibrary, assetType, underlyingAssetType, sDate, eDate, stockSetTS,
                                         stockSetAll, configAnalyzer)
        elif assetType == "StockAfternoon":
            dataManager = StockDataManagerAfternoon(mdLibrary, infLibrary, assetType, underlyingAssetType, sDate, eDate,
                                                    stockSetTS, stockSetAll, configAnalyzer)
        else:
            raise Exception("Unsupported Asset Type")

        try:
            dataManager.loadData()
        except:
            myPrint(traceback.format_exc())
            myPrint(f"ERROR: An unexpected error occurred when loading data for {stockSetTS} between {sDate} and {eDate}")

            hf = HDFSFile(dfs=context.get_hdfs())
            with hf.open("{}/{}_{}_{}.log".format(logFilePath, sDate, eDate, taskID), "wb") as f:
                f.write(f"An unexpected error occurred when loading data for {stockSetTS} between {sDate} and {eDate}\r\n")
                f.write("Traceback: {}".format(traceback.format_exc()))

            return

        factorManagerDict = {}
        for stock in stockSetTS:
            stockSetAllSingle = configAnalyzer.getStockSetAll(stock, sDate, eDate)
            factorManagerDict[stock] = FactorManager(assetType, stock, factorConfig, sDate, eDate, stockSetAllSingle,
                                                     tickFactorLibrary, l2pTickFactorLibrary, minuteFactorLibrary,
                                                     dataManager)
            factorManagerDict[stock].initFactors()

        tradingDayList = getTradingDay(sDate, eDate)
        for date in tradingDayList:
            if date > sDate:
                dataManager.updateTickData(date)

            for stock in stockSetTS:
                try:
                    factorManagerDict[stock].calculateFactors(date)
                except:
                    myPrint(traceback.format_exc())
                    myPrint(f"ERROR: An unexpected error occurred when calculating factors for {stock} on {date}")

                    hf = HDFSFile(dfs=context.get_hdfs())
                    with hf.open("/{}/{}_{}_{}.log".format(logFilePath, date, stock, taskID), "wb") as f:
                        f.write(f"ERROR: An unexpected error occurred when calculating factors for {stock} on {date}; "
                                f"Start Date {sDate}, End Date {eDate}\r\n")
                        f.write("Traceback: {}".format(traceback.format_exc()))

            gc.collect()

    def __getSparkConf(self, maxExecutorNum):
        config = Configuration()
        config.set_app_name(str(self.__uuid))
        config.set_dst_dir(self.__getDstDir())
        config.set_env_dir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#        config.set_executor_instances(str(min(len(self.__taskList), maxExecutorNum)))
        config._Configuration__config_map["spark"]["spark.executor.instances"] = str(maxExecutorNum)

        config.set_executor_memory("8G")
        config.set_driver_memory("100G")

        return config

    def __getDstDir(self, removeID=False):
        logFilePath = self.__logFilePath[self.__logFilePath.index("/") + 1:] if removeID else self.__logFilePath

        return f"{logFilePath}/{self.__uuid}/"
