import numpy as np
from System.Factor import Factor


class FactorPassiveOrderRatioSell(Factor):
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
        passiveNumList.append(self.passiveOrderNum.getLastFactorValue()[1])

        askN = np.nansum(self._getLastNTickData("AskNum", 2)[0][:3])
        fv = np.sum(passiveNumList[-self.window:]) / askN if askN > 1e-4 else 0

        self._addFactorValue(fv)
