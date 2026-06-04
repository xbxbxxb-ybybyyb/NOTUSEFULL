import numpy as np
from System.Factor import Factor


class FactorBidDriveForceQuantileX(Factor):
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
        self._addIntermediate("bidDriveForceList", [])

    def calculate(self):
        bidDriveForce, _ = self.__driveForce.getLastFactorValue()

        bidDriveForceList = self.getIntermediate("bidDriveForceList")
        bidDriveForce = self._EMA_calculate(bidDriveForce, bidDriveForceList, self.__lag)
        bidDriveForceList.append(bidDriveForce)

        bidDriveForceSlice = np.array(bidDriveForceList[-self.__window:])
        if len(bidDriveForceSlice) < 5:
            factorValue = 0.
        else:
            factorValue = np.sum(bidDriveForceSlice < bidDriveForceSlice[-1]) / len(bidDriveForceSlice) - 0.5

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