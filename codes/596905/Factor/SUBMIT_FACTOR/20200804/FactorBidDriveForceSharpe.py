import numpy as np
from System.Factor import Factor


class FactorBidDriveForceSharpe(Factor):
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
        self._addIntermediate("bidDriveForceList", [])

    def calculate(self):
        bidDriveForce, _ = self.__driveForce.getLastFactorValue()

        bidDriveForceList = self.getIntermediate("bidDriveForceList")
        bidDriveForceList.append(bidDriveForce)

        bidDriveForceSlice = bidDriveForceList[-self.__lag:]
        if len(bidDriveForceSlice) <= 5:
            factorValue = 0.
        else:
            if np.nanstd(bidDriveForceSlice) != 0:
                factorValue = np.nanmean(bidDriveForceSlice) / np.nanstd(bidDriveForceSlice)
            else:
                lastFactorValue = self.getLastFactorValue()
                if lastFactorValue is not None:
                    factorValue = lastFactorValue
                else:
                    factorValue = 0.

        self._addFactorValue(factorValue)