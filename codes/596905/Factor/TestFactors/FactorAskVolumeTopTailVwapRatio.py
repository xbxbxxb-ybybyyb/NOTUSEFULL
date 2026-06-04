#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorAskVolumeTopTailVwapRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self.__vwapPrice = self._getFactor(
            {
                "ClassName": "AvePrice"
            }
        )
        self._addIntermediate("TickVolumeList", [])
        self._addIntermediate("TickAmountList", [])
        self._addIntermediate("TransVolumeList", [])

    def calculate(self):
        vwap = self.__vwapPrice.getLastFactorValue()
        volume = self._getLastTickData("Volume")
        amount = self._getLastTickData("Amount")

        tickVolumeList = self.getIntermediate("TickVolumeList")
        tickAmountList = self.getIntermediate("TickAmountList")
        transVolumeList = self.getIntermediate("TransVolumeList")

        if len(tickVolumeList) == 0:
            transactionData = self._getAllHistoricalTickData("Transactions")
            for transaction in transactionData:
                if transaction is not None:
                    bsFlag = self._getTransactionData("BSFlag", transaction)
                    transactionVolume = self._getTransactionData("Volume", transaction)
                    hisTransVolume = np.nansum(transactionVolume[bsFlag == 2])
                    transVolumeList.append(hisTransVolume)
                else:
                    transVolumeList.append(0.)

            hisVolume = self._getAllHistoricalTickData("Volume")
            hisAmount = self._getAllHistoricalTickData("Amount")
            tickVolumeList.extend(hisVolume)
            tickAmountList.extend(hisAmount)

        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            transactionVolume = self._getTransactionData("Volume", transaction)
            transVolume = np.nansum(transactionVolume[bsFlag == 2])
            transVolumeList.append(transVolume)
        else:
            transVolumeList.append(0.)

        tickAmountList.append(amount)
        tickVolumeList.append(volume)

        volumeSlice = np.array(tickVolumeList[-self.__window:])
        amountSlice = np.array(tickAmountList[-self.__window:])
        transVolumeSlice = np.array(transVolumeList[-self.__window:])
        top = transVolumeSlice > np.nanpercentile(transVolumeSlice, 90)
        tail = transVolumeSlice < np.nanpercentile(transVolumeSlice, 10)
        vwapTop = np.nansum(amountSlice[top]) / np.nansum(volumeSlice[top]) if np.nansum(volumeSlice[top]) != 0 else vwap
        vwapTail = np.nansum(amountSlice[tail]) / np.nansum(volumeSlice[tail]) if np.nansum(volumeSlice[tail]) != 0 else vwap

        if vwapTail != 0:
            factorValue = vwapTop / vwapTail
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)




