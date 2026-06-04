from System.Factor import Factor
import numpy as np


class FactorAskIncremtActiveVolume(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__askVolumeDeltaSelfSide = self._getFactor(
            {
                "ClassName": "AskVolumeDeltaSelfSide",
            }
        )
        self.__askVolumeDeltaOtherSide = self._getFactor(
            {
                "ClassName": "AskVolumeDeltaOtherSide",
            }
        )
        self._addIntermediate("LLTs", [])

    def calculate(self):

        dvol = np.nanmean(self._getAllTodayTickData("Volume"))
        llts = self.getIntermediate("LLTs")
        askvs = self.__askVolumeDeltaSelfSide.getFactorValueList()[-3:]
        askos = self.__askVolumeDeltaOtherSide.getFactorValueList()[-3:]

        if dvol > 0:
            askactv = np.add(askvs, askos)
            filter_llts = list(filter(lambda x: x is not None, llts))
            if len(filter_llts) < 2:
                llts.append(askactv[-1])
            else:
                a = 2 / (1 + self.__lag)
                llt = (a - a * a / 4) * askactv[-1] + a * a / 2 * askactv[-2] - (a - 3 * a * a / 4) * askactv[-3] + \
                      2 * (1 - a) * filter_llts[-1] - (1 - a) ** 2 * filter_llts[-2]
                llts.append(llt)
            factorValue = llts[-1] / dvol
        else:
            llts.append(None)
            factorValue = 0.

        self._addFactorValue(factorValue)
