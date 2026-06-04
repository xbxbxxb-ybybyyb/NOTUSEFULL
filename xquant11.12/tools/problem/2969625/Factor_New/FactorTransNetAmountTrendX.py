import numpy as np
from System.Factor import Factor


class FactorTransNetAmountTrendX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("sLag")

        self._addIntermediate("RatioList", [])

    def calculate(self):
        ratioList = self.getIntermediate("RatioList")
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            volume = self._getTransactionData("Volume", transaction)
            price = self._getTransactionData("Price", transaction)
            amount = price * volume
            bidV = np.nansum(amount[bsFlag == 1])
            askV = np.nansum(amount[bsFlag == 2])
            ratio = (bidV - askV)
        else:
            ratio = 0 if len(ratioList) == 0 else ratioList[-1]
        ratioList.append(ratio)

        if len(ratioList) < min(3, self.__sLag):
            factorValue = 0.
        else:
            factorValue = self.amplify_zcore(ratioList, self.__sLag, self.__lag) * 100

        self._addFactorValue(factorValue)

    @staticmethod
    def amplify_zcore(valueList, sLag, lag):
        size = len(valueList)
        sLag = min(max(1, int(size * sLag / lag)), sLag)
        std = np.nanstd(valueList)
        if std < 1e-6 or np.isnan(std):
            return 0
        else:
            return (np.nanmean(valueList[-sLag:]) - np.nanmean(valueList[-lag:])) / std




