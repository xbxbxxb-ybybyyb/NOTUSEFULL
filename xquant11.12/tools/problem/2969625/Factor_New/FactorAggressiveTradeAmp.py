import numpy as np
from System.Factor import Factor


class FactorAggressiveTradeAmp(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("sLag")

        self._addIntermediate("RatioList", [])

    def calculate(self):
        ratioList = self.getIntermediate("RatioList")
        askP0 = self._getLastNTickData("AskPrice", 2)[0][0]
        bidP0 = self._getLastNTickData("BidPrice", 2)[0][0]
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            price = self._getTransactionData("Price", transaction)
            volume = self._getTransactionData("Volume", transaction)
            activeBuy = volume[(bsFlag == 1) & (price > askP0 - 1e-6)].sum()
            activeSell = volume[(bsFlag == 2) & (price < bidP0 + 1e-6)].sum()
            ratio = activeBuy - activeSell
        else:
            if len(ratioList) > 0:
                ratio = ratioList[-1]
            else:
                ratio = 0.

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







