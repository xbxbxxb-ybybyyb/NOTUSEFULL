import numpy as np
from System.Factor import Factor


class FactorAggressiveOrderRatioRelSell(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.window = self._getParameter("Window")
        self.lag1 = self._getParameter("Lag1")
        self.lag2 = self._getParameter("Lag2")

        self.aggressiveOrderNum = self._getFactor(
            {
                "ClassName": "AggressiveOrderNum"
            }
        )

        self._addIntermediate("aggressiveNumList", [])
        self._addIntermediate("aggressiveRatioList", [])

    def calculate(self):
        aggressiveNumList = self.getIntermediate("aggressiveNumList")
        aggressiveNumList.append(self.aggressiveOrderNum.getLastFactorValue()[1])

        bidN = np.nansum(self._getLastNTickData("BidNum", 2)[0][:3])
        ratio = np.nansum(aggressiveNumList[-self.window:]) / bidN if bidN > 1e-4 else 0

        aggressiveRatioList = self.getIntermediate("aggressiveRatioList")
        aggressiveRatioList.append(ratio)

        fv = self.relative(aggressiveRatioList, self.lag1, self.lag2)

        self._addFactorValue(fv)

    @staticmethod
    def relative(l, w1, w2):
        length = len(l)
        ratio = w1 / w2
        w1 = min(max(1, int(length * ratio)), w1)

        mean2 = np.nanmean(l[-w2:])

        if (mean2 < 1e-6) or np.isnan(mean2):
            return 0
        else:
            return np.nanmean(l[-w1:]) / mean2
