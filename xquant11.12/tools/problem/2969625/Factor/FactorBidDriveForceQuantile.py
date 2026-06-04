import numpy as np
from System.Factor import Factor


class FactorBidDriveForceQuantile(Factor):
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

        bidDriveForceSlice = np.array(bidDriveForceList[-self.__lag:])
        if len(bidDriveForceSlice) < 1:
            factorValue = 0.
        else:
            factorValue = sum(bidDriveForceSlice < bidDriveForceSlice[-1]) / len(bidDriveForceSlice)

        self._addFactorValue(factorValue)