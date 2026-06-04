from System.Factor import Factor
import numpy as np


class FactorMaxQuoteVNBidPToMidP(Factor):
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

    def calculate(self):
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

        if midpw > 1e-4:
            factor_value = (mqvp / midpw - 1) * 1e2
        else:
            factor_value = 0.4

        self._addFactorValue(factor_value)
