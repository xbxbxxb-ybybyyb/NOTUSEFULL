import numpy as np
from System.Factor import Factor


class FactorMdfFlex20BidAmtPerTradeZScore(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
        self.__longWindow = self._getParameter("LongWindow")

        self._addIntermediate("BidAmountList", [])
    
    def calculate(self):
        amount = self._getLastNTickData("Amount", self.__longWindow)
        transaction = self._getLastTickData("Transactions")
        if transaction is None:
            value = 0.
        else:
            value = self.__getBidAmt(transaction)
        bidAmountList = self.getIntermediate("BidAmountList")
        bidAmountList.append(value)
        bidAmountSlice = np.array(bidAmountList[-self.__window:])
        bidAmountMean = np.nanmean(bidAmountSlice)
        amountStd = np.nanstd(amount)
        if amountStd < 1e-6:
            factorValue = 0.
        else:
            factorValue = (bidAmountMean - np.nanmean(amount)) / amountStd
        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    def __getBidAmt(self, transaction):
        BSFlag = self._getTransactionData("BSFlag", transaction)
        volumeData = self._getTransactionData("Volume", transaction)
        priceData = self._getTransactionData("Price", transaction)
        amountData = volumeData * priceData
        if (BSFlag == 1).sum() == 0:
            return 0
        else:
            return amountData[BSFlag == 1].sum()











