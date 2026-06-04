from System.Factor import Factor
import numpy as np


class FactorBidMaxQuoteVPToMidpw(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__midpW = self._getFactor(
            {
                "ClassName": "MidPriceWeighted",
                "Parameters": {
                    "Grade": 1,
                }
            }
        )

        self._addIntermediate("MaxQuoteVolumePrice", [])

    def calculate(self):

        mqvps = self.getIntermediate("MaxQuoteVolumePrice")
        bn = self._getLastTickData("BidNum")
        bv = self._getLastTickData("BidVolume")
        bp = self._getLastTickData("BidPrice")
        minp = self._getLastTickData("MinPrice")
        midpw = self.__midpW.getLastFactorValue()

        if np.all(bv > 1e-6) and np.all(bp > 1e-6):
            bvn = bv / bn
            mqvp = bp[np.argmax(bvn)]
        else:
            mqvp = minp
        mqvps.append(mqvp)

        if midpw > 1e-4:
            factor_value = (mqvp / midpw - 1) * 1e2
        else:
            factor_value = 0.

        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
