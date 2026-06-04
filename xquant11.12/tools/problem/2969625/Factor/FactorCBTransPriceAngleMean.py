#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from scipy.fftpack import fft
from System.Factor import Factor


class FactorCBTransPriceAngleMean(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("AskPriceList", [])
        self._addIntermediate("BidPriceList", [])

    def calculate(self):
        askPriceList = self.getIntermediate("AskPriceList")
        bidPriceList = self.getIntermediate("BidPriceList")
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            price = self._getTransactionData("Price", transaction)
            volume = self._getTransactionData("Volume", transaction)
            amount = price * volume
            if np.nansum(volume[bsFlag == 2]) != 0:
                askPrice = np.nansum(amount[bsFlag == 2]) / np.nansum(volume[bsFlag == 2])
                askPriceList.append(askPrice)
            else:
                askPriceList.append(None)

            if np.nansum(volume[bsFlag == 1]) != 0:
                bidPrice = np.nansum(amount[bsFlag == 1]) / np.nansum(volume[bsFlag == 1])
                bidPriceList.append(bidPrice)
            else:
                bidPriceList.append(None)
        else:
            askPriceList.append(None)
            bidPriceList.append(None)
        filterAskPriceList = list(filter(lambda x: x is not None, askPriceList))
        filterBidPriceList= list(filter(lambda x: x is not None, bidPriceList))

        askPriceSlice = np.array(filterAskPriceList)
        bidPriceSlice = np.array(filterBidPriceList)

        if len(askPriceSlice) > 3:
            lookBack = self.__lag if self.__lag < len(askPriceSlice) else 3
            askFactorValue = np.nanmean(np.angle(fft(askPriceSlice))[-lookBack:])
        else:
            askFactorValue = 0.

        if len(bidPriceSlice) > 3:
            lookBack = self.__lag if self.__lag < len(bidPriceSlice) else 3
            bidFactorValue = np.nanmean(np.angle(fft(bidPriceSlice))[-lookBack:])
        else:
            bidFactorValue = 0.

        factorValue = (askFactorValue + bidFactorValue) / 2.

        self._addFactorValue(factorValue)




