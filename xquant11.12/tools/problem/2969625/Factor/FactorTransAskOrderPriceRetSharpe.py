#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorTransAskOrderPriceRetSharpe(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__vwapPrice = self._getFactor(
            {
                "ClassName": "AvePrice"
            }
        )
        self._addIntermediate("ExcessReturnList", [])

    def calculate(self):
        excessReturnList = self.getIntermediate("ExcessReturnList")
        vwapPrice = self.__vwapPrice.getLastFactorValue()

        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            volume = self._getTransactionData("Volume", transaction)
            price = self._getTransactionData("Price", transaction)
            amount = volume * price
            askPrice = np.nansum(amount[bsFlag == 2]) / np.nansum(volume[bsFlag == 2]) if \
                       np.nansum(volume[bsFlag == 2]) != 0 else np.nanmean(price)
            excessReturn  = (askPrice / vwapPrice - 1.) * 1000
            excessReturnList.append(excessReturn)
        else:
            excessReturnList.append(None)
        filterExcessReturnList = list(filter(lambda x: x is not None, excessReturnList))

        excessReturnSlice = np.array(filterExcessReturnList[-self.__lag:])
        if len(excessReturnSlice) > 0 and np.nanstd(excessReturnSlice) > 1e-6:
            factorValue = np.nanmean(excessReturnSlice) / np.nanstd(excessReturnSlice)
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)





