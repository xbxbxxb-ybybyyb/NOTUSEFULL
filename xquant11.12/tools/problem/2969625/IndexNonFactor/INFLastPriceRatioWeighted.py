from System.Factor import Factor
import numpy as np


class INFLastPriceRatioWeighted(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dlag = self._getParameter("DayLag")

    def calculate(self):

        dclose_g = self._getLastNHistoricalDailyDataForStockGroup("ClosePrice", self.__dlag - 1, isStacked=True)
        lastp_g = self._getLastTickDataForStockGroup("LastPrice", isStacked=True)[0]
        ma_g = (np.nansum(dclose_g, axis=0) + lastp_g) / self.__dlag
        ma_g[ma_g == 0] = np.nan
        ma_ratio_g = lastp_g / ma_g
        w = self.__get_weights()
        factorValue = np.nansum(np.multiply(ma_ratio_g, w))

        self._addFactorValue(factorValue)

    def __get_weights(self):
        ffs = self._getLastNHistoricalDailyDataForStockGroup("FreeFloatShares", 1, isStacked=True)[0]
        closep = self._getLastNHistoricalDailyDataForStockGroup("ClosePrice", 1, isStacked=True)[0]
        mktcap = ffs * closep
        w = mktcap / np.nansum(mktcap)
        return w
