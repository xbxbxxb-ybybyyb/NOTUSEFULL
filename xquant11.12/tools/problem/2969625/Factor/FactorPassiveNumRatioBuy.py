import numpy as np
from System.Factor import Factor


class FactorPassiveNumRatioBuy(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.lag1 = self._getParameter("Lag1")
        self.lag2 = self._getParameter("Lag2")

        self.aggressiveOrderNum = self._getFactor(
            {
                "ClassName": "AggressiveOrderNum"
            }
        )
        self._addIntermediate("passiveRatioList", [])

    def calculate(self):
        passiveRatioList = self.getIntermediate("passiveRatioList")

        askN = np.nansum(self._getLastNTickData("AskNum", 2)[0][:2])
        passiveRatioList.append(self.aggressiveOrderNum.getLastFactorValue()[2] / askN if askN > 1e-4 else np.nan)

        fv = self.relative(passiveRatioList, self.lag1, self.lag2)
        if np.isnan(fv):
            fv = 0

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
