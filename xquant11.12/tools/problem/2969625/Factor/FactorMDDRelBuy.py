import numpy as np
from System.Factor import Factor


class FactorMDDRelBuy(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.lag1 = self._getParameter("Lag1")
        self.lag2 = self._getParameter("Lag2")

        self._addIntermediate("askP1List", [])
        self._addIntermediate("mddList", [])

    def calculate(self):
        askP1List = self.getIntermediate("askP1List")
        mddList = self.getIntermediate("mddList")

        maxP = self._getLastTickData("MaxPrice")
        askP1 = self._getLastTickData("AskPrice")[0]
        if askP1 <= 0:
            askP1 = maxP
        askP1List.append(askP1)

        mdd, j, i = self.mdd(askP1List[-self.lag2:])
        mddList.append(mdd)

        fv = self.relative(mddList, self.lag1, self.lag2)

        self._addFactorValue(fv)

    @staticmethod
    def mdd(l1):  # 最大回撤
        i = np.argmax((np.maximum.accumulate(l1) - np.array(l1)))
        if i == 0:
            return 0, 0, 0
        j = np.argmax(l1[:i])
        return l1[j] - l1[i], j, i

    @staticmethod
    def relative(l, w1, w2):
        length = len(l)
        ratio = w1 / w2
        w1 = min(max(1, int(length * ratio)), w1)

        mean2 = np.nanmean(l[-w2:])

        if mean2 == 0 or np.isnan(mean2):
            return 0
        else:
            return np.nanmean(l[-w1:]) / mean2
