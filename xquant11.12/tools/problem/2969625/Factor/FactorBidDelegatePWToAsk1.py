from System.Factor import Factor
import numpy as np


class FactorBidDelegatePWToAsk1(Factor):

    def calculate(self):

        bidp = self._getLastTickData("BidPrice")
        bidv = self._getLastTickData("BidVolume")
        askp = self._getLastNTodayTickData("AskPrice", 2)

        if len(bidp) < 2:
            factorValue = 0.
        else:
            if np.nansum(bidv) == 0:  # 跌停
                factorValue = -1.
            elif (askp[-1][0] < 0.01) or (askp[0][0] < 0.01):  # 涨停
                factorValue = 1.
            else:
                bidpw = np.nansum(bidp * bidv) / np.nansum(bidv)
                dist_1 = bidpw / askp[-1][0] - 1
                dist_2 = askp[-1][0] / askp[0][0] - 1
                factorValue = (dist_1 + dist_2) * 1e2

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)
