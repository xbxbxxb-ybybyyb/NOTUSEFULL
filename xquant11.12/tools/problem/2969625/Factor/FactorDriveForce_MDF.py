import numpy as np
from System.Factor import Factor


class FactorDriveForce_MDF(Factor):
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
        self._addIntermediate("bidDriveForceList", [])

    def calculate(self):
        bidDriveForce, askDriveForce = self.__driveForce.getLastFactorValue()

        askDriveForceList = self.getIntermediate("askDriveForceList")
        askDriveForceList.append(askDriveForce)
        bidDriveForceList = self.getIntermediate("bidDriveForceList")
        bidDriveForceList.append(bidDriveForce)

        bidDriveForceSlice = np.array(bidDriveForceList[-self.__lag:])
        askDriveForceSlice = np.array(askDriveForceList[-self.__lag:])
        if len(askDriveForceSlice) < 1 or len(bidDriveForceSlice) < 1:
            factorValue = 0
        else:
            factorValue = sum(bidDriveForceSlice < bidDriveForceSlice[-1]) / len(bidDriveForceSlice) - sum(askDriveForceSlice < askDriveForceSlice[-1]) / len(askDriveForceSlice)

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