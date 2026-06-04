from System.Factor import Factor
import numpy as np


class FactorAskBidVolumeRatioOtherSides(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__bidVolumeDeltaOtherSide = self._getFactor(
            {
                "ClassName": "BidVolumeDeltaOtherSide",
            }
        )
        self.__askVolumeDeltaOtherSide = self._getFactor(
            {
                "ClassName": "AskVolumeDeltaOtherSide",
            }
        )
        self._addIntermediate("LLTs", [])

    def calculate(self):

        llts = self.getIntermediate("LLTs")
        bidos = self.__bidVolumeDeltaOtherSide.getFactorValueList()[-3:]
        askos = self.__askVolumeDeltaOtherSide.getFactorValueList()[-3:]
        abovr = np.array(bidos) / np.add(bidos, askos)
        np.place(abovr, np.isnan(abovr), 0)  # nan对应该tick完全没有成交

        if len(llts) < 2:
            llts.append(abovr[-1])
        else:
            a = 2 / (1 + self.__lag)
            llt = (a - a * a / 4) * abovr[-1] + a * a / 2 * abovr[-2] - (a - 3 * a * a / 4) * abovr[-3] + \
                  2 * (1 - a) * llts[-1] - (1 - a) ** 2 * llts[-2]
            llts.append(llt)
        factorValue = llts[-1]

        self._addFactorValue(factorValue)
