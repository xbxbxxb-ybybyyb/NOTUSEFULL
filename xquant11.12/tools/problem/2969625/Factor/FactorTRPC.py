from System.Factor import Factor
import numpy as np

class FactorTRPC(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__Lag = self._getParameter("Lag")
        self._addIntermediate("AvgTRPList", [])

    def calculate(self):
        avgTRPList = self.getIntermediate("AvgTRPList")
        transcations = self._getLastTickData("Transactions")
        previousClose = self._getLastTickData("PreviousClose")

        if transcations is None:
            if len(avgTRPList) > 0:
                avgTRPList.append(avgTRPList[-1])
            else:
                avgTRPList.append(previousClose)
        else:
            tradePrices = self._getTransactionData("Price", transcations)
            tradeVolume = self._getTransactionData("Volume", transcations)
            if np.sum(tradeVolume) < 0.01:
                if len(avgTRPList) > 0:
                    avgTRP = avgTRPList[-1]
                else:
                    avgTRP = previousClose
            else:
                avgTRP = np.sum(tradePrices * tradeVolume) / np.sum(tradeVolume)
            avgTRPList.append(avgTRP)

        localAvgTRPList = avgTRPList[-self.__Lag:]
        L = len(localAvgTRPList)
        if L < 5:
            factorValue = 0.
        else:
            factorValue = np.corrcoef(np.arange(L), localAvgTRPList)[0][1]
            if np.isnan(factorValue):
                factorValue = 0.

        lastFactorValue = self.getLastFactorValue()
        if lastFactorValue is not None:
            factorValue = 0.9*factorValue + 0.1*lastFactorValue

        self._addFactorValue(factorValue)