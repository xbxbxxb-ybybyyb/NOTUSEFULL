from System.Factor import Factor
import numpy as np


class FactorAskBidWeightedPriceDiff(Factor):

    def calculate(self):
        avgp = self._getLastNHistoricalDailyData("ClosePrice", 1)[-1]
        askp = self._getLastTickData("AskPrice")
        askv = self._getLastTickData("AskVolume")
        bidp = self._getLastTickData("BidPrice")
        bidv = self._getLastTickData("BidVolume")

        if np.isnan(avgp) or avgp == 0:
            factorValue = 0

        elif (np.nansum(askv) != 0) and (np.nansum(bidv) != 0):
            askpw = np.nansum(askp * askv / np.nansum(askv))
            bidpw = np.nansum(bidp * bidv / np.nansum(bidv))
            factorValue = (askpw - bidpw) / avgp * 10
        else:
            lastv = self.getLastFactorValue()
            if lastv is not None:
                factorValue = lastv
            else:
                factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

