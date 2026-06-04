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
        self.__dataType = set()
        self.__dataTypeCS = set()
        self.__dataTypeIndex = set()
        self.__dataTypeUA = set()
        self.__indexGroup = set()
        self.__isSplitAdjustedNeeded = False
        self.__isUseUnderlyingAsset = False

        self.__completeStockDict = None
        self.__indexDict = {}
        self.__industryDict = {}
        self.__industryStockDict = {}
        self.__userDefinedStockGroup = []
        self.__usedStockGroup = set()
        self.__underlyingAssetDict = {}

    def analyzeConfig(self, sDate, eDate):
        tradingDayList = getTradingDay(getNDaysOff(sDate, 1), getNDaysOff(eDate, 1))

        fd = None
        completeStockList = None

        for config in self.__factorConfig:
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
            self.__isSplitAdjustedNeeded = self.__isSplitAdjustedNeeded or config.get("SplitAdjusted", False)
            self.__isUseUnderlyingAsset = self.__isUseUnderlyingAsset or config.get("UnderlyingAsset", False)

            # Update Time Series Data Type
            dataType = config.get("DataType", "Tick")
            if dataType == "Tick":
                self.__dataType.add("Tick")
            elif dataType == "Both" or dataType == "Minute":
                self.__dataType.add("Tick")
                self.__dataType.add("Minute")

            # Acquire Necessary Stock Group Lists for All Factors
            group = config.get("StockGroup")
            if group is not None:
                if fd is None:
                    fd = FDTool(self.__mdLibrary)
                    completeStockList = fd.hset("MARKET", getNDaysOff(eDate, 1), "ALLA_HIS")

                if isinstance(group, dict):
                    self.__userDefinedStockGroup.append(group)
                elif group == "ALLA":
                    if self.__completeStockDict is None:
                        self.__completeStockDict = {}
                        for date in tradingDayList:
                            self.__completeStockDict[date] = fd.hset("MARKET", date, "ALLA")
                        self.__usedStockGroup.add(group)
                elif group in ["SZ50", "HS300", "ZZ500"]:
                    if group not in self.__usedStockGroup:
                        self.__indexDict[group] = {}
                        for date in tradingDayList:
                            self.__indexDict[group][date] = fd.hset("INDEX", date, group)
                        self.__usedStockGroup.add(group)
                else:
                    if group not in self.__usedStockGroup:
                        self.__industryDict[group] = {}
                        self.__industryStockDict[group] = {}
                        for date in tradingDayList:
                            industryDF = fd.hsi(completeStockList, date, group[:-1], int(group[-1]))
                            industryDF = industryDF.dropna()
                            self.__industryDict[group][date] = industryDF.set_index("Stock")["IndustryCode"].to_dict()
                            self.__industryStockDict[group][date] = {}
                            for industryCode, stockSeries in industryDF.groupby("IndustryCode")["Stock"]:
                                self.__industryStockDict[group][date][industryCode] = stockSeries.tolist()
                        self.__usedStockGroup.add(group)

                # Update Cross Section Data Type when StockGroup is Provided
                dataTypeCS = config.get("DataTypeCS", "Minute")
                if dataTypeCS == "Minute":
                    self.__dataTypeCS.add("Minute")
                elif dataTypeCS == "Tick":
                    self.__dataTypeCS.add("Tick")
                elif dataTypeCS == "Both":
                    self.__dataTypeCS.add("Minute")
                    self.__dataTypeCS.add("Tick")

            # Acquire Necessary Industry Codes for Industry Index for All Factors
            indexGroupList = config.get("IndexGroup")
            if indexGroupList is not None:
                if fd is None:
                    fd = FDTool(self.__mdLibrary)
                    completeStockList = fd.hset("MARKET", getNDaysOff(eDate, 1), "ALLA_HIS")

                self.__indexGroup = self.__indexGroup.union(indexGroupList)

                for indexGroup in indexGroupList:
                    if indexGroup not in INDEX_LIST and indexGroup not in self.__usedStockGroup:
                        self.__industryDict[indexGroup] = {}
                        self.__industryStockDict[indexGroup] = {}
                        for date in tradingDayList:
                            industryDF = fd.hsi(completeStockList, date, indexGroup[:-1], int(indexGroup[-1]))
                            industryDF = industryDF.dropna()
                            self.__industryDict[indexGroup][date] = (industryDF.set_index("Stock")["IndustryCode"]
                                                                     .to_dict())
                            self.__industryStockDict[indexGroup][date] = {}
                            for industryCode, stockSeries in industryDF.groupby("IndustryCode")["Stock"]:
                                self.__industryStockDict[indexGroup][date][industryCode] = stockSeries.tolist()

                # Update Index Data Type when IndexGroup is Provided
                dataTypeIndex = config.get("DataTypeIndex", "Minute")
                if dataTypeIndex == "Minute":
                    self.__dataTypeIndex.add("Minute")
                elif dataTypeIndex == "Tick":
                    self.__dataTypeIndex.add("Tick")
                elif dataTypeIndex == "Both":
                    self.__dataTypeIndex.add("Minute")
                    self.__dataTypeIndex.add("Tick")

            if self.__isUseUnderlyingAsset:
                if fd is None:
                    fd = FDTool(self.__mdLibrary)

                if not self.__underlyingAssetDict:
                    for date in tradingDayList:
                        if self.__assetType == "CB":
                            cbMap = fd.cbs_map(getNDaysOff(date, -1))
                            cbMap = cbMap.dropna()
                            self.__underlyingAssetDict[date] = cbMap.set_index("CBond")["Stock"].to_dict()
                        elif self.__assetType == "ETF":
                            self.__underlyingAssetDict[date] = STOCK_ETF_INDEX_MAP
                        elif self.__assetType == "Future":
                            self.__underlyingAssetDict[date] = INDEX_FUTURE_INDEX_MAP

                dataTypeUA = config.get("DataTypeUA", "Tick")
                if dataTypeUA == "Minute":
                    self.__dataTypeUA.add("Minute")
                elif dataTypeUA == "Tick":
                    self.__dataTypeUA.add("Tick")
                elif dataTypeUA == "Both":
                    self.__dataTypeUA.add("Minute")
                    self.__dataTypeUA.add("Tick")

        del fd

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
            "dataType": self.__dataType,
            "dataTypeCS": self.__dataTypeCS,
            "dataTypeIndex": self.__dataTypeIndex,
            "dataTypeUA": self.__dataTypeUA,
            "indexGroup": self.__indexGroup,
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
