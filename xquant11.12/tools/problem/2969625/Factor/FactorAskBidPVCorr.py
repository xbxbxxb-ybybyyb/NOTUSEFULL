import numpy as np
from System.Factor import Factor


class FactorAskBidPVCorr(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lookback = self._getParameter("LookBack")
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("AskPriceList", [])
        self._addIntermediate("AskVolumeList", [])
        self._addIntermediate("BidPriceList", [])
        self._addIntermediate("BidVolumeList", [])

    def calculate(self):
        askVolume = self._getLastTickData("AskVolume")
        askPrice = self._getLastTickData("AskPrice")
        bidVolume = self._getLastTickData("BidVolume")
        bidPrice = self._getLastTickData("BidPrice")

        AskPriceList = self.getIntermediate("AskPriceList")
        AskVolumeList = self.getIntermediate("AskVolumeList")
        AskPriceList.append(askPrice[0])
        AskVolumeList.append(askVolume[0])

        BidPriceList = self.getIntermediate("BidPriceList")
        BidVolumeList = self.getIntermediate("BidVolumeList")
        BidPriceList.append(bidPrice[0])
        BidVolumeList.append(bidVolume[0])

        bidCorr = np.corrcoef(BidPriceList[-self.__lookback:], BidVolumeList[-self.__lookback:])[0, 1]
        askCorr = np.corrcoef(AskPriceList[-self.__lookback:], AskVolumeList[-self.__lookback:])[0, 1]
        if len(BidPriceList[-self.__lookback:]) > 1:
            if np.isnan(bidCorr) and np.isnan(askCorr):
                factorValue = 0.
            elif np.isnan(bidCorr):
                factorValue = askCorr
            elif np.isnan(askCorr):
                factorValue = bidCorr
            else:
                factorValue = bidCorr + askCorr
        else:
            factorValue = 0.

        factorValueList = self.getFactorValueList()
        factorValue = self._EMA_calculate(factorValue, factorValueList, self.__lag)

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])

