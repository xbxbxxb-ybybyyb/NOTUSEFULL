from System.Factor import Factor
import numpy as np


class FactorAskNumVolumePKWPR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("NumWeightedPKPrice", [])
        self._addIntermediate("VolumeWeightedPKPrice", [])

    def calculate(self):

        nwpkp = self.getIntermediate("NumWeightedPKPrice")
        vwpkp = self.getIntermediate("VolumeWeightedPKPrice")
        ap = self._getLastTickData("AskPrice")
        av = self._getLastTickData("AskVolume")
        an = self._getLastTickData("AskNum")

        nwpkp.append(np.nansum(ap * an) / np.nansum(an))
        vwpkp.append(np.nansum(ap * av) / np.nansum(av))

        if np.nanmean(nwpkp[-self.__lag:]) > 1e-6:
            factorValue = (np.nanmean(vwpkp[-self.__lag:]) / np.nanmean(nwpkp[-self.__lag:]) - 1) * 1e3
        else:  # 涨停
            lastValue = self.getLastFactorValue()
            if lastValue is not None:
                factorValue = lastValue
            else:
                factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

