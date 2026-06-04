from copy import deepcopy
from System.COLUMN_CONFIG import TRANSACTION_COLUMN_INDEX_DICT
from System.TradingDay import getNDaysOff


class Factor:
    def __init__(self, config, factorManager):
        self.__factorManager = factorManager
        self.__dataBroadcaster = self.__factorManager.getDataBroadcaster()
        self.__symbol = self.__factorManager.getStock()

        # Config
        self.__config = config
        self.__factorName = config["FactorName"]
        self.__historicalTickDataLength = config["TickLength"]
        self.__historicalMinuteDataLength = config["MinuteLength"]
        self.__historicalDailyDataLength = config["DailyLength"]
        self.__historicalTickDataLengthCS = config["TickLengthCS"]
        self.__historicalMinuteDataLengthCS = config["MinuteLengthCS"]
        self.__historicalDailyDataLengthCS = config["DailyLengthCS"]
        self.__historicalTickDataLengthIndex = config["TickLengthIndex"]
        self.__historicalMinuteDataLengthIndex = config["MinuteLengthIndex"]
        self.__historicalDailyDataLengthIndex = config["DailyLengthIndex"]
        self.__historicalTickDataLengthUA = config["TickLengthUA"]
        self.__historicalMinuteDataLengthUA = config["MinuteLengthUA"]
        self.__historicalDailyDataLengthUA = config["DailyLengthUA"]
        self.__dataType = config["DataType"]
        self.__dataTypeCS = config["DataTypeCS"]
        self.__dataTypeIndex = config["DataTypeIndex"]
        self.__dataTypeUA = config["DataTypeUA"]
        self.__stockGroup = config["StockGroup"]
        self.__indexGroup = config["IndexGroup"]
        self.__isSplitAdjusted = config["SplitAdjusted"]
        self.__parameters = config["Parameters"]

        self.__isTodayTickValid = "Tick" in self.__dataType
        self.__isTodayTickCSValid = "Tick" in self.__dataTypeCS
        self.__isTodayTickIndexValid = "Tick" in self.__dataTypeIndex
        self.__isTodayTickUAValid = "Tick" in self.__dataTypeUA
        self.__isTodayMinuteValid = "Minute" in self.__dataType
        self.__isTodayMinuteCSValid = "Minute" in self.__dataTypeCS
        self.__isTodayMinuteIndexValid = "Minute" in self.__dataTypeIndex
        self.__isTodayMinuteUAValid = "Minute" in self.__dataTypeUA

        self.__tickHistoricalStartDate = None
        self.__minuteHistoricalStartDate = None
        self.__dailyHistoricalStartDate = None
        self.__tickHistoricalStartDateCS = None
        self.__minuteHistoricalStartDateCS = None
        self.__dailyHistoricalStartDateCS = None
        self.__tickHistoricalStartDateIndex = None
        self.__minuteHistoricalStartDateIndex = None
        self.__dailyHistoricalStartDateIndex = None
        self.__tickHistoricalStartDateUA = None
        self.__minuteHistoricalStartDateUA = None
        self.__dailyHistoricalStartDateUA = None

        self.__stockList = None
        self.__industryCodeDict = {}
        self.__underlyingAsset = None

        # Intermediate & Factor Value
        self.__intermediateDictOriginal = {}
        self.__intermediateDict = None
        self.__factorValueList = None

    def _getFactor(self, config):
        """
        获取对应config文件的Factor或NonFactor
        :param config: dict
        :return: Factor
        """
        return self.__factorManager.getFactor(config)

    def _getConfig(self, configName):
        return self.__config.get(configName)

    def _getParameter(self, parameterName):
        """
        获取参数，若配置文件中不存在，则返回None
        :param parameterName: str
        :return: object
        """
        return self.__parameters.get(parameterName)

    # ################################################# Tick Data API ##################################################
    def _getAllTickData(self, field):
        """
        获取field字段的所有Tick数据
        若field为AskPrice、AskVolume、BidPrice、BidVolume或Transactions，则返回的np.ndarray中的元素为np.ndarray
        若field为其他值，则返回的np.ndarray中的元素为np.float64
        :param field: str
        :return: np.ndarray
        """
        if not self.__isTodayTickValid:
            raise Exception("No today's tick data for {}, please use historical API instead".format(self.__factorName))

        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDate, self.__symbol,
                                                       self.__isSplitAdjusted, mode=0)

    def _getLastTickData(self, field):
        """
        获取field字段的最近一个Tick数据
        若field为AskPrice、AskVolume、BidPrice、BidVolume或Transactions，则返回np.ndarray
        若field为其他值，则返回np.float64
        :param field: str
        :return: float or np.ndarray
        """
        if not self.__isTodayTickValid:
            raise Exception("No today's tick data for {}, please use historical API instead".format(self.__factorName))

        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDate, self.__symbol,
                                                       self.__isSplitAdjusted, mode=0, n=1)[0]

    def _getLastNTickData(self, field, n):
        """
        获取field字段的过去n个Tick数据
        若field为AskPrice、AskVolume、BidPrice、BidVolume或Transactions，则返回的np.ndarray中的元素为np.ndarray
        若field为其他值，则返回的np.ndarray中的元素为np.float64
        返回的np.ndarray的长度为min(n, field的数据长度)
        :param field: str
        :param n: int
        :return: np.ndarray
        """
        if not self.__isTodayTickValid:
            raise Exception("No today's tick data for {}, please use historical API instead".format(self.__factorName))

        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDate, self.__symbol,
                                                       self.__isSplitAdjusted, mode=0, n=n)

    def _getAllTickDataForStockGroup(self, field):
        """
        获取field字段的所有截面Tick数据，返回的np.ndarray的长度为数据长度最长的股票的长度
        若field为AskPrice、AskVolume、BidPrice、BidVolume或Transactions，则返回的np.ndarray中的元素为np.ndarray，
        数据长度不足n的以None填充
        若field为其他值，则返回的np.ndarray中的元素为np.float64，数据长度不足n的以np.nan填充
        :param field: str
        :return: np.ndarray
        """
        if not self.__isTodayTickCSValid:
            raise Exception("No today's cross sectional tick data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNTickDataForStockGroup(field, self.__tickHistoricalStartDateCS,
                                                                    self.__stockList, self.__isSplitAdjusted, mode=0)

    def _getLastTickDataForStockGroup(self, field):
        """
        获取field字段的最近一个截面Tick数据，返回的np.ndarray的长度为n
        若field为AskPrice、AskVolume、BidPrice、BidVolume或Transactions，则返回的np.ndarray中的元素为np.ndarray，
        数据长度不足n的以None填充
        若field为其他值，则返回的np.ndarray中的元素为np.float64，数据长度不足n的以np.nan填充
        :param field: str
        :return: np.ndarray
        """
        if not self.__isTodayTickCSValid:
            raise Exception("No today's cross sectional tick data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNTickDataForStockGroup(field, self.__tickHistoricalStartDateCS,
                                                                    self.__stockList, self.__isSplitAdjusted, mode=0,
                                                                    n=1)

    def _getLastNTickDataForStockGroup(self, field, n):
        """
        获取field字段的过去n个截面Tick数据，返回的np.ndarray的长度为n
        若field为AskPrice、AskVolume、BidPrice、BidVolume或Transactions，则返回的np.ndarray中的元素为np.ndarray，
        数据长度不足n的以None填充
        若field为其他值，则返回的np.ndarray中的元素为np.float64，数据长度不足n的以np.nan填充
        :param field: str
        :param n: int
        :return: np.ndarray
        """
        if not self.__isTodayTickCSValid:
            raise Exception("No today's cross sectional tick data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNTickDataForStockGroup(field, self.__tickHistoricalStartDateCS,
                                                                    self.__stockList, self.__isSplitAdjusted, mode=0,
                                                                    n=n)

    def _getAllTodayTickData(self, field):
        """
        获取field字段的所有当日Tick数据
        :param field: str
        :return: np.ndarray
        """
        if not self.__isTodayTickValid:
            raise Exception("No today's tick data for {}, please use historical API instead".format(self.__factorName))

        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDate, self.__symbol,
                                                       self.__isSplitAdjusted, mode=1)

    def _getLastNTodayTickData(self, field, n):
        """
        获取field字段的当日过去n个Tick数据，返回的np.ndarray的长度为min(n, field的当日数据长度)
        :param field: str
        :param n: int
        :return: np.ndarray
        """
        if not self.__isTodayTickValid:
            raise Exception("No today's tick data for {}, please use historical API instead".format(self.__factorName))

        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDate, self.__symbol,
                                                       self.__isSplitAdjusted, mode=1, n=n)

    def _getAllTodayTickDataForStockGroup(self, field):
        """
        获取field字段的所有当日截面Tick数据，返回的np.ndarray的长度为数据长度最长的股票的长度
        若field为AskPrice、AskVolume、BidPrice、BidVolume或Transactions，则返回的np.ndarray中的元素为np.ndarray，
        数据长度不足的以None填充
        若field为其他值，则返回的np.ndarray中的元素为np.float64，数据长度不足的以np.nan填充
        :param field: str
        :return: np.ndarray
        """
        if not self.__isTodayTickCSValid:
            raise Exception("No today's cross sectional tick data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNTickDataForStockGroup(field, self.__tickHistoricalStartDateCS,
                                                                    self.__stockList, self.__isSplitAdjusted, mode=1)

    def _getLastNTodayTickDataForStockGroup(self, field, n):
        """
        获取field字段的当日过去n个截面Tick数据，返回的np.ndarray的长度为n
        若field为AskPrice、AskVolume、BidPrice、BidVolume或Transactions，则返回的np.ndarray中的元素为np.ndarray，
        数据长度不足n的以None填充
        若field为其他值，则返回的np.ndarray中的元素为np.float64，数据长度不足n的以np.nan填充
        :param field: str
        :param n: int
        :return: np.ndarray
        """
        if not self.__isTodayTickCSValid:
            raise Exception("No today's cross sectional tick data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNTickDataForStockGroup(field, self.__tickHistoricalStartDateCS,
                                                                    self.__stockList, self.__isSplitAdjusted, mode=1,
                                                                    n=n)

    def _getAllHistoricalTickData(self, field):
        """
        获取field字段的所有历史Tick数据
        :param field: str
        :return: np.ndarray
        """
        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDate, self.__symbol,
                                                       self.__isSplitAdjusted, mode=2)

    def _getLastNHistoricalTickData(self, field, n):
        """
        获取field字段的历史过去n个Tick数据
        :param field: str
        :param n: int
        :return: np.ndarray
        """
        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDate, self.__symbol,
                                                       self.__isSplitAdjusted, mode=2, n=n)

    def _getAllHistoricalTickDataForStockGroup(self, field):
        """
        获取field字段的所有历史截面Tick数据
        :param field: str
        :return: np.ndarray
        """
        return self.__dataBroadcaster.getLastNTickDataForStockGroup(field, self.__tickHistoricalStartDateCS,
                                                                    self.__stockList, self.__isSplitAdjusted, mode=2)

    def _getLastNHistoricalTickDataForStockGroup(self, field, n):
        """
        获取field字段的历史过去n个截面Tick数据
        :param field: str
        :param n: int
        :return: np.ndarray
        """
        return self.__dataBroadcaster.getLastNTickDataForStockGroup(field, self.__tickHistoricalStartDateCS,
                                                                    self.__stockList, self.__isSplitAdjusted, mode=2,
                                                                    n=n)

    def _getAllTickDataUA(self, field):
        if not self.__isTodayTickUAValid:
            raise Exception("No today's tick data for {}, please use historical API instead".format(self.__factorName))

        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDateUA, self.__underlyingAsset,
                                                       self.__isSplitAdjusted, mode=0)

    def _getLastTickDataUA(self, field):
        if not self.__isTodayTickUAValid:
            raise Exception("No today's tick data for {}, please use historical API instead".format(self.__factorName))

        data = self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDateUA, self.__underlyingAsset,
                                                       self.__isSplitAdjusted, mode=0, n=1)
        if data.shape[0] == 0:
            return data
        else:
            return data[0]

    def _getLastNTickDataUA(self, field, n):
        if not self.__isTodayTickUAValid:
            raise Exception("No today's tick data for {}, please use historical API instead".format(self.__factorName))

        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDateUA, self.__underlyingAsset,
                                                       self.__isSplitAdjusted, mode=0, n=n)

    def _getAllTodayTickDataUA(self, field):
        if not self.__isTodayTickUAValid:
            raise Exception("No today's tick data for {}, please use historical API instead".format(self.__factorName))

        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDateUA, self.__underlyingAsset,
                                                       self.__isSplitAdjusted, mode=1)

    def _getLastNTodayTickDataUA(self, field, n):
        if not self.__isTodayTickUAValid:
            raise Exception("No today's tick data for {}, please use historical API instead".format(self.__factorName))

        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDateUA, self.__underlyingAsset,
                                                       self.__isSplitAdjusted, mode=1, n=n)

    def _getAllHistoricalTickDataUA(self, field):
        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDateUA, self.__underlyingAsset,
                                                       self.__isSplitAdjusted, mode=2)

    def _getLastNHistoricalTickDataUA(self, field, n):
        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDateUA, self.__underlyingAsset,
                                                       self.__isSplitAdjusted, mode=2, n=n)

    @staticmethod
    def _getTransactionData(field, transactionArray):
        """
        根据field从transactionArray中获取该列
        :param field: str
        :param transactionArray: np.ndarray
        :return: np.ndarray
        """
        return transactionArray[:, TRANSACTION_COLUMN_INDEX_DICT[field]]

    # ################################################ Minute Data API #################################################
    def _getAllMinuteData(self, field):
        if not self.__isTodayMinuteValid:
            raise Exception("No today's minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDate, self.__symbol,
                                                         self.__isSplitAdjusted, mode=0)

    def _getLastMinuteData(self, field):
        if not self.__isTodayMinuteValid:
            raise Exception("No today's minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        data = self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDate, self.__symbol,
                                                         self.__isSplitAdjusted, mode=0, n=1)
        if data.shape[0] == 0:
            return data
        else:
            return data[0]

    def _getLastNMinuteData(self, field, n):
        if not self.__isTodayMinuteValid:
            raise Exception("No today's minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDate, self.__symbol,
                                                         self.__isSplitAdjusted, mode=0, n=n)

    def _getAllMinuteDataForStockGroup(self, field):
        if not self.__isTodayMinuteCSValid:
            raise Exception("No today's cross sectional minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNMinuteDataForStockGroup(field, self.__minuteHistoricalStartDateCS,
                                                                      self.__stockList, self.__isSplitAdjusted, mode=0)

    def _getLastMinuteDataForStockGroup(self, field):
        if not self.__isTodayMinuteCSValid:
            raise Exception("No today's cross sectional minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNMinuteDataForStockGroup(field, self.__minuteHistoricalStartDateCS,
                                                                      self.__stockList, self.__isSplitAdjusted, mode=0,
                                                                      n=1)

    def _getLastNMinuteDataForStockGroup(self, field, n):
        if not self.__isTodayMinuteCSValid:
            raise Exception("No today's cross sectional minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNMinuteDataForStockGroup(field, self.__minuteHistoricalStartDateCS,
                                                                      self.__stockList, self.__isSplitAdjusted, mode=0,
                                                                      n=n)

    def _getAllTodayMinuteData(self, field):
        if not self.__isTodayMinuteValid:
            raise Exception("No today's minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDate, self.__symbol,
                                                         self.__isSplitAdjusted, mode=1)

    def _getLastNTodayMinuteData(self, field, n):
        if not self.__isTodayMinuteValid:
            raise Exception("No today's minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDate, self.__symbol,
                                                         self.__isSplitAdjusted, mode=1, n=n)

    def _getAllTodayMinuteDataForStockGroup(self, field):
        if not self.__isTodayMinuteCSValid:
            raise Exception("No today's cross sectional minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNMinuteDataForStockGroup(field, self.__minuteHistoricalStartDateCS,
                                                                      self.__stockList, self.__isSplitAdjusted, mode=1)

    def _getLastNTodayMinuteDataForStockGroup(self, field, n):
        if not self.__isTodayMinuteCSValid:
            raise Exception("No today's cross sectional minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNMinuteDataForStockGroup(field, self.__minuteHistoricalStartDateCS,
                                                                      self.__stockList, self.__isSplitAdjusted, mode=1,
                                                                      n=n)

    def _getAllHistoricalMinuteData(self, field):
        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDate, self.__symbol,
                                                         self.__isSplitAdjusted, mode=2)

    def _getLastNHistoricalMinuteData(self, field, n):
        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDate, self.__symbol,
                                                         self.__isSplitAdjusted, mode=2, n=n)

    def _getAllHistoricalMinuteDataForStockGroup(self, field):
        return self.__dataBroadcaster.getLastNMinuteDataForStockGroup(field, self.__minuteHistoricalStartDateCS,
                                                                      self.__stockList, self.__isSplitAdjusted, mode=2)

    def _getLastNHistoricalMinuteDataForStockGroup(self, field, n):
        return self.__dataBroadcaster.getLastNMinuteDataForStockGroup(field, self.__minuteHistoricalStartDateCS,
                                                                      self.__stockList, self.__isSplitAdjusted, mode=2,
                                                                      n=n)

    def _getAllMinuteDataUA(self, field):
        if not self.__isTodayMinuteUAValid:
            raise Exception("No today's minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDateUA,
                                                         self.__underlyingAsset, self.__isSplitAdjusted, mode=0)

    def _getLastMinuteDataUA(self, field):
        if not self.__isTodayMinuteUAValid:
            raise Exception("No today's minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        data = self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDateUA,
                                                         self.__underlyingAsset, self.__isSplitAdjusted, mode=0, n=1)
        if data.shape[0] == 0:
            return data
        else:
            return data[0]

    def _getLastNMinuteDataUA(self, field, n):
        if not self.__isTodayMinuteUAValid:
            raise Exception("No today's minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDateUA,
                                                         self.__underlyingAsset, self.__isSplitAdjusted, mode=0, n=n)

    def _getAllTodayMinuteDataUA(self, field):
        if not self.__isTodayMinuteUAValid:
            raise Exception("No today's minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDateUA,
                                                         self.__underlyingAsset, self.__isSplitAdjusted, mode=1)

    def _getLastNTodayMinuteDataUA(self, field, n):
        if not self.__isTodayMinuteUAValid:
            raise Exception("No today's minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDateUA,
                                                         self.__underlyingAsset, self.__isSplitAdjusted, mode=1, n=n)

    def _getAllHistoricalMinuteDataUA(self, field):
        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDateUA,
                                                         self.__underlyingAsset, self.__isSplitAdjusted, mode=2)

    def _getLastNHistoricalMinuteDataUA(self, field, n):
        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDateUA,
                                                         self.__underlyingAsset, self.__isSplitAdjusted, mode=2, n=n)

    # ################################################# Daily Data API #################################################
    def _getAllHistoricalDailyData(self, field):
        return self.__dataBroadcaster.getLastNHistoricalDailyData(field, self.__dailyHistoricalStartDate, self.__symbol,
                                                                  self.__isSplitAdjusted)

    def _getLastNHistoricalDailyData(self, field, n):
        return self.__dataBroadcaster.getLastNHistoricalDailyData(field, self.__dailyHistoricalStartDate, self.__symbol,
                                                                  self.__isSplitAdjusted, n)

    def _getAllHistoricalDailyDataForStockGroup(self, field):
        return self.__dataBroadcaster.getLastNHistoricalDailyDataForStockGroup(field, self.__dailyHistoricalStartDateCS,
                                                                               self.__stockList, self.__isSplitAdjusted)

    def _getLastNHistoricalDailyDataForStockGroup(self, field, n):
        return self.__dataBroadcaster.getLastNHistoricalDailyDataForStockGroup(field, self.__dailyHistoricalStartDateCS,
                                                                               self.__stockList, self.__isSplitAdjusted,
                                                                               n)

    def _getAllHistoricalDailyDataUA(self, field):
        return self.__dataBroadcaster.getLastNHistoricalDailyData(field, self.__dailyHistoricalStartDateUA,
                                                                  self.__underlyingAsset, self.__isSplitAdjusted)

    def _getLastNHistoricalDailyDataUA(self, field, n):
        return self.__dataBroadcaster.getLastNHistoricalDailyData(field, self.__dailyHistoricalStartDateUA,
                                                                  self.__underlyingAsset, self.__isSplitAdjusted, n)

    # ################################################### Index API ####################################################
    def _getAllIndexTickData(self, indexName, field):
        if not self.__isTodayTickIndexValid:
            raise Exception("No today's index tick data for {}, please use historical API instead"
                            .format(self.__factorName))

        indexName = self.__industryCodeDict.get(indexName, indexName)
        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDateIndex, indexName, False,
                                                       mode=0)

    def _getLastIndexTickData(self, indexName, field):
        if not self.__isTodayTickIndexValid:
            raise Exception("No today's index tick data for {}, please use historical API instead"
                            .format(self.__factorName))

        indexName = self.__industryCodeDict.get(indexName, indexName)
        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDateIndex, indexName, False,
                                                       mode=0, n=1)[0]

    def _getLastNIndexTickData(self, indexName, field, n):
        if not self.__isTodayTickIndexValid:
            raise Exception("No today's index tick data for {}, please use historical API instead"
                            .format(self.__factorName))

        indexName = self.__industryCodeDict.get(indexName, indexName)
        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDateIndex, indexName, False,
                                                       mode=0, n=n)

    def _getAllTodayIndexTickData(self, indexName, field):
        if not self.__isTodayTickIndexValid:
            raise Exception("No today's index tick data for {}, please use historical API instead"
                            .format(self.__factorName))

        indexName = self.__industryCodeDict.get(indexName, indexName)
        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDateIndex, indexName, False,
                                                       mode=1)

    def _getLastNTodayIndexTickData(self, indexName, field, n):
        if not self.__isTodayTickIndexValid:
            raise Exception("No today's index tick data for {}, please use historical API instead"
                            .format(self.__factorName))

        indexName = self.__industryCodeDict.get(indexName, indexName)
        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDateIndex, indexName, False,
                                                       mode=1, n=n)

    def _getAllHistoricalIndexTickData(self, indexName, field):
        indexName = self.__industryCodeDict.get(indexName, indexName)
        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDateIndex, indexName, False,
                                                       mode=2)

    def _getLastNHistoricalIndexTickData(self, indexName, field, n):
        indexName = self.__industryCodeDict.get(indexName, indexName)
        return self.__dataBroadcaster.getLastNTickData(field, self.__tickHistoricalStartDateIndex, indexName, False,
                                                       mode=2, n=n)

    def _getAllIndexMinuteData(self, indexName, field):
        if not self.__isTodayMinuteIndexValid:
            raise Exception("No today's index minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        indexName = self.__industryCodeDict.get(indexName, indexName)
        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDateIndex, indexName, False,
                                                         mode=0)

    def _getLastIndexMinuteData(self, indexName, field):
        if not self.__isTodayMinuteIndexValid:
            raise Exception("No today's index minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        indexName = self.__industryCodeDict.get(indexName, indexName)
        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDateIndex, indexName, False,
                                                         mode=0, n=1)[0]

    def _getLastNIndexMinuteData(self, indexName, field, n):
        if not self.__isTodayMinuteIndexValid:
            raise Exception("No today's index minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        indexName = self.__industryCodeDict.get(indexName, indexName)
        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDateIndex, indexName, False,
                                                         mode=0, n=n)

    def _getAllTodayIndexMinuteData(self, indexName, field):
        if not self.__isTodayMinuteIndexValid:
            raise Exception("No today's index minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        indexName = self.__industryCodeDict.get(indexName, indexName)
        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDateIndex, indexName, False,
                                                         mode=1)

    def _getLastNTodayIndexMinuteData(self, indexName, field, n):
        if not self.__isTodayMinuteIndexValid:
            raise Exception("No today's index minute data for {}, please use historical API instead"
                            .format(self.__factorName))

        indexName = self.__industryCodeDict.get(indexName, indexName)
        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDateIndex, indexName, False,
                                                         mode=1, n=n)

    def _getAllHistoricalIndexMinuteData(self, indexName, field):
        indexName = self.__industryCodeDict.get(indexName, indexName)
        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDateIndex, indexName, False,
                                                         mode=2)

    def _getLastNHistoricalIndexMinuteData(self, indexName, field, n):
        indexName = self.__industryCodeDict.get(indexName, indexName)
        return self.__dataBroadcaster.getLastNMinuteData(field, self.__minuteHistoricalStartDateIndex, indexName, False,
                                                         mode=2, n=n)

    def _getAllHistoricalIndexDailyData(self, indexName, field):
        indexName = self.__industryCodeDict.get(indexName, indexName)
        return self.__dataBroadcaster.getLastNHistoricalDailyData(field, self.__dailyHistoricalStartDateIndex,
                                                                  indexName, False)

    def _getLastNHistoricalIndexDailyData(self, indexName, field, n):
        indexName = self.__industryCodeDict.get(indexName, indexName)
        return self.__dataBroadcaster.getLastNHistoricalDailyData(field, self.__dailyHistoricalStartDateIndex,
                                                                  indexName, False, n)

    # ################################################## General API ###################################################
    def _addIntermediate(self, intermediateName, intermediateValue):
        self.__intermediateDictOriginal[intermediateName] = intermediateValue

    def _setIntermediate(self, intermediateName, intermediateValue):
        self.__intermediateDict[intermediateName] = intermediateValue

    def _addFactorValue(self, factorValue):
        """
        存储因子值
        :param factorValue: float
        """
        self.__factorValueList.append(factorValue)

    def _onDayEnd(self):
        pass

    def getIntermediate(self, intermediateName):
        return self.__intermediateDict.get(intermediateName)

    def getLastFactorValue(self):
        """
        获取最近一个已经计算的因子值，若没有因子值，则返回None
        :return: object
        """
        if len(self.__factorValueList) == 0:
            return None
        else:
            return self.__factorValueList[-1]

    def getFactorValueList(self):
        """
        获取已经计算的因子值列表
        :return: list
        """
        return self.__factorValueList

    def calculate(self):
        """
        因子计算逻辑
        """
        pass

    def register(self):
        self.__factorManager.registerFactor(self.__config, self)

    def onNewDay(self, date):
        self.__intermediateDict = deepcopy(self.__intermediateDictOriginal)
        self.__factorValueList = []

        self.__tickHistoricalStartDate = getNDaysOff(date, self.__historicalTickDataLength)
        self.__minuteHistoricalStartDate = getNDaysOff(date, self.__historicalMinuteDataLength)
        self.__dailyHistoricalStartDate = getNDaysOff(date, self.__historicalDailyDataLength)
        self.__tickHistoricalStartDateCS = getNDaysOff(date, self.__historicalTickDataLengthCS)
        self.__minuteHistoricalStartDateCS = getNDaysOff(date, self.__historicalMinuteDataLengthCS)
        self.__dailyHistoricalStartDateCS = getNDaysOff(date, self.__historicalDailyDataLengthCS)
        self.__tickHistoricalStartDateIndex = getNDaysOff(date, self.__historicalTickDataLengthIndex)
        self.__minuteHistoricalStartDateIndex = getNDaysOff(date, self.__historicalMinuteDataLengthIndex)
        self.__dailyHistoricalStartDateIndex = getNDaysOff(date, self.__historicalDailyDataLengthIndex)
        self.__tickHistoricalStartDateUA = getNDaysOff(date, self.__historicalTickDataLengthUA)
        self.__minuteHistoricalStartDateUA = getNDaysOff(date, self.__historicalMinuteDataLengthUA)
        self.__dailyHistoricalStartDateUA = getNDaysOff(date, self.__historicalDailyDataLengthUA)

        if isinstance(self.__stockGroup, dict):
            self.__stockList = deepcopy(self.__stockGroup[self.__symbol])
            if self.__symbol in self.__stockList:
                self.__stockList.remove(self.__symbol)
        elif self.__stockGroup == "Self":
            self.__stockList = []
        else:
            self.__stockList = self.__factorManager.getStockList(date, self.__stockGroup)

        for indexGroup in self.__indexGroup:
            industryCode = self.__factorManager.getIndustryCode(date, indexGroup)
            if industryCode is not None:
                self.__industryCodeDict[indexGroup] = industryCode

        self.__underlyingAsset = self.__factorManager.getUnderlyingAsset(date)

    def onDayEnd(self):
        self._onDayEnd()

        if self.__factorName.startswith("factor") or self.__factorName.startswith("tag"):
            return self.__factorName, self.__factorValueList
        else:
            return None, None
