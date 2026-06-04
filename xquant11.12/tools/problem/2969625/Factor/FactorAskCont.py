import numpy as np
from System.Factor import Factor


class FactorAskCont(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self._addIntermediate("askP1List", [])

    def calculate(self):
        maxP = self._getLastTickData("MaxPrice")
        askP1 = self._getLastTickData("AskPrice")[0]
        if askP1 <= 0:
            askP1 = maxP

        askP1List = self.getIntermediate("askP1List")
        askP1List.append(askP1)

        askSign = np.diff([askP1List[0]] + askP1List)
        askSign = np.sign(askSign)

        if len(askSign) < 2:
            fv = 0
        else:
            fv = np.corrcoef(np.cumsum(askSign), np.arange(len(askSign)))[0, 1]
        if np.isnan(fv):
            fv = 0

        self._addFactorValue(fv)
