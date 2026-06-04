#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 15:13
import datetime as dt
from System.Factor import Factor


class FactorMdfOrderPressureConsistency(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("SmoothLag")

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

        netPressureList = self.getIntermediate("netPressureList")
        netPressureList.append(pressureBuy - pressureSell)

        if len(netPressureList) > 1:
            last_tick_time = timestampList[-2]
            current_tick_time = timestampList[-1]
            if netPressureList[-1] > 0:
                factorValue = self.getLastFactorValue() + self.__time_diff(last_tick_time, current_tick_time)
            elif netPressureList[-1] < 0:
                factorValue = self.getLastFactorValue() - self.__time_diff(last_tick_time, current_tick_time)
            else:
                factorValue = self.getLastFactorValue()
        else:
            factorValue = 0

        factorValueList = self.getFactorValueList()
        factorValue = self._EMA_calculate(factorValue, factorValueList, self.__sLag)

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