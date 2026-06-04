from System.Factor import Factor
import numpy as np


class FactorBidDealDiff(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        transaction = self._getLastTickData("Transactions")
        flag = 0
        factorValue = 0
        if transaction is not None:
            BSFlag = self._getTransactionData("BSFlag", transaction)
            priceData = self._getTransactionData("Price", transaction)
            volumeData = self._getTransactionData("Volume", transaction)
            priceData = priceData[BSFlag == 1]
            volumeData = volumeData[BSFlag == 1]
            if np.nansum(volumeData) > 0:
                bid_dealp_w = np.nansum(priceData * volumeData) / np.nansum(volumeData)
                bidp0 = self._getLastTickData("BidPrice")[0]
                midp = self.__midPrice.getLastFactorValue()
                factorValue = bidp0 / bid_dealp_w + (bidp0 - bid_dealp_w) / midp
            else:
                flag = 1
        else:
            flag = 1

        if flag == 1:
            lastValue = self.getLastFactorValue()
            if lastValue is not None:
                factorValue = lastValue
            else:
                factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

