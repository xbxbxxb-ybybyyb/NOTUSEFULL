import numpy as np
from System.Factor import Factor


class FactorAskVolumeStableX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("sLag")

        self._addIntermediate("AskVolumeList", [])

    def calculate(self):
        askVolumeArray = self._getLastTickData("AskVolume")
        askVolume = np.nansum(askVolumeArray)
        askVolumeList = self.getIntermediate("AskVolumeList")
        askVolumeList.append(askVolume)

        askVolumeSlice = np.array(askVolumeList[-self.__lag:])
        if len(askVolumeSlice) < 5:
            factorValue = 0.
        else:
            askVolumeStd = np.nanstd(askVolumeSlice)
            if askVolumeStd > 1e-6:
                factorValue = - (askVolumeSlice[-1] - np.nanmean(askVolumeSlice[-self.__sLag:])) / askVolumeStd * 100
            else:
                lastFactorValue = self.getLastFactorValue()
                if lastFactorValue is not None:
                    factorValue = lastFactorValue
                else:
                    factorValue = 0.

        self._addFactorValue(factorValue)



