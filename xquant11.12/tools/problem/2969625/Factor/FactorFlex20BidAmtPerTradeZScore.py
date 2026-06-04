from System.Factor import Factor
import numpy as np


class FactorFlex20BidAmtPerTradeZScore(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
        self.__longWindow = self._getParameter("LongWindow")

        self._addIntermediate("BidAmountList", [])
    
    def calculate(self):
        amt = self._getLastNTickData('Amount', self.__longWindow)
        avg_amt = np.nanmean(amt)
        std_amt = np.nanstd(amt)
        transaction = self._getLastTickData('Transactions')
        if transaction is None:
            value = 0.
        else:
            value = self.__getBidAmt(transaction)
        bidAmountList = self.getIntermediate("BidAmountList")
        bidAmountList.append(value)
        avg_tickamt = np.nanmean(np.array(bidAmountList[-self.__window:]))
        if std_amt == 0:
            res = 0.
        else:
            res = (avg_tickamt - avg_amt) / std_amt
        if np.isnan(res):
            res = 0.

        self._addFactorValue(res)

    def __getBidAmt(self, transaction):
        BSFlag = self._getTransactionData("BSFlag", transaction)
        volumeData = self._getTransactionData("Volume", transaction)
        priceData = self._getTransactionData("Price", transaction)
        timestampData = self._getTransactionData("Timestamp", transaction)
        amountData = volumeData * priceData
        if (BSFlag == 1).sum() == 0:
            return 0
        else:
            weight_amt = np.power(np.e, ( timestampData * 1000 - timestampData[-1] * 1000 ) / 1000 ) * amountData
            bid_amt_per_trans = (weight_amt[BSFlag == 1]).sum()
            return bid_amt_per_trans











