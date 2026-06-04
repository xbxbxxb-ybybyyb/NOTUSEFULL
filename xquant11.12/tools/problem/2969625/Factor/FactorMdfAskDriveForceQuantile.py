import numpy as np
from System.Factor import Factor


class FactorMdfAskDriveForceQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__level = self._getParameter("Level")
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("SLag")

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
        askDriveForceList.append(askDriveForce)

        askDriveForceSlice = np.array(askDriveForceList[-self.__lag:])
        if len(askDriveForceSlice) < 1:
            factorValue = 0.
        else:
            factorValue = sum(askDriveForceSlice < askDriveForceSlice[-1]) / len(askDriveForceSlice)

        factorValueList = self.getFactorValueList()
        factorValue = self._EMA_calculate(factorValue, factorValueList, self.__sLag)

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])