import numpy as np
from System.Factor import Factor


class ResPrice(Factor):
    def calculate(self):
        bidP = self._getLastTickData("BidPrice")
        askP = self._getLastTickData("AskPrice")
        bidV = self._getLastTickData("BidVolume")
        askV = self._getLastTickData("AskVolume")
        maxP = self._getLastTickData("MaxPrice")
        minP = self._getLastTickData("MinPrice")

        if askV[0] < 0.5:
            askRes = maxP
        elif (askV > 2 * np.mean(askV)).sum() > 0:
            mask = askV > 2 * np.mean(askV)
            askRes = np.sum(askP[mask] * askV[mask]) / np.sum(askV[mask])
        else:
            askRes = np.sum(askP * askV) / np.sum(askV)

        if bidV[0] < 0.5:
            bidRes = minP
        elif (bidV > 2 * np.mean(bidV)).sum() > 0:
            mask = bidV > 2 * np.mean(bidV)
            bidRes = np.sum(bidP[mask] * bidV[mask]) / np.sum(bidV[mask])
        else:
            bidRes = np.sum(bidP * bidV) / np.sum(bidV)

        factorValue = [askRes, bidRes]

        self._addFactorValue(factorValue)
