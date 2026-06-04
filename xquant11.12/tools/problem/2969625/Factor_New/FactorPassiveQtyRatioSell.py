import numpy as np
from System.Factor import Factor


class FactorPassiveQtyRatioSell(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.AggressiveOrderQty = self._getFactor({"ClassName": "AggressiveOrderQty"})
        self._addIntermediate("ratio", [])

    def calculate(self):
        buyQty, sellQty = self.AggressiveOrderQty.getLastFactorValue()[2:4]
        bidV = self._getLastTickData("BidVolume")
        askV = self._getLastTickData("AskVolume")
        bidN = self._getLastTickData("BidNum")
        askN = self._getLastTickData("AskNum")

        bidQty = np.sum(bidV[:5]) / np.sum(bidN[:5]) if np.sum(bidN[:5]) > 0 else np.sum(askV[:5]) / np.sum(askN[:5])

        ratio = self.getIntermediate("ratio")
        ratio.append(sellQty / bidQty)

        fv = self.zscore(ratio, 5, 60)

        self._addFactorValue(-fv)

    @staticmethod
    def zscore(l1, w1, w2):
        std1 = np.nanstd(l1[-w2:])
        if std1 == 0 or np.isnan(std1):
            return 0
        else:
            return (np.nanmean(l1[-w1:]) - np.nanmean(l1[-w2:])) / std1
