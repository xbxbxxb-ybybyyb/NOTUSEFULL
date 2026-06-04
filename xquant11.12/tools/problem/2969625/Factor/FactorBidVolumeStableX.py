import numpy as np
from System.Factor import Factor


class FactorBidVolumeStableX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("sLag")

        self._addIntermediate("BidVolumeList", [])

    def calculate(self):
        bidVolumeArray = self._getLastTickData("BidVolume")
        bidVolume = np.nansum(bidVolumeArray)
        bidVolumeList = self.getIntermediate("BidVolumeList")
        bidVolumeList.append(bidVolume)

        bidVolumeSlice = np.array(bidVolumeList[-self.__lag:])
        if len(bidVolumeSlice) < 5:
            factorValue = 0
        else:
            bidVolumeStd = np.nanstd(bidVolumeSlice)
            if bidVolumeStd > 1e-4:
                factorValue = (bidVolumeSlice[-1] - np.nanmean(bidVolumeSlice[-self.__sLag:])) / bidVolumeStd * 100
            else:
                lastFactorValue = self.getLastFactorValue()
                if lastFactorValue is not None:
                    factorValue = lastFactorValue
                else:
                    factorValue = 0.

        self._addFactorValue(factorValue)



