import math
from System.Factor import Factor


class OrderVolumePressure(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__numOrderMax = self._getParameter("NumOrderMax")
        self.__numOrderMin = self._getParameter("NumOrderMin")
        self.__weightDecay = self._getParameter("WeightDecay")

        self.__aveOrderVolumeWeighted = self._getFactor(
            {
                "ClassName": "AveOrderVolumeWeightedM",
                "Parameters": {
                    "NumOrderMax": self.__numOrderMax,
                    "NumOrderMin": self.__numOrderMin,
                    "WeightDecay": self.__weightDecay
                }
            }
        )

    def calculate(self):
        aveVolumeBid, aveVolumeAsk = self.__aveOrderVolumeWeighted.getLastFactorValue()

        if aveVolumeBid == 0 or aveVolumeAsk == 0:
            factorValue = 0
        else:
            factorValue = math.log(aveVolumeAsk) - math.log(aveVolumeBid)

        self._addFactorValue(factorValue)
