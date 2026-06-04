from System.Factor import Factor
import numpy as np


class FactorBidWeightedVolumeRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__svlag = self._getParameter("ShortVolumeLag")
        self.__lvlag = self._getParameter("LongVolumeLag")

        self._addIntermediate("BidWeightedVolume", [])

    def calculate(self):

        bidwv_list = self.getIntermediate("BidWeightedVolume")
        bidv = self._getLastTickData("BidVolume")
        w = np.linspace(0.1, 1, len(bidv))[::-1]
        bidwv = np.dot(bidv, w) / np.nansum(w)
        bidwv_list.append(bidwv)

        lm = np.nanmean(bidwv_list[-self.__lvlag:])
        if lm != 0:
            if len(bidwv_list) <= self.__svlag:
                sm = np.nanmean(bidwv_list[-(len(bidwv_list)//2):])
            else:
                sm = np.nanmean(bidwv_list[-self.__svlag:])
            factorValue = sm / lm
        else:
            lastValue = self.getLastFactorValue()
            if lastValue is not None:
                factorValue = lastValue
            else:
                factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
