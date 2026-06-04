import ray
import traceback
from SystemRay.DataManager import DataManager
from System.FactorManager import FactorManager


class Executor:
    def __init__(self, sDate, eDate, stockSetTS, factorLibrary, factorConfig, configAnalyzer, s2):
        self.__sDate = sDate
        self.__eDate = eDate
        self.__stockSetTS = stockSetTS
        self.__factorLibrary = factorLibrary
        self.__factorConfig = factorConfig
        self.__configAnalyzer = configAnalyzer
        # self.__dataManagerRequirements = dataManagerRequirements

        self.__dataManager = DataManager(self.__configAnalyzer)
        # self.__dataManager.setStockSetAll(dataManagerRequirements["StockSetAll"])
        # self.__dataManager.setIndexSet(dataManagerRequirements["IndexSet"])
        # self.__dataManager.setAllTradingDayDict(dataManagerRequirements["AllTradingDayDict"])
        # self.__dataManager.setInvalidTradingDayDict(dataManagerRequirements["InvalidTradingDayDict"])
        # self.__dataManager.setTickDataDict1(s1)
        self.__dataManager.setTickDataDict2(s2)
        # self.__dataManager.setTickDataDict3(s3)
        # self.__dataManager.setTickDataDict4(s4)
        # self.__dataManager.setMinuteDataDict1(s5)
        # self.__dataManager.setMinuteDataDict2(s6)
        # self.__dataManager.setDailyDataDict1(s7)
        # self.__dataManager.setDailyDataDict2(s8)
        # self.__dataManager.setTickDataDict1(dataManagerRequirements["TickDataDict1"])
        # self.__dataManager.setTickDataDict2(dataManagerRequirements["TickDataDict2"])
        # self.__dataManager.setTickDataDict3(dataManagerRequirements["TickDataDict3"])
        # self.__dataManager.setTickDataDict4(dataManagerRequirements["TickDataDict1"])
        # self.__dataManager.setMinuteDataDict1(dataManagerRequirements["MinuteDataDict1"])
        # self.__dataManager.setMinuteDataDict2(dataManagerRequirements["MinuteDataDict2"])
        # self.__dataManager.setDailyDataDict1(dataManagerRequirements["DailyDataDict1"])
        # self.__dataManager.setDailyDataDict2(dataManagerRequirements["DailyDataDict2"])
        # self.__dataManager.reshapeData()

        self.__factorManagerDict = None
        print("ssssssssssssssssssssssssssssss")

    def initExecutor(self):

        # tickDataDict = self.__dataManagerRequirements["TickDataDict"]
        # for i in range(len(tickDataDict)):
        #     for k, v in tickDataDict[i].items():
        #         self.__dataManagerRequirements["TickDataDict"][i][k] = ray.get(v)
        #
        # minuteDataDict = self.__dataManagerRequirements["MinuteDataDict"]
        # for i in range(len(minuteDataDict)):
        #     for k, v in minuteDataDict[i].items():
        #         self.__dataManagerRequirements["MinuteDataDict"][i][k] = ray.get(v)
        #
        # dailyDataDict = self.__dataManagerRequirements["DailyDataDict"]
        # for i in range(len(dailyDataDict)):
        #     for k, v in dailyDataDict[i].items():
        #         self.__dataManagerRequirements["DailyDataDict"][i][k] = ray.get(v)
        #
        # self.__dataManager.setTickDataDict(self.__dataManagerRequirements["TickDataDict"])
        # self.__dataManager.setMinuteDataDict(self.__dataManagerRequirements["MinuteDataDict"])
        # self.__dataManager.setDailyDataDict(self.__dataManagerRequirements["DailyDataDict"])


        self.__factorManagerDict = {}
        for stock in self.__stockSetTS:
            stockSetAllSingle = self.__configAnalyzer.getStockSetAll(stock, self.__sDate, self.__eDate)
            self.__factorManagerDict[stock] = FactorManager(stock, self.__factorConfig, self.__sDate, self.__eDate,
                                                            stockSetAllSingle, self.__factorLibrary, self.__dataManager)
            self.__factorManagerDict[stock].initFactors()

    def execute(self, date):
        for stock in self.__stockSetTS:
            try:
                self.__factorManagerDict[stock].calculateFactors(date)
            except:
                print(traceback.format_exc())
                print("ERROR: An unexpected error occurred when calculating factors for {} on {}"
                      .format(stock, date))
