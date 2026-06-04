from System.Factor import Factor
import numpy as np


class FactorOrderVolumeAboveAve(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__numOrderMax = self._getParameter("NumOrderMax")
        self.__numOrderMin = self._getParameter("NumOrderMin")
        self.__weightDecay = self._getParameter("WeightDecay")
        self.__lag = self._getParameter("Lag")

        self.__emaOrderVolumePressure = self._getFactor(
            {
                "ClassName": "OrderVolumePressure",
                "Parameters": {
                    "NumOrderMax": self.__numOrderMax,
                    "NumOrderMin": self.__numOrderMin,
                    "WeightDecay": self.__weightDecay
                }
            }
        )

    def calculate(self):
        ValueList = self.__emaOrderVolumePressure.getFactorValueList()[-self.__lag:]
        factorValue = -ValueList[-1] + np.nanmean(ValueList)
        self._addFactorValue(factorValue)
