import numpy as np
from System.Factor import Factor


class FactorAskDriveForceSharpeM(Factor):
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

        askDriveForceSlice = askDriveForceList[-self.__lag:]
        if len(askDriveForceSlice) < 5:
            factorValue = 0.
        else:
            askStd = np.nanstd(askDriveForceSlice) 
            if askStd > 1e-6:
                factorValue = - np.nanmean(askDriveForceSlice) / askStd
            else:
                lastFactorValue = self.getLastFactorValue()
                if lastFactorValue is not None:
                    factorValue = lastFactorValue
                else:
                    factorValue = 0.

        self._addFactorValue(factorValue)