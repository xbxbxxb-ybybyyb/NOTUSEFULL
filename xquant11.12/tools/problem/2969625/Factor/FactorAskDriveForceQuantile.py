import numpy as np
from System.Factor import Factor


class FactorAskDriveForceQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__level = self._getParameter("Level")
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
        askDriveForceList.append(askDriveForce)

        askDriveForceSlice = np.array(askDriveForceList[-self.__lag:])
        if len(askDriveForceSlice) < 1:
            factorValue = 0.
        else:
            factorValue = sum(askDriveForceSlice < askDriveForceSlice[-1]) / len(askDriveForceSlice)

        self._addFactorValue(factorValue)