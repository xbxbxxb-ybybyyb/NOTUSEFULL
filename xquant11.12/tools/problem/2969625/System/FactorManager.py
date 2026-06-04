import gc
import importlib
import datetime as dt
import numpy as np
import pandas as pd
from copy import deepcopy
from System.DataBroadcaster.StockDataBroadcaster import StockDataBroadcaster
from System.DataBroadcaster.CBDataBroadcaster import CBDataBroadcaster
from System.DataBroadcaster.ETFDataBroadcaster import ETFDataBroadcaster
from System.DataBroadcaster.FutureDataBroadcaster import FutureDataBroadcaster
from System.DataBroadcaster.IndexDataBroadcaster import IndexDataBroadcaster
from System.DataBroadcaster.INFDataBroadcaster import INFDataBroadcaster
from CommonUtils.MyPrint import myPrint
from xquant.factordata import FactorData


class FactorManager:
    def __init__(self, assetType, symbol, factorConfig, startDate, endDate, stockSet, tickOutputLibrary,
                 l2pTickOutputLibrary, minuteOutputLibrary, dataManager):
        self.__fd = FactorData()

        self.__DATA_TYPE_DICT = {"Tick": {"Tick"}, "Minute": {"Minute"}, "Both": {"Tick", "Minute"}}

        self.__assetType = assetType
        self.__symbol = symbol
        self.__factorConfig = deepcopy(factorConfig)
        self.__startDate = startDate
        self.__endDate = endDate
        self.__tickOutputLibrary = tickOutputLibrary
        self.__l2pTickOutputLibrary = l2pTickOutputLibrary
        self.__minuteOutputLibrary = minuteOutputLibrary
        self.__dataManager = dataManager

        if self.__assetType == "Stock":
            self.__dataBroadcaster = StockDataBroadcaster(symbol, stockSet, dataManager)
        elif self.__assetType == "CB":
            self.__dataBroadcaster = CBDataBroadcaster(symbol, stockSet, dataManager)
        elif self.__assetType == "ETF":
            self.__dataBroadcaster = ETFDataBroadcaster(symbol, stockSet, dataManager)
        elif self.__assetType == "Future":
            self.__dataBroadcaster = FutureDataBroadcaster(symbol, stockSet, dataManager)
        elif self.__assetType == "Index":
            self.__dataBroadcaster = IndexDataBroadcaster(symbol, stockSet, dataManager)
        elif self.__assetType == "INF":
            self.__dataBroadcaster = INFDataBroadcaster(symbol, stockSet, dataManager)
        elif self.__assetType == "StockAfternoon":
            self.__dataBroadcaster = StockDataBroadcaster(symbol, stockSet, dataManager)
        else:
            raise Exception("Unsupported Asset Type")

        self.__validTradingDayList = self.__dataManager.getValidTradingDayList(symbol, startDate, endDate)

        self.__factorList = []
        self.__broadcastTypeList = []
        self.__factorDict = {}

        self.__tickTimestampList = None
        self.__minuteTimestampList = None
        self.__INFStockGroup = None

        self.__l2pTickTimestampList = None
        self.__l2pTickFactorValueDict = None

    def initFactors(self):
        for config in self.__factorConfig:
            # if self.__symbol.endswith("SH") and ("O" in config.get("DataSource", []) or "C" in config.get("DataSource", [])):
            #     continue

            self.__fillDefaultValuesForConfig(config)

            className = config["ClassName"]
            if className.startswith("Factor"):
                module = importlib.import_module(f"Factor.{className}")
            elif className.startswith("Tag"):
                module = importlib.import_module(f"Tag.{className}")
            elif className.startswith("INF"):
                module = importlib.import_module(f"IndexNonFactor.{className}")
            else:
                continue
            factor = getattr(module, className)(config, self)
            factor.register()

            if self.__assetType == "INF":
                if self.__INFStockGroup is None or self.__INFStockGroup == config["StockGroup"]:
                    self.__INFStockGroup = config["StockGroup"]
                else:
                    raise Exception(f"Different StockGroup for {className}")

    def getDataBroadcaster(self):
        return self.__dataBroadcaster

    def getAssetType(self):
        return self.__assetType

    def getStock(self):
        return self.__symbol

    def getStockList(self, date, stockGroup):
        return self.__dataManager.getStockList(self.__symbol, date, stockGroup)

    def getIndustryCode(self, date, industryGroup):
        return self.__dataManager.getIndustryCode(self.__symbol, date, industryGroup)

    def getUnderlyingAsset(self, date):
        return self.__dataManager.getUnderlyingAsset(self.__symbol, date)

    def getINFStockListDict(self, symbol, date):
        return self.__dataManager.getINFStockListDict(symbol, date)

    def getFactor(self, config):
        self.__fillDefaultValuesForConfig(config)

        config["FactorName"] = config.get("FactorName", "")
        className = config["ClassName"]
        if className.startswith("Factor"):
            module = importlib.import_module(f"Factor.{className}")
        elif className.startswith("INF"):
            module = importlib.import_module(f"IndexNonFactor.{className}")
        else:
            module = importlib.import_module(f"NonFactor.{className}")
        factor = getattr(module, className)(config, self)
        factor.register()

        del config["FactorName"]
        for configTmp, factorTmp in self.__factorDict[className]:
            if config == configTmp:
                return factorTmp

        raise Exception("Unexpected Error: Factor Not Found")

    def registerFactor(self, config, factor):
        config = deepcopy(config)

        if "FactorName" in config:
            del config["FactorName"]

        className = config["ClassName"]
        if className not in self.__factorDict:
            self.__factorDict[className] = [[config, factor]]
            self.__factorList.append(factor)
            self.__broadcastTypeList.append(int(config["BType"] == "Minute"))
        else:
            for configTmp, _ in self.__factorDict[className]:
                if config == configTmp:
                    return

            self.__factorDict[className].append([config, factor])
            self.__factorList.append(factor)
            self.__broadcastTypeList.append(int(config["BType"] == "Minute"))

    def calculateFactors(self, date):
        if date in self.__validTradingDayList:
            self.__onNewDay(date)
            self.__calculate()
            self.__onDayEnd(date)

    def __onNewDay(self, date):
        self.__dataBroadcaster.onNewDay(date)

        self.__tickTimestampList = []
        self.__minuteTimestampList = []
        self.__l2pTickTimestampList = []
        self.__l2pTickFactorValueDict = {}
        for factor in self.__factorList:
            factor.onNewDay(date)

        gc.collect()

    def __onAfternoon(self):
        for factor in self.__factorList:
            factor.onAfternoon()

    def __calculate(self):
        isAfternoonBegin = False

        while True:
            timestamp, dataType = self.__dataBroadcaster.broadcast()

            if timestamp is None:
                break

            if not isAfternoonBegin and (timestamp + 28800) % 86400 > 43200:
                self.__onAfternoon()
                isAfternoonBegin = True

            if dataType == 0:
                self.__tickTimestampList.append(timestamp)
                for factor, broadcastType in zip(self.__factorList, self.__broadcastTypeList):
                    if broadcastType == 0:
                        factor.calculate()
            elif dataType == 1:
                self.__minuteTimestampList.append(timestamp)
                for factor, broadcastType in zip(self.__factorList, self.__broadcastTypeList):
                    if broadcastType == 1:
                        factor.calculate()
            elif dataType == 2:
                self.__l2pTickTimestampList.append(timestamp)
                for factor, broadcastType in zip(self.__factorList, self.__broadcastTypeList):
                    if broadcastType == 0:
                        factor.calculate()
                for factor, broadcastType in zip(self.__factorList, self.__broadcastTypeList):
                    if broadcastType == 0:
                        factorName, factorValue = factor.reset()
                        if factorName is None:
                            continue
                        if factorName not in self.__l2pTickFactorValueDict:
                            self.__l2pTickFactorValueDict[factorName] = []
                        self.__l2pTickFactorValueDict[factorName].append(factorValue)
            else:
                raise Exception(f"Unexpected data type {dataType}")

    def __onDayEnd(self, date):
        tickFactorValueDict = {}
        minuteFactorValueDict = {}
        for factor, broadcastType in zip(self.__factorList, self.__broadcastTypeList):
            factorName, factorValueList = factor.onDayEnd()
            if factorName is None:
                continue

            if broadcastType == 0:
                tickFactorValueDict[factorName] = factorValueList
            else:
                minuteFactorValueDict[factorName] = factorValueList

        if tickFactorValueDict:
            tickFactorValueDict["timestamp"] = self.__tickTimestampList
            tickFactorValueDF = pd.DataFrame(tickFactorValueDict)
            self.__saveFactorValue(tickFactorValueDF, date, self.__tickOutputLibrary)

        if minuteFactorValueDict:
            minuteFactorValueDict["timestamp"] = self.__minuteTimestampList
            minuteFactorValueDF = pd.DataFrame(minuteFactorValueDict)
            self.__saveFactorValue(minuteFactorValueDF, date, self.__minuteOutputLibrary)

        if self.__l2pTickFactorValueDict:
            self.__l2pTickFactorValueDict["timestamp"] = self.__l2pTickTimestampList
            l2pTickFactorValueDF = pd.DataFrame(self.__l2pTickFactorValueDict)
            self.__saveFactorValue(l2pTickFactorValueDF, date, self.__l2pTickOutputLibrary)

    def __saveFactorValue(self, factorValueDF, date, outputLibrary):
        factorNames = factorValueDF.columns.difference(["timestamp"])
        factorValueDF.loc[:, factorNames] = factorValueDF.loc[:, factorNames].astype(np.float32)

        isHasNaN = False
        factorWithNansNames = None
        if factorValueDF.isnull().any().any():
            isHasNaN = True
            factorWithNansNames = factorValueDF.columns[factorValueDF.isnull().any(axis=0)].tolist()
            factorValueDF = factorValueDF.dropna(axis=1, how="any")
            myPrint(f"ERROR: There is NaNs in factor value data frame for {self.__symbol} on {date}")

        if not factorValueDF.empty:
            if self.__assetType == "INF":
                factorValueDF["symbols"] = ([self.getStockList(date, self.__INFStockGroup)] + [np.nan] * (len(self.__tickTimestampList) - 1))

            startTime = dt.datetime.now()
            if self.__assetType == "INF":
                for i in range(0, factorValueDF.shape[1], 8):
                    self.__fd.update_factor_value(outputLibrary, factorValueDF.iloc[:, i: min(i + 8, factorValueDF.shape[1])], self.__symbol, str(date), cell_size=200)
            else:
                self.__fd.update_factor_value(outputLibrary, factorValueDF, self.__symbol, str(date))
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if timeCost >= 1:
                myPrint(f"WARN: Writing to HBASE costs {round(timeCost, 2)} sec for {self.__symbol} on {date}")

        if isHasNaN:
            raise Exception(f"ERROR: There is NaNs in factor value data frame for {self.__symbol} on {date}; FactorNames: {factorWithNansNames}")

    def __fillDefaultValuesForConfig(self, config):
        config["TickLength"] = config.get("TickLength", 0)
        config["MinuteLength"] = config.get("MinuteLength", 0)
        config["DailyLength"] = config.get("DailyLength", 0)
        config["TickLengthCS"] = config.get("TickLengthCS", 0)
        config["MinuteLengthCS"] = config.get("MinuteLengthCS", 0)
        config["DailyLengthCS"] = config.get("DailyLengthCS", 0)
        config["TickLengthIndex"] = config.get("TickLengthIndex", 0)
        config["MinuteLengthIndex"] = config.get("MinuteLengthIndex", 0)
        config["DailyLengthIndex"] = config.get("DailyLengthIndex", 0)
        config["TickLengthUA"] = config.get("TickLengthUA", 0)
        config["MinuteLengthUA"] = config.get("MinuteLengthUA", 0)
        config["DailyLengthUA"] = config.get("DailyLengthUA", 0)
        config["TickLengthINF"] = config.get("TickLengthINF", 0)
        config["BType"] = config.get("BType", "Tick")
        config["DataType"] = self.__DATA_TYPE_DICT[config.get("DataType", config.get("BType", "Tick"))]
        config["DataTypeCS"] = self.__DATA_TYPE_DICT[config.get("DataTypeCS", "Minute")]
        config["DataTypeIndex"] = self.__DATA_TYPE_DICT[config.get("DataTypeIndex", "Minute")]
        config["DataTypeUA"] = self.__DATA_TYPE_DICT[config.get("DataTypeUA", "Tick")]
        config["StockGroup"] = config.get("StockGroup", "Self")
        config["IndexGroup"] = config.get("IndexGroup", [])
        config["INFGroup"] = config.get("INFGroup", {})
        config["SplitAdjusted"] = config.get("SplitAdjusted", False)
        config["UnderlyingAsset"] = config.get("UnderlyingAsset", False)
        config["Parameters"] = config.get("Parameters", {})
