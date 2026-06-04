import ray
from System.TradingDay import getTradingDay
from System.ConfigAnalyzer import ConfigAnalyzer
from SystemRay.DataLoader import DataLoader
from SystemRay.DataCollector import DataCollector
from SystemRay.DataManager import DataManager
from SystemRay.Executor import Executor


class RayLauncher:
    def __init__(self, mdLibrary, factorLibrary, factorConfig):
        self.__mdLibrary = mdLibrary
        self.__factorLibrary = factorLibrary
        self.__factorConfig = factorConfig

        self.__taskList = None

    def setTaskList(self, taskList):
        self.__taskList = taskList

    def launch(self, startDate, endDate, stockSetTSAll):
        configAnalyzer = ConfigAnalyzer(self.__mdLibrary, self.__factorConfig)
        configAnalyzer.analyzeConfig(startDate, endDate)

        DataLoaderRemote = ray.remote(DataLoader)
        ExecutorRemote = ray.remote(Executor)

        for taskMeta in self.__taskList:
            sDate = taskMeta.getStartDate()
            eDate = taskMeta.getEndDate()
            stockSetTSList = taskMeta.getStockSetTSList()

            stockSetAll = set()
            for stock in stockSetTSAll:
                stockSetAll = stockSetAll.union(configAnalyzer.getStockSetAll(stock, sDate, eDate))

            dataCollector = DataCollector(self.__mdLibrary, sDate, eDate, stockSetTSAll, stockSetAll, configAnalyzer)

            ray.init(object_store_memory=70 * 1024 ** 3)

            stockNum = len(stockSetAll)
            stockGroupNum = min(len(stockSetTSList), stockNum)
            stockNumPerGroup, residual = divmod(stockNum, stockGroupNum)
            stockNumPerGroupList = [stockNumPerGroup] * (stockGroupNum - residual) + [stockNumPerGroup + 1] * residual
            startIndexList = [sum(stockNumPerGroupList[:i]) for i in range(len(stockNumPerGroupList))]
            endIndexList = startIndexList[1:] + [stockNum]

            dataLoaderRemoteList = []
            stockListAll = list(stockSetAll)
            for startIndex, endIndex in zip(startIndexList, endIndexList):
                dataLoaderRemote = DataLoaderRemote.remote(self.__mdLibrary, sDate, eDate, stockSetTSAll,
                                                           set(stockListAll[startIndex:endIndex]), configAnalyzer)
                dataLoaderRemoteList.append(dataLoaderRemote)
                dataLoaderRemote.loadData.remote()

            dataCollector.loadData()

            for dataLoaderRemote in dataLoaderRemoteList:
                dataCollector.setAllTradingDayDict(ray.get(dataLoaderRemote.getAllTradingDayDict.remote()))
                dataCollector.setInvalidTradingDayDict(ray.get(dataLoaderRemote.getInvalidTradingDayDict.remote()))
                dataCollector.setAdjFactorDict(ray.get(dataLoaderRemote.getAdjFactorDict.remote()))
                dataCollector.setTickDataDict(*ray.get(dataLoaderRemote.getTickDataDict.remote()))
                dataCollector.setMinuteDataDict(*ray.get(dataLoaderRemote.getMinuteDataDict.remote()))
                dataCollector.setDailyDataDict(*ray.get(dataLoaderRemote.getDailyDataDict.remote()))

            ray.shutdown()

            tradingDayList = getTradingDay(sDate, eDate)
            for date in tradingDayList:
                if date > sDate:
                    ray.init(object_store_memory=70 * 1024 ** 3)

                    stockNum = len(stockSetAll)
                    stockGroupNum = min(len(stockSetTSList), stockNum)
                    stockNumPerGroup, residual = divmod(stockNum, stockGroupNum)
                    stockNumPerGroupList = [stockNumPerGroup] * (stockGroupNum - residual) + [
                        stockNumPerGroup + 1] * residual
                    startIndexList = [sum(stockNumPerGroupList[:i]) for i in range(len(stockNumPerGroupList))]
                    endIndexList = startIndexList[1:] + [stockNum]

                    dataLoaderRemoteList = []
                    stockListAll = list(stockSetAll)
                    for startIndex, endIndex in zip(startIndexList, endIndexList):
                        dataLoaderRemote = DataLoaderRemote.remote(self.__mdLibrary, sDate, eDate, stockSetTSAll,
                                                                   set(stockListAll[startIndex:endIndex]),
                                                                   configAnalyzer)
                        dataLoaderRemoteList.append(dataLoaderRemote)
                        dataLoaderRemote.updateTickData.remote()

                    dataCollector.updateMinuteAndIndexTickData(date)

                    for dataLoaderRemote in dataLoaderRemoteList:
                        dataCollector.updateTickData(date, *ray.get(dataLoaderRemote.getTickDataDict.remote()))

                    ray.shutdown()

                ray.init(object_store_memory=70 * 1024 ** 3)

                dataManagerRequirements = self.__generateDataMangerRequirements(dataCollector)
                # dataManagerRequirements = 1
                # sss = dataCollector.getTickDataDict()[0]
                # zzz = ray.put(sss)
                # s1 = ray.put(dataManagerRequirements[0])
                s2 = ray.put(dataManagerRequirements[1])
                import pickle
                with open("/data/user/015390/RayTestObject.pickle", "wb") as f:
                    pickle.dump(dataManagerRequirements[1], f)
                # s3 = ray.put(dataManagerRequirements[2])
                # s4 = ray.put(dataManagerRequirements[3])
                # s5 = ray.put(dataManagerRequirements[4])
                # s6 = ray.put(dataManagerRequirements[5])
                # s7 = ray.put(dataManagerRequirements[6])
                # s8 = ray.put(dataManagerRequirements[7])

                executorList = []
                executorTaskIDs = []
                for stockSetTS in stockSetTSList:
                    configAnalyzer = None
                    executor = ExecutorRemote.remote(sDate, eDate, stockSetTS, self.__factorLibrary,
                                                     self.__factorConfig, configAnalyzer, s2)
                    executorList.append(executor)
                    executorTaskIDs.append(executor.initExecutor.remote())
                ray.get(executorTaskIDs)

                taskIDs = [executor.execute.remote(date) for executor in executorList]
                ray.get(taskIDs)

                ray.shutdown()

    @staticmethod
    def __generateDataMangerRequirements(dataCollector):
        dataManagerRequirements = [
            # "StockSetAll": dataCollector.getStockSetAll(),
            # "IndexSet": dataCollector.getIndexSet(),
            dataCollector.getTickDataDict()[0],
            dataCollector.getTickDataDict()[1],
            dataCollector.getTickDataDict()[2],
            dataCollector.getTickDataDict()[3],
             dataCollector.getMinuteDataDict()[0],
             dataCollector.getMinuteDataDict()[1],
             dataCollector.getDailyDataDict()[0],
             dataCollector.getDailyDataDict()[1],
            # "AllTradingDayDict": dataCollector.getAllTradingDayDict(),
            # "InvalidTradingDayDict": dataCollector.getInvalidTradingDayDict(),
        ]
        # dataManagerRequirements = {
        #     "StockSetAll": ray.put(dataCollector.getStockSetAll()),
        #     "IndexSet": ray.put(dataCollector.getIndexSet()),
        #     "TickDataDict": ray.put(dataCollector.getTickDataDict()),
        #     "MinuteDataDict": ray.put(dataCollector.getMinuteDataDict()),
        #     "DailyDataDict": ray.put(dataCollector.getDailyDataDict()),
        #     "AllTradingDayDict": ray.put(dataCollector.getAllTradingDayDict()),
        #     "InvalidTradingDayDict": ray.put(dataCollector.getInvalidTradingDayDict()),
        # }
        return dataManagerRequirements

        tickDataDict = dataCollector.getTickDataDict()
        dataManagerRequirements["TickDataDict"] = [{}] * len(tickDataDict)
        for i in range(len(tickDataDict)):
            for k, v in tickDataDict[i].items():
                dataManagerRequirements["TickDataDict"][i][k] = ray.put(v)

        minuteDataDict = dataCollector.getMinuteDataDict()
        dataManagerRequirements["MinuteDataDict"] = [{}] * len(minuteDataDict)
        for i in range(len(minuteDataDict)):
            for k, v in minuteDataDict[i].items():
                dataManagerRequirements["MinuteDataDict"][i][k] = ray.put(v)

        dailyDataDict = dataCollector.getDailyDataDict()
        dataManagerRequirements["DailyDataDict"] = [{}] * len(dailyDataDict)
        for i in range(len(dailyDataDict)):
            for k, v in dailyDataDict[i].items():
                dataManagerRequirements["DailyDataDict"][i][k] = ray.put(v)

        return dataManagerRequirements
