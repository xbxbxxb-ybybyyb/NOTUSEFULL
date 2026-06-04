from copy import deepcopy
from Constants.INDEX_LIST import INDEX_LIST
from Constants.FUND_LIST import STOCK_ETF_INDEX_MAP
from Constants.FUTURE_LIST import INDEX_FUTURE_INDEX_MAP
from System.TradingDay import getTradingDay, getNDaysOff
from FactorDataTool.FDTool import FDTool


class ConfigAnalyzer:
    def __init__(self, mdLibrary, assetType, underlyingAssetType, factorConfig):
        self.__mdLibrary = mdLibrary
        self.__assetType = assetType
        self.__underlyingAssetType = underlyingAssetType
        self.__factorConfig = deepcopy(factorConfig)

        self.__maxTickLength = 0
        self.__maxMinuteLength = 0
        self.__maxDailyLength = 0
        self.__maxTickLengthCS = 0
        self.__maxMinuteLengthCS = 0
        self.__maxDailyLengthCS = 0
        self.__maxTickLengthIndex = 0
        self.__maxMinuteLengthIndex = 0
        self.__maxDailyLengthIndex = 0
        self.__maxTickLengthUA = 0
        self.__maxMinuteLengthUA = 0
        self.__maxDailyLengthUA = 0
        self.__maxTickLengthINF = 0
        self.__maxMinuteLengthINF = 0
        self.__maxDailyLengthINF = 0
        self.__dataType = set()
        self.__dataTypeCS = set()
        self.__dataTypeIndex = set()
        self.__dataTypeUA = set()
        self.__dataTypeINF = set()
        self.__isSplitAdjustedNeeded = False
        self.__isUseUnderlyingAsset = False

        self.__completeStockDict = {}
        self.__indexDict = {}
        self.__industryDict = {}
        self.__industryStockDict = {}
        self.__indexGroup = set()
        self.__infGroup = {}
        self.__userDefinedStockGroup = []
        self.__usedStockGroup = set()
        self.__underlyingAssetDict = {}

        self.__fdtool = None
        self.__completeStockList = None

    def analyzeConfig(self, sDate, eDate):
        for config in self.__factorConfig:
            self.__updateDataLength(config)  # 历史数据长度 & 复权 & 关联标的
            self.__updateDataType(config)  # 时序数据类型
            self.__loadFDTool(config, eDate)  # 根据需要加载FDTool

        tradingDayList = getTradingDay(getNDaysOff(sDate, 1), getNDaysOff(eDate, 1))
        tradingDayListINF = getTradingDay(getNDaysOff(sDate, self.__maxTickLengthINF + 1), getNDaysOff(eDate, 1))
        for config in self.__factorConfig:
            self.__updateINFGroup(config, tradingDayListINF)  # 根据需要加载股票列表 需最先加载INF
            self.__updateStockGroup(config, tradingDayList)  # 根据需要加载股票列表
            self.__updateIndexGroup(config, tradingDayList)  # 根据需要加载股票列表
            self.__updateUnderlyingAsset(tradingDayList)  # 根据标的类型加载映射关系

    def __updateDataLength(self, config):
        self.__maxTickLength = max(self.__maxTickLength, config.get("TickLength", 0))
        self.__maxMinuteLength = max(self.__maxMinuteLength, config.get("MinuteLength", 0))
        self.__maxDailyLength = max(self.__maxDailyLength, config.get("DailyLength", 0))
        self.__maxTickLengthCS = max(self.__maxTickLengthCS, config.get("TickLengthCS", 0))
        self.__maxMinuteLengthCS = max(self.__maxMinuteLengthCS, config.get("MinuteLengthCS", 0))
        self.__maxDailyLengthCS = max(self.__maxDailyLengthCS, config.get("DailyLengthCS", 0))
        self.__maxTickLengthIndex = max(self.__maxTickLengthIndex, config.get("TickLengthIndex", 0))
        self.__maxMinuteLengthIndex = max(self.__maxMinuteLengthIndex, config.get("MinuteLengthIndex", 0))
        self.__maxDailyLengthIndex = max(self.__maxDailyLengthIndex, config.get("DailyLengthIndex", 0))
        self.__maxTickLengthUA = max(self.__maxTickLengthUA, config.get("TickLengthUA", 0))
        self.__maxMinuteLengthUA = max(self.__maxMinuteLengthUA, config.get("MinuteLengthUA", 0))
        self.__maxDailyLengthUA = max(self.__maxDailyLengthUA, config.get("DailyLengthUA", 0))
        self.__maxTickLengthINF = max(self.__maxTickLengthINF, config.get("TickLengthINF", 0))
        self.__maxMinuteLengthINF = max(self.__maxMinuteLengthINF, config.get("MinuteLengthINF", 0))
        self.__maxDailyLengthINF = max(self.__maxDailyLengthINF, config.get("DailyLengthINF", 0))
        self.__isSplitAdjustedNeeded = self.__isSplitAdjustedNeeded or config.get("SplitAdjusted", False)
        self.__isUseUnderlyingAsset = self.__isUseUnderlyingAsset or config.get("UnderlyingAsset", False)

    def __updateDataType(self, config):
        dataTypeMap = {"Both": ["Tick", "Minute"], "Tick": ["Tick"], "Minute": ["Minute"]}

        dataType = config.get("DataType", config.get("BType", "Tick"))
        self.__dataType = self.__dataType.union(dataTypeMap[dataType])

        if config.get("StockGroup") is not None:
            dataTypeCS = config.get("DataTypeCS", "Minute")
            self.__dataTypeCS = self.__dataTypeCS.union(dataTypeMap[dataTypeCS])

        if config.get("IndexGroup") is not None:
            dataTypeIndex = config.get("DataTypeIndex", "Minute")
            self.__dataTypeIndex = self.__dataTypeIndex.union(dataTypeMap[dataTypeIndex])

        if self.__isUseUnderlyingAsset:
            dataTypeUA = config.get("DataTypeUA", "Tick")
            self.__dataTypeUA = self.__dataTypeUA.union(dataTypeMap[dataTypeUA])

        if config.get("INFGroup") is not None:
            dataTypeINF = config.get("DataTypeINF", "Tick")
            self.__dataTypeINF = self.__dataTypeINF.union(dataTypeMap[dataTypeINF])

    def __loadFDTool(self, config, date):
        stockGroup = config.get("StockGroup")
        indexGroupList = config.get("IndexGroup")
        infGroupDict = config.get("INFGroup")

        if (stockGroup is None
                and indexGroupList is None
                and not self.__isUseUnderlyingAsset
                and infGroupDict is None):
            return

        if self.__fdtool is None:
            self.__fdtool = FDTool(self.__mdLibrary)
            self.__completeStockList = self.__fdtool.hset("MARKET", getNDaysOff(date, 1), "ALLA_HIS")

    def __updateStockGroup(self, config, tradingDayList):
        group = config.get("StockGroup")

        if group is None:
            return

        if isinstance(group, dict):  # key: 标的名 value: 截面标的名列表
            self.__userDefinedStockGroup.append(group)
            return

        if group in self.__usedStockGroup:  # 避免重复加载数据
            return

        if group == "ALLA":  # 全市场股票列表
            for date in tradingDayList:
                self.__completeStockDict[date] = self.__fdtool.hset("MARKET", date, "ALLA")
        elif group in ["SZ50", "HS300", "ZZ500"]:  # 宽基指数成分股列表
            self.__indexDict[group] = {}
            for date in tradingDayList:
                self.__indexDict[group][date] = self.__fdtool.hset("INDEX", date, group)
        else:  # 行业指数成分股列表
            self.__industryDict[group] = {}
            self.__industryStockDict[group] = {}
            for date in tradingDayList:
                industryDF = self.__fdtool.hsi(self.__completeStockList, date, group[:-1], int(group[-1]))
                industryDF = industryDF.dropna()
                self.__industryDict[group][date] = industryDF.set_index("Stock")["IndustryCode"].to_dict()
                self.__industryStockDict[group][date] = {}
                for industryCode, stockSeries in industryDF.groupby("IndustryCode")["Stock"]:
                    self.__industryStockDict[group][date][industryCode] = stockSeries.tolist()

        self.__usedStockGroup.add(group)

    def __updateIndexGroup(self, config, tradingDayList):
        indexGroupList = config.get("IndexGroup")

        if indexGroupList is None:
            return

        self.__indexGroup = self.__indexGroup.union(indexGroupList)

        for indexGroup in indexGroupList:
            if indexGroup in self.__usedStockGroup or indexGroup in INDEX_LIST:
                continue

            self.__industryDict[indexGroup] = {}
            self.__industryStockDict[indexGroup] = {}
            for date in tradingDayList:
                industryDF = self.__fdtool.hsi(self.__completeStockList, date, indexGroup[:-1], int(indexGroup[-1]))
                industryDF = industryDF.dropna()
                self.__industryDict[indexGroup][date] = industryDF.set_index("Stock")["IndustryCode"].to_dict()
                self.__industryStockDict[indexGroup][date] = {}
                for industryCode, stockSeries in industryDF.groupby("IndustryCode")["Stock"]:
                    self.__industryStockDict[indexGroup][date][industryCode] = stockSeries.tolist()

            self.__usedStockGroup.add(indexGroup)

    def __updateUnderlyingAsset(self, tradingDayList):
        if not self.__isUseUnderlyingAsset or self.__underlyingAssetDict:
            return

        for date in tradingDayList:
            if self.__assetType == "CB":
                cbMap = self.__fdtool.cbs_map(getNDaysOff(date, -1))
                cbMap = cbMap.dropna()
                self.__underlyingAssetDict[date] = cbMap.set_index("CBond")["Stock"].to_dict()
            elif self.__assetType == "ETF":
                self.__underlyingAssetDict[date] = STOCK_ETF_INDEX_MAP
            elif self.__assetType == "Future":
                self.__underlyingAssetDict[date] = INDEX_FUTURE_INDEX_MAP

    def __updateINFGroup(self, config, tradingDayListINF):
        infGroupDict = config.get("INFGroup")

        if infGroupDict is None:
            return

        for k, v in infGroupDict.items():
            if k not in self.__infGroup:
                self.__infGroup[k] = set()
            self.__infGroup[k] = self.__infGroup[k].union(v)

        for infGroup in infGroupDict:
            if infGroup in self.__usedStockGroup or infGroup in INDEX_LIST:
                continue

            self.__industryDict[infGroup] = {}
            self.__industryStockDict[infGroup] = {}
            for date in tradingDayListINF:
                industryDF = self.__fdtool.hsi(self.__completeStockList, date, infGroup[:-1], int(infGroup[-1]))
                industryDF = industryDF.dropna()
                self.__industryDict[infGroup][date] = industryDF.set_index("Stock")["IndustryCode"].to_dict()
                self.__industryStockDict[infGroup][date] = {}
                for industryCode, stockSeries in industryDF.groupby("IndustryCode")["Stock"]:
                    self.__industryStockDict[infGroup][date][industryCode] = stockSeries.tolist()

            self.__usedStockGroup.add(infGroup)

    def getDataRequirements(self):
        return {
            "maxTickLength": self.__maxTickLength,
            "maxMinuteLength": self.__maxMinuteLength,
            "maxDailyLength": self.__maxDailyLength,
            "maxTickLengthCS": self.__maxTickLengthCS,
            "maxMinuteLengthCS": self.__maxMinuteLengthCS,
            "maxDailyLengthCS": self.__maxDailyLengthCS,
            "maxTickLengthIndex": self.__maxTickLengthIndex,
            "maxMinuteLengthIndex": self.__maxMinuteLengthIndex,
            "maxDailyLengthIndex": self.__maxDailyLengthIndex,
            "maxTickLengthUA": self.__maxTickLengthUA,
            "maxMinuteLengthUA": self.__maxMinuteLengthUA,
            "maxDailyLengthUA": self.__maxDailyLengthUA,
            "maxTickLengthINF": self.__maxTickLengthINF,
            "maxMinuteLengthINF": self.__maxMinuteLengthINF,
            "maxDailyLengthINF": self.__maxDailyLengthINF,
            "dataType": self.__dataType,
            "dataTypeCS": self.__dataTypeCS,
            "dataTypeIndex": self.__dataTypeIndex,
            "dataTypeUA": self.__dataTypeUA,
            "dataTypeINF": self.__dataTypeINF,
            "indexGroup": self.__indexGroup,
            "infGroup": self.__infGroup,
            "splitAdjustedNeeded": self.__isSplitAdjustedNeeded,
            "isUseUnderlyingAsset": self.__isUseUnderlyingAsset,
        }

    def getStockSetAll(self, stock, sDate, eDate):
        stockSetAll = {stock}
        tradingDayList = getTradingDay(getNDaysOff(sDate, 1), getNDaysOff(eDate, 1))

        for stockGroupDict in self.__userDefinedStockGroup:
            stockSetAll = stockSetAll.union(stockGroupDict[stock])

        for group in self.__usedStockGroup:
            if group == "ALLA":
                for date in tradingDayList:
                    stockSetAll = stockSetAll.union(self.__completeStockDict[date])
            elif group in ["SZ50", "HS300", "ZZ500"]:
                for date in tradingDayList:
                    stockSetAll = stockSetAll.union(self.__indexDict[group][date])
            else:
                if self.__assetType == "INF":
                    for date in tradingDayList:
                        stockSetAll = stockSetAll.union(self.__industryStockDict[group][date].get(stock, []))
                else:
                    for date in tradingDayList:
                        targetIndustry = self.__industryDict[group][date].get(stock)
                        if targetIndustry is not None:
                            stockSetAll = stockSetAll.union(self.__industryStockDict[group][date][targetIndustry])

        return stockSetAll

    def getIndustryCode(self, stock, date, stockGroup):
        if stockGroup in INDEX_LIST:
            return None

        date = getNDaysOff(date, 1)
        return self.__industryDict[stockGroup][date].get(stock)

    def getStockList(self, stock, date, stockGroup):
        date = getNDaysOff(date, 1)
        if stockGroup == "ALLA":
            stockList = deepcopy(self.__completeStockDict[date])
            stockList.remove(stock)
        elif stockGroup in ["SZ50", "HS300", "ZZ500"]:
            stockList = deepcopy(self.__indexDict[stockGroup][date])
            if stock in stockList:
                stockList.remove(stock)
        else:
            if self.__assetType == "INF":
                stockList = deepcopy(self.__industryStockDict[stockGroup][date][stock])
            else:
                targetIndustry = self.__industryDict[stockGroup][date][stock]
                stockList = deepcopy(self.__industryStockDict[stockGroup][date][targetIndustry])
                stockList.remove(stock)

        return stockList

    def getUnderlyingAsset(self, symbol, date):
        date = getNDaysOff(date, 1)
        if date not in self.__underlyingAssetDict:
            return None
        else:
            return self.__underlyingAssetDict[date].get(symbol)

    def getValidTradingDaySet(self, stock, sDate, eDate):
        invalidTradingDaySet = set()
        tradingDayList = getTradingDay(getNDaysOff(sDate, 1), getNDaysOff(eDate, 1))

        for stockGroupDict in self.__userDefinedStockGroup:
            if stockGroupDict[stock] in [[], [stock]]:
                return set(getTradingDay(sDate, eDate))

        for industryDict in self.__industryDict.values():
            for date in tradingDayList:
                if stock not in industryDict[date]:
                    invalidTradingDaySet.add(getNDaysOff(date, -1))

        if self.__isUseUnderlyingAsset:
            for date in tradingDayList:
                if stock not in self.__underlyingAssetDict[date]:
                    invalidTradingDaySet.add(getNDaysOff(date, -1))

        return set(getTradingDay(sDate, eDate)) - invalidTradingDaySet

    def getIndexValidTradingDaySet(self, symbol, sDate, eDate):
        validTradingDaySet = set()
        tradingDayList = getTradingDay(getNDaysOff(sDate, 1), getNDaysOff(eDate, 1))

        if symbol in ["SZ50", "HS300", "ZZ500"]:
            return set(getTradingDay(sDate, eDate))

        for industryStockDict in self.__industryStockDict.values():
            for date in tradingDayList:
                if symbol in industryStockDict[date]:
                    validTradingDaySet.add(getNDaysOff(date, -1))

        return validTradingDaySet
