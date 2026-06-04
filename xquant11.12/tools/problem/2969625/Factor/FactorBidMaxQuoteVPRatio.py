from System.Factor import Factor
import numpy as np


class FactorBidMaxQuoteVPRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("MaxQuoteVolumePrice", [])

    def calculate(self):

        mqvps = self.getIntermediate("MaxQuoteVolumePrice")
        bn = self._getLastTickData("BidNum")
        bv = self._getLastTickData("BidVolume")
        bp = self._getLastTickData("BidPrice")
        minp = self._getLastTickData("MinPrice")

        if np.all(bv > 1e-6) and np.all(bp > 1e-6):
            bvn = bv / bn
            mqvp = bp[np.argmax(bvn)]
        else:
            mqvp = minp
        mqvps.append(mqvp)

        sub_mqvps = mqvps[-self.__lag:]
        if mqvps[-1] > 1e-6:
            factor_value = (np.nanmean(np.subtract(sub_mqvps, mqvps[-1])) / mqvps[-1]) * 1e2
        else:
            factor_value = (np.nanmean(np.subtract(sub_mqvps, mqvps[-1])) / minp) * 1e2

        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
