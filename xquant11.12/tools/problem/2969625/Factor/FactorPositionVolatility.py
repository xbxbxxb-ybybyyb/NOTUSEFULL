from System.Factor import Factor
import numpy as np


class FactorPositionVolatility(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dlag = self._getParameter("DayLag")

    def calculate(self):
        avg_dvol = np.nanmean(self._getLastNHistoricalDailyData("Volume", self.__dlag))
        bid_vol = self._getLastTickData("BidVolume")
        ask_vol = self._getLastTickData("AskVolume")
        if bid_vol is None or ask_vol is None:
            lastv = self.getLastFactorValue()
            if lastv is None:
                factorValue = 0
            else:
                factorValue = lastv
        else:
            if np.isnan(avg_dvol) or avg_dvol == 0:
                factorValue = 0.
            else:
                factorValue = np.nanstd(bid_vol / avg_dvol) - np.nanstd(ask_vol / avg_dvol)

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
