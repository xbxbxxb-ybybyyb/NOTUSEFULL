import os
import gc
import importlib
import datetime as dt
import pandas as pd
from copy import deepcopy
from System.DataBroadcaster.StockDataBroadcaster import StockDataBroadcaster
from System.DataBroadcaster.CBDataBroadcaster import CBDataBroadcaster
from System.DataBroadcaster.ETFDataBroadcaster import ETFDataBroadcaster
from System.DataBroadcaster.FutureDataBroadcaster import FutureDataBroadcaster
from System.DataBroadcaster.IndexDataBroadcaster import IndexDataBroadcaster
from xquant.factordata import FactorData
from xquant.compute.sparkmr import remote_print


class FactorManager:
    def __init__(self, assetType, symbol, factorConfig, startDate, endDate, stockSet, outputLibrary, dataManager):
        self.__fd = FactorData()
        self.__isExecutor = "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ

        self.__DATA_TYPE_DICT = {"Tick": {"Tick"}, "Minute": {"Minute"}, "Both": {"Tick", "Minute"}}

        self.__assetType = assetType
        self.__symbol = symbol
        self.__factorConfig = deepcopy(factorConfig)
        self.__startDate = startDate
        self.__endDate = endDate
        self.__outputLibrary = outputLibrary
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
        else:
            raise Exception("Unsupported Asset Type")

        self.__validTradingDayList = self.__dataManager.getValidTradingDayList(symbol, startDate, endDate)

        self.__factorList = []
        self.__factorDict = {}

        self.__tickTimestampList = None

    def initFactors(self):
        for config in self.__factorConfig:
            self.__fillDefaultValuesForConfig(config)

            className = config["ClassName"]
            if className.startswith("Factor"):
                module = importlib.import_module("Factor.{}".format(className))
            elif className.startswith("Tag"):
                module = importlib.import_module("Tag.{}".format(className))
            else:
                continue
            factor = getattr(module, className)(config, self)
            factor.register()

    def getDataBroadcaster(self):
        return self.__dataBroadcaster

    def getStock(self):
        return self.__symbol

    def getStockList(self, date, stockGroup):
        return self.__dataManager.getStockList(self.__symbol, date, stockGroup)

    def getIndustryCode(self, date, industryGroup):
        return self.__dataManager.getIndustryCode(self.__symbol, date, industryGroup)

    def getUnderlyingAsset(self, date):
        return self.__dataManager.getUnderlyingAsset(self.__symbol, date)

    def getFactor(self, config):
        self.__fillDefaultValuesForConfig(config)

        config["FactorName"] = config.get("FactorName", "")
        className = config["ClassName"]
        if className.startswith("Factor"):
            module = importlib.import_module("Factor.{}".format(className))
        else:
            module = importlib.import_module("NonFactor.{}".format(className))
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
        else:
            for configTmp, _ in self.__factorDict[className]:
                if config == configTmp:
                    return

            self.__factorDict[className].append([config, factor])
            self.__factorList.append(factor)

    def calculateFactors(self, date):
        if date in self.__validTradingDayList:
            self.__onNewDay(date)
            self.__calculate()
            self.__onDayEnd(date)

    def __onNewDay(self, date):
        self.__dataBroadcaster.onNewDay(date)

        self.__tickTimestampList = []
        for factor in self.__factorList:
            factor.onNewDay(date)

        gc.collect()

    def __calculate(self):
        while True:
            tickTimestamp = self.__dataBroadcaster.broadcast()

            if tickTimestamp is None:
                break

            self.__tickTimestampList.append(tickTimestamp)
            for factor in self.__factorList:
                factor.calculate()

    def __onDayEnd(self, date):
        factorValueDict = {}
        for factor in self.__factorList:
            factorName, factorValueList = factor.onDayEnd()
            if factorName is None:
                continue
            else:
                factorValueDict[factorName] = factorValueList
        factorValueDict["timestamp"] = self.__tickTimestampList
        factorValueDF = pd.DataFrame(factorValueDict)

        isHasNaN = False
        if factorValueDF.isnull().any().any():
            isHasNaN = True
            factorWithNansNames = factorValueDF.columns[factorValueDF.isnull().any(axis=0)].tolist()
            factorValueDF = factorValueDF.dropna(axis=1, how="any")
            if self.__isExecutor:
                remote_print("ERROR: There is NaNs in factor value data frame for {} on {}".format(self.__symbol, date))
            else:
                print("ERROR: There is NaNs in factor value data frame for {} on {}".format(self.__symbol, date))

        if not factorValueDF.empty:
            startTime = dt.datetime.now()
            self.__fd.update_factor_value(self.__outputLibrary, factorValueDF, self.__symbol, str(date))
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if timeCost >= 1:
                if self.__isExecutor:
                    remote_print("WARN: Writing to HBASE costs {} sec for {} on {}"
                                 .format(round(timeCost, 2), self.__symbol, date))
                else:
                    print("WARN: Writing to HBASE costs {} sec for {} on {}"
                          .format(round(timeCost, 2), self.__symbol, date))

        if isHasNaN:
            raise Exception("ERROR: There is NaNs in factor value data frame for {} on {}; FactorNames: {}"
                            .format(self.__symbol, date, factorWithNansNames))

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
        config["DataType"] = self.__DATA_TYPE_DICT[config.get("DataType", "Tick")]
        config["DataTypeCS"] = self.__DATA_TYPE_DICT[config.get("DataTypeCS", "Minute")]
        config["DataTypeIndex"] = self.__DATA_TYPE_DICT[config.get("DataTypeIndex", "Minute")]
        config["DataTypeUA"] = self.__DATA_TYPE_DICT[config.get("DataTypeUA", "Tick")]
        config["StockGroup"] = config.get("StockGroup", "Self")
        config["IndexGroup"] = config.get("IndexGroup", [])
        config["SplitAdjusted"] = config.get("SplitAdjusted", False)
        config["UnderlyingAsset"] = config.get("UnderlyingAsset", False)
        config["Parameters"] = config.get("Parameters", {})
