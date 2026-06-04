# BreakingP0NumOrders
import numpy as np
import datetime as dt
import os


class FactorBase:
    def __init__(self, param_dict, factorManager, marketDataManager) -> None:
        self.factorManager = factorManager
        self.marketDataManager = marketDataManager
        self._factorValueList = []
        self.params = param_dict

    def set_factor_name(self, factor_class_name, pidx):
        if self.params.get("factor_name", None):
            factor_name = self.params.get("factor_name")
        else:
            if pidx > 0:
                extra_param = "_" + "_".join([str(self.params[pkey]).replace(".", "") for pkey in self.params])
                factor_name = factor_class_name + extra_param
            else:
                # ��һ�����ӱ���ԭ��
                factor_name = factor_class_name
        self.factor_name = factor_name

    def getPrevNTick(self, field, slide):
        return self.marketDataManager.getPrevNTick(field, slide)

    def getPrevTick(self, field):
        return self.marketDataManager.getPrevTick(field)

    def getPrevSecTick(self, field, n_seconds, end_timestamp):
        return self.marketDataManager.getPrevSecTick(field, n_seconds, end_timestamp = end_timestamp)

    def getPrevOrder(self, field):
        return self.marketDataManager.getPrevOrder(field)

    def getPrevTrade(self, field):
        return self.marketDataManager.getPrevTrade(field)

    def getPrevNOrder(self, field, slide):
        return self.marketDataManager.getPrevNOrder(field, slide)

    def getPrevNTrade(self, field, slide):
        return self.marketDataManager.getPrevNTrade(field, slide)

    def getPrevSecOrder(self, field, n_seconds, end_timestamp = None):
        return self.marketDataManager.getPrevSecOrder(field, n_seconds, end_timestamp = end_timestamp)

    def getPrevSecTrade(self, field, n_seconds, end_timestamp = None):
        return self.marketDataManager.getPrevSecTrade(field, n_seconds, end_timestamp = end_timestamp)

    def getPrevNCancel(self, field, slide):
        return self.marketDataManager.getPrevNCancel(field, slide)

    def getPrevSecCancel(self, field, n_seconds, end_timestamp = None):
        return self.marketDataManager.getPrevSecCancel( field, n_seconds, end_timestamp = end_timestamp)

    def getPrevCancel(self, field):
        return self.marketDataManager.getPrevCancel(field)

    def addFactorValue(self, factorValue):
        self._factorValueList.append(factorValue)

    def addNanFactorValue(self):
        self._factorValueList.append(np.nan)

    def addZeroFactorValue(self, type_int = False):
        if type_int:
            self._factorValueList.append(0)
        else:
            self._factorValueList.append(0.0)

    def getFactorValue(self):
        return np.array(self._factorValueList)

    def getLastFactorValue(self):
        return self._factorValueList[-1]

    def get_factor_instance(self, factor_name):
        return self.factorManager.get_factor_instance(factor_name)

