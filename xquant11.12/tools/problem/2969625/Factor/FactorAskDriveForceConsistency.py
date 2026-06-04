import numpy as np
import datetime as dt
from System.Factor import Factor


class FactorAskDriveForceConsistency(Factor):
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
        timestampList = self._getAllTodayTickData("Timestamp")

        _, askDriceForce = self.__driveForce.getLastFactorValue()
        askDriveForceList = self.getIntermediate("askDriveForceList")
        askDriveForceList.append(askDriceForce)

        factorValue = 0.
        if len(askDriveForceList) > 1:
            last_tick_time = timestampList[-2]
            current_tick_time = timestampList[-1]
            if askDriveForceList[-1] > 0 and askDriveForceList[-2] > 0:
                factorValue = self.getLastFactorValue() - self.__time_diff(last_tick_time, current_tick_time)
            elif askDriveForceList[-1] < 0 and askDriveForceList[-2] < 0:
                factorValue = self.getLastFactorValue() + self.__time_diff(last_tick_time, current_tick_time)

        factorValueList = self.getFactorValueList()
        factorValue = self._EMA_calculate(factorValue, factorValueList, self.__lag)

        self._addFactorValue(factorValue)

    def __time_diff(self, transactionTimestamp, tickTimestamp):
        transactionTime = dt.datetime.fromtimestamp(transactionTimestamp)
        tickTime = dt.datetime.fromtimestamp(tickTimestamp)
        morningEndTimestamp = (dt.datetime(transactionTime.year, transactionTime.month, transactionTime.day, 11, 30, 00)
                               .timestamp())
        afternoonStartTimestamp = dt.datetime(tickTime.year, tickTime.month, tickTime.day, 13, 00, 00).timestamp()
        if transactionTimestamp <= morningEndTimestamp and tickTimestamp >= afternoonStartTimestamp:
            transactionTimestamp += (dt.datetime(transactionTime.year, transactionTime.month, transactionTime.day,
                                                 13, 00, 00).timestamp() - morningEndTimestamp)
        return tickTimestamp - transactionTimestamp

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])