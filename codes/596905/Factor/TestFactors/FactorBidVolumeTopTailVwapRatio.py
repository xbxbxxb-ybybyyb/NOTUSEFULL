#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorBidVolumeTopTailVwapRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self.__vwapPrice = self._getFactor(
            {
                "ClassName": "AvePrice"
            }
        )
        self._addIntermediate("VolumeList", [])
        self._addIntermediate("AmountList", [])

    def calculate(self):
        vwap = self.__vwapPrice.getLastFactorValue()
        volumeList = self.getIntermediate("VolumeList")
        amountList = self.getIntermediate("AmountList")

        if len(volumeList) == 0:
            transactionData = self._getAllHistoricalTickData("Transactions")
            for transaction in transactionData:
                if transaction is not None:
                    bsFlag = self._getTransactionData("BSFlag", transaction)
                    transactionPrice = self._getTransactionData("Price", transaction)
                    transactionVolume = self._getTransactionData("Volume", transaction)
                    transactionAmount = transactionPrice * transactionVolume
                    hisVolume = np.nansum(transactionVolume[bsFlag == 1])
                    hisAmount = np.nansum(transactionAmount[bsFlag == 1])
                    amountList.append(hisVolume)
                    volumeList.append(hisAmount)

        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            transactionPrice = self._getTransactionData("Price", transaction)
            transactionVolume = self._getTransactionData("Volume", transaction)
            transactionAmount = transactionPrice * transactionVolume
            volume = np.nansum(transactionVolume[bsFlag == 1])
            amount = np.nansum(transactionAmount[bsFlag == 1])
            amountList.append(amount)
            volumeList.append(volume)

        volumeSlice = np.array(volumeList[-self.__window:])
        amountSlice = np.array(amountList[-self.__window:])
        top = volumeSlice > np.nanpercentile(volumeSlice, 90)
        tail = volumeSlice < np.nanpercentile(volumeSlice, 10)
        vwapTop = np.nansum(amountSlice[top]) / np.nansum(volumeSlice[top]) if np.nansum(volumeSlice[top]) != 0 else vwap
        vwapTail = np.nansum(amountSlice[tail]) / np.nansum(volumeSlice[tail]) if np.nansum(volumeSlice[tail]) != 0 else vwap

        if vwapTop != 0:
            factorValue = vwapTail / vwapTop
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)




