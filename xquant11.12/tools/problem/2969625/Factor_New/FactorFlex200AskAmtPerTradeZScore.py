from System.Factor import Factor
import numpy as np


class FactorFlex200AskAmtPerTradeZScore(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
        self.__longWindow = self._getParameter("LongWindow")

        self._addIntermediate("AskAmountList", [])
        
    def calculate(self):
        amt = self._getLastNTickData('Amount', self.__longWindow)
        avg_amt = np.nanmean(amt)
        std_amt = np.nanstd(amt)
        transaction = self._getLastTickData('Transactions')
        if transaction is None:
            value = 0.
        else:
            value = self.__getAskAmt(transaction)
        askAmountList = self.getIntermediate("AskAmountList")
        askAmountList.append(value)
        if len(amt) >= self.__longWindow:
            avg_tickamt = np.nanmean(np.array(askAmountList[-self.__window:]))
        else:
            window_change = max(int(self.__longWindow/10), 1)
            avg_tickamt = np.nanmean(np.array(askAmountList[-window_change:]))
        if (len(amt) == 0) or (len(askAmountList) == 0):
            res = 0.
        else:
            if std_amt < 1e-6:
                res = 0.
            else:
                res = (avg_tickamt - avg_amt) / std_amt

        self._addFactorValue(res)

    def __getAskAmt(self, transaction):
        BSFlag = self._getTransactionData("BSFlag", transaction)
        volumeData = self._getTransactionData("Volume", transaction)
        priceData = self._getTransactionData("Price", transaction)
        timestampData = self._getTransactionData("Timestamp", transaction)
        amountData = volumeData * priceData
        if (BSFlag == 2).sum() == 0:
            return 0
        else:
            weight_amt = np.power(np.e, (timestampData * 1000 - timestampData[-1] * 1000 ) / 1000) * amountData
            ask_amt_per_trans = (weight_amt[BSFlag == 2]).sum()
            return ask_amt_per_trans











