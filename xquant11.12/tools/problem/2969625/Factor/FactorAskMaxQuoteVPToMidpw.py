from System.Factor import Factor
import numpy as np


class FactorAskMaxQuoteVPToMidpw(Factor):
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
        an = self._getLastTickData("AskNum")
        av = self._getLastTickData("AskVolume")
        ap = self._getLastTickData("AskPrice")
        maxp = self._getLastTickData("MaxPrice")
        midpw = self.__midpW.getLastFactorValue()

        if np.all(av > 1e-6) and np.all(ap > 1e-6):
            avn = av / an
            mqvp = ap[np.argmax(avn)]
        else:
            mqvp = maxp
        mqvps.append(mqvp)

        if midpw > 1e-4:
            factor_value = (mqvp / midpw - 1) * 1e2
        else:
            factor_value = 0.

        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
