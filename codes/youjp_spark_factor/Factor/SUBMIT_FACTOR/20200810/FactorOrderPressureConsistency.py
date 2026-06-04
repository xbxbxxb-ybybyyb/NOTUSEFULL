#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 15:13

import math
import datetime as dt
from System.Factor import Factor


class FactorOrderPressureConsistency(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__emaOrderPressure = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__lag,
                    "OriginalData": {
                        "ClassName": "OrderEvaluate2"
                    }
                }
            }
        )
        self._addIntermediate("netPressureList", [])

    def calculate(self):
        timestampList = self._getAllTodayTickData("Timestamp")
        pressureBuy, pressureSell = self.__emaOrderPressure.getLastFactorValue()

        if pressureBuy == 0 and pressureSell == 0:
            netPressure = 0
        elif pressureBuy == 0:
            netPressure = -10
        elif pressureSell == 0:
            netPressure = 10
        else:
            netPressure = pressureBuy - pressureSell

        netPressureList = self.getIntermediate("netPressureList")
        netPressureList.append(netPressure)

        factorValue = 0.
        if len(netPressureList) > 1:
            last_tick_time = timestampList[-2]
            current_tick_time = timestampList[-1]
            if netPressureList[-1] > 0 and netPressureList[-2] > 0:
                factorValue = self.getLastFactorValue() + self.__time_diff(last_tick_time, current_tick_time)
            elif netPressureList[-1] < 0 and netPressureList[-2] < 0:
                factorValue = self.getLastFactorValue() - self.__time_diff(last_tick_time, current_tick_time)

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