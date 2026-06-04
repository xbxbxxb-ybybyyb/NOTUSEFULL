import numpy as np
from System.Factor import Factor


class FactorBidVolumeStable(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("ShortLag")

        self._addIntermediate("BidVolumeList", [])

    def calculate(self):
        bidVolumeArray = self._getLastTickData("BidVolume")
        bidVolume = np.nansum(bidVolumeArray)
        bidVolumeList = self.getIntermediate("BidVolumeList")
        bidVolumeList.append(bidVolume)

        bidVolumeSlice = np.array(bidVolumeList[-self.__lag:])
        bidVolumeStd = np.nanstd(bidVolumeSlice)
        if bidVolumeStd > 1e-6:
            factorValue = (bidVolumeSlice[-1] - np.nanmean(bidVolumeSlice[-self.__sLag:])) / bidVolumeStd
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)



