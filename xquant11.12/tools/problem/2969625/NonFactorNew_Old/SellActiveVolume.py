import numpy as np
from System.Factor import Factor


class SellActiveVolume(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        transactions = self._getLastNTickData("Transactions", self.__lag - 1)
        tranPrice = [self._getTransactionData("Price", tran) for tran in transactions if tran is not None]
        tranVolume = [self._getTransactionData("Volume", tran) for tran in transactions if tran is not None]

        if len(tranPrice) == 0:
            self._addFactorValue(0)
            return

        tranPrice = np.concatenate(tranPrice)
        tranVolume = np.concatenate(tranVolume)

        askP0 = self._getLastNTickData("AskPrice", self.__lag)[0][0]
        maxP = self._getLastTickData("MaxPrice")
        if askP0 == 0:
            askP0 = maxP
        aSellVolume = tranVolume[tranPrice < askP0].sum()

        self._addFactorValue(aSellVolume)
