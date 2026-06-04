import numpy as np
from System.Factor import Factor


class FactorPassiveOrderRatioRelBuy(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.window = self._getParameter("Window")
        self.lag1 = self._getParameter("Lag1")
        self.lag2 = self._getParameter("Lag2")

        self.passiveOrderNum = self._getFactor(
            {
                "ClassName": "PassiveOrderNum"
            }
        )

        self._addIntermediate("passiveNumList", [])
        self._addIntermediate("passiveRatioList", [])

    def calculate(self):
        passiveNumList = self.getIntermediate("passiveNumList")
        passiveNumList.append(self.passiveOrderNum.getLastFactorValue()[0])

        bidN = np.nansum(self._getLastNTickData("BidNum", 2)[0][:3])
        ratio = np.nansum(passiveNumList[-self.window:]) / bidN if bidN > 1e-4 else 0

        passiveRatioList = self.getIntermediate("passiveRatioList")
        passiveRatioList.append(ratio)

        fv = self.relative(passiveRatioList, self.lag1, self.lag2)

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
