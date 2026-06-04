from System.Factor import Factor
import numpy as np


class FactorMinuteTurnStrength(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("MidPriceWeighted", [])

    def calculate(self):

        midpw = self.getIntermediate("MidPriceWeighted")

        askp = self._getLastNTickData("AskPrice", 1)
        askv = self._getLastNTickData("AskVolume", 1)
        bidp = self._getLastNTickData("BidPrice", 1)
        bidv = self._getLastNTickData("BidVolume", 1)
        if len(askp) > 0:
            midpw.append((askp[-1][0] * askv[-1][0] + bidp[-1][0] * bidv[-1][0]) / (askv[-1][0] + bidv[-1][0]))
        else:
            midpw.append(None)

        sub_midpw = [each for each in midpw if each is not None][::-1]

        if len(sub_midpw) > self.__lag + 1:
            direction = np.sign(sub_midpw[0] - sub_midpw[self.__lag])
            p = 0
            for i in range(self.__lag, len(sub_midpw), self.__lag):
                p = int(min(i + self.__lag, len(sub_midpw) - 1))
                if np.sign(sub_midpw[i] - sub_midpw[p]) != direction:
                    p = i
                    break
            factorValue = (sub_midpw[0] / sub_midpw[p] - 1) * 1e2

        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)
