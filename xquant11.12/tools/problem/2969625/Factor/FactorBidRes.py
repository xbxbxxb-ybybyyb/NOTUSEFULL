import numpy as np
from System.Factor import Factor


class FactorBidRes(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        bidP = self._getLastTickData("BidPrice")
        askP = self._getLastTickData("AskPrice")
        bidV = self._getLastTickData("BidVolume")
        askV = self._getLastTickData("AskVolume")
        maxP = self._getLastTickData("MaxPrice")
        minP = self._getLastTickData("MinPrice")

        askVSum = askV[:2].sum()
        askVWAP = (askP[:2] * askV[:2]).sum() / askVSum if askVSum > 0 else maxP

        bidIdx = self.__get_top_2_index(bidV)
        bidV = bidV[bidIdx]
        bidP = bidP[bidIdx]

        bidVSum = bidV.sum()
        bidRes = (bidP * bidV).sum() / bidVSum if bidVSum > 0 else minP

        ret = (askVWAP / bidRes - 1) * 1000 if bidRes > 0.001 else 0.0
        vol = bidVSum / askVSum if askVSum > 0 else 0.0

        factorValue = vol / ret if ret > 0 else 0.0

        self._addFactorValue(factorValue)

    @staticmethod
    def __get_top_2_index(x):
        if x[0] > x[1]:
            vmax = [x[0], x[1]]
            imax = [0, 1]
        else:
            vmax = [x[1], x[0]]
            imax = [1, 0]

        for i in range(2, len(x)):
            if x[i] > vmax[0] - 1e-6:
                vmax[1] = vmax[0]
                imax[1] = imax[0]
                vmax[0] = x[i]
                imax[0] = i
            elif x[i] > vmax[1] - 1e-6:
                vmax[1] = x[i]
                imax[1] = i
        return imax
