#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor
from scipy.fftpack import fft


class FactorCBTransPriceAngle(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("AskPriceList", [])
        self._addIntermediate("BidPriceList", [])
        self._addIntermediate("AskPriceAngleList", [])
        self._addIntermediate("BidPriceAngleList", [])

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
                askPrice = np.nansum(amount[bsFlag == 2]) / np.nansum(volume[bsFlag == 2])  # 卖方成交均价
                askPriceList.append(askPrice)
            else:
                askPriceList.append(None)

            if np.nansum(volume[bsFlag == 1]) != 0:
                bidPrice = np.nansum(amount[bsFlag == 1]) / np.nansum(volume[bsFlag == 1])  # 买方成交均价
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
        askFactorValue = np.angle(fft(askPriceSlice))[-1] if len(askPriceSlice) > 3 else 0.
        bidFactorValue = np.angle(fft(bidPriceSlice))[-1] if len(bidPriceSlice) > 3 else 0.

        askPriceAngleList = self.getIntermediate("AskPriceAngleList")
        askFactorValue = self._EMA_calculate(askFactorValue, askPriceAngleList, self.__lag)
        askPriceAngleList.append(askFactorValue)

        bidPriceAngleList = self.getIntermediate("BidPriceAngleList")
        bidFactorValue = self._EMA_calculate(bidFactorValue, bidPriceAngleList, self.__lag)
        bidPriceAngleList.append(bidFactorValue)

        factorValue = (askFactorValue + bidFactorValue) / 2.

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])




