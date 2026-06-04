import numpy as np
from System.Factor import Factor


class FactorAggressiveOrderRatioBuy(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.window = self._getParameter("Window")

        self.aggressiveOrderNum = self._getFactor(
            {
                "ClassName": "AggressiveOrderNum"
            }
        )

        self._addIntermediate("aggressiveNumList", [])

    def calculate(self):
        aggressiveNumList = self.getIntermediate("aggressiveNumList")
        aggressiveNumList.append(self.aggressiveOrderNum.getLastFactorValue()[0])

        askN = np.nansum(self._getLastNTickData("AskNum", 2)[0][:3])
        fv = np.nansum(aggressiveNumList[-self.window:]) / askN if askN > 1e-4 else 0

        self._addFactorValue(fv)
