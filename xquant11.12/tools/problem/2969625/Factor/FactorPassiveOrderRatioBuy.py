import numpy as np
from System.Factor import Factor


class FactorPassiveOrderRatioBuy(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.window = self._getParameter("Window")

        self.passiveOrderNum = self._getFactor(
            {
                "ClassName": "PassiveOrderNum"
            }
        )

        self._addIntermediate("passiveNumList", [])

    def calculate(self):
        passiveNumList = self.getIntermediate("passiveNumList")
        passiveNumList.append(self.passiveOrderNum.getLastFactorValue()[0])

        bidN = np.nansum(self._getLastNTickData("BidNum", 2)[0][:3])
        fv = np.sum(passiveNumList[-self.window:]) / bidN if bidN > 1e-4 else 0

        self._addFactorValue(fv)
