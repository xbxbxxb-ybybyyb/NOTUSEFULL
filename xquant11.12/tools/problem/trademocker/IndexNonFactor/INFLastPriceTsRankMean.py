from System.Factor import Factor
import numpy as np


class INFLastPriceTsRankMean(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dlag = self._getParameter("DayLag")

    def calculate(self):

        lastp_g = self._getLastTickDataForStockGroup("LastPrice", isStacked=True)
        dclose_g = self._getLastNHistoricalDailyDataForStockGroup("ClosePrice", self.__dlag, isStacked=True)

        factorValue = np.nanmean(np.nansum(dclose_g < lastp_g, axis=0) / self.__dlag)

        self._addFactorValue(factorValue)
