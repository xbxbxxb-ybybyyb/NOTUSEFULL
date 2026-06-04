import numpy as np
from System.Factor import Factor


class FactorAskDriveForceQuantileX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__level = self._getParameter("Level")
        self.__window = self._getParameter("Window")
        self.__lag = self._getParameter("Lag")

        self.__driveForce = self._getFactor(
            {
                "ClassName": "OrderDriveForce",
                "Parameters": {
                    "Level": self.__level
                }
            }
        )
        self._addIntermediate("askDriveForceList", [])

    def calculate(self):
        _, askDriveForce = self.__driveForce.getLastFactorValue()

        askDriveForceList = self.getIntermediate("askDriveForceList")
        askDriveForce = self._EMA_calculate(askDriveForce, askDriveForceList, self.__lag)
        askDriveForceList.append(askDriveForce)

        askDriveForceSlice = np.array(askDriveForceList[-self.__window:])
        if len(askDriveForceSlice) < 5:
            factorValue = 0.
        else:
            factorValue = - np.sum(askDriveForceSlice < askDriveForceSlice[-1]) / len(askDriveForceSlice) + 0.5

        factorValueList = self.getFactorValueList()
        factorValue = self._EMA_calculate(factorValue, factorValueList, self.__lag)

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])