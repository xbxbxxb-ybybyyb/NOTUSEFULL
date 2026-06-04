from System.Factor import Factor
import numpy as np


class FactorMaxQuoteVNAskPToMidP(Factor):
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

        if midpw > 1e-4:
            factorValue = (mqvp / midpw - 1) * 1e2
        else:
            factorValue = 0.4

        self._addFactorValue(factorValue)

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x
