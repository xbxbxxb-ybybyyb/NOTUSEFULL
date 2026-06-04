from System.Factor import Factor
import numpy as np
from scipy.stats import norm


class INFDeviationRate(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__indexName = self._getParameter("IndexName")
        self.__deviation_rate = self.__get_deviation_rate()

    def calculate(self):
        self._addFactorValue(self.__deviation_rate)

    def __get_deviation_rate(self):
        closepI = self._getLastNHistoricalIndexDailyData(self.__indexName, "ClosePrice", 1)  # TODO 暂时取不到行业日频数据
        pclosepI = self._getLastNHistoricalIndexDailyData(self.__indexName, "PreviousClose", 1)
        closepG = self._getLastNHistoricalDailyDataForStockGroup("ClosePrice", 1)
        pclosepG = self._getLastNHistoricalDailyDataForStockGroup("PreviousClose", 1)
        if len(closepG) > 1:
            returnG = closepG / pclosepG
            returnI = closepI / pclosepI - 1
            wStd = np.nansum(np.power(returnG - returnI, 2)) / (len(closepG) - 1)
            loc = (returnG - returnI) / wStd
            deviation_rate = norm.cdf(loc, returnI, wStd)
        else:
            deviation_rate = np.zeros(1)
        return deviation_rate
