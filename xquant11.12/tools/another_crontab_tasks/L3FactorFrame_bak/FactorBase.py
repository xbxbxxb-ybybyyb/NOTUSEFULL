# BreakingP0NumOrders
import numpy as np
import datetime as dt
import os

###########
date = "20231207"
symbol = "688012.SH"
###########

from xquant.marketdata import MarketData


class FactorBase:
    def __init__(self, param_dict, marketDataManager) -> None:
        self.marketDataManager = marketDataManager
        self.__factorValueList = []
        self.params = param_dict

    def set_factor_name(self, factor_class_name, pidx):
        if self.params.get("factor_name", None):
            factor_name = self.params.get("factor_name")
        else:
            if pidx > 0:
                extra_param = "_" + "_".join([str(self.params[pkey]).replace(".", "") for pkey in self.params])
                factor_name = factor_class_name + extra_param
            else:
                # 第一个因子保持原名
                factor_name = factor_class_name
        self.factor_name = factor_name

    def getPrevNTick(self, field, slide):
        return self.marketDataManager.getPrevNTick(field, slide)

    def getPrevTick(self, field):
        return self.marketDataManager.getPrevTick(field)

    def getPrevSecTick(self, field, n_seconds):
        return self.marketDataManager.getPrevSecTick(field, n_seconds)

    def getPrevOrder(self, field):
        return self.marketDataManager.getPrevOrder(field)

    def getPrevTrade(self, field):
        return self.marketDataManager.getPrevTrade(field)

    def getPrevNOrder(self, field, slide):
        return self.marketDataManager.getPrevNOrder(field, slide)

    def getPrevNTrade(self, field, slide):
        return self.marketDataManager.getPrevNTrade(field, slide)

    def getPrevSecOrder(self, field, n_seconds):
        return self.marketDataManager.getPrevSecOrder(field, n_seconds)

    def getPrevSecTrade(self, field, n_seconds):
        return self.marketDataManager.getPrevSecTrade(field, n_seconds)

    def getPrevNCancel(self, field, slide):
        return self.marketDataManager.getPrevNCancel(field, slide)

    def getPrevSecCancel(self, field, n_seconds):
        return self.marketDataManager.getPrevSecCancel( field, n_seconds)

    def getPrevCancel(self, field):
        return self.marketDataManager.getPrevCancel(field)

    def addFactorValue(self, factorValue):
        self.__factorValueList.append(factorValue)

    def addNanFactorValue(self):
        self.__factorValueList.append(np.nan)

    def addZeroFactorValue(self, type_int = False):
        if type_int:
            self.__factorValueList.append(0)
        else:
            self.__factorValueList.append(0.0)

    def getFactorValue(self):
        return np.array(self.__factorValueList)

    def getLastFactorValue(self):
        return self.__factorValueList[-1]

