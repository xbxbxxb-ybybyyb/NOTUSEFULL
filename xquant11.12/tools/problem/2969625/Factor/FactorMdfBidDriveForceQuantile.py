import numpy as np
from System.Factor import Factor


class FactorMdfBidDriveForceQuantile(Factor):
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