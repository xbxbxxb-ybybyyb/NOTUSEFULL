#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorTransBidOrderPriceRet(Factor):
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
            bidPrice = np.nansum(amount[bsFlag == 1]) / np.nansum(volume[bsFlag == 1]) if \
                       np.nansum(volume[bsFlag == 1]) != 0 else np.nanmean(price)
            excessReturn  = (bidPrice / vwapPrice - 1.) * 1000 if vwapPrice > 1e-6 else 0.
            excessReturnList.append(excessReturn)
        else:
            excessReturnList.append(None)
        filterExcessReturnList = list(filter(lambda x: x is not None, excessReturnList))

        excessReturnSlice = np.array(filterExcessReturnList[-self.__lag:])
        if len(excessReturnSlice) > 0:
            factorValue = np.nanmax(excessReturnSlice) - np.nanmin(excessReturnSlice)
        else:
            factorValue = 0.

        self._addFactorValue(factorValue)





