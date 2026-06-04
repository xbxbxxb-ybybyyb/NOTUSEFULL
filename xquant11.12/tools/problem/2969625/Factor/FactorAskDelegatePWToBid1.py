from System.Factor import Factor
import numpy as np


class FactorAskDelegatePWToBid1(Factor):

    def calculate(self):

        askp = self._getLastTickData("AskPrice")
        askv = self._getLastTickData("AskVolume")
        bidp = self._getLastNTodayTickData("BidPrice", 2)

        if len(bidp) < 2:
            factorValue = 0.
        else:
            if np.nansum(askv) == 0:  # 涨停
                factorValue = 1.
            elif (bidp[-1][0] < 0.01) or (bidp[0][0] < 0.01):  # 跌停
                factorValue = 0.
            else:
                askpw = np.nansum(askp * askv) / np.nansum(askv)
                dist_1 = askpw / bidp[-1][0] - 1
                dist_2 = bidp[-1][0] / bidp[0][0] - 1
                factorValue = (dist_1 + dist_2) * 1e2

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)
