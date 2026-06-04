import datetime as dt
import numpy as np
from System.Factor import Factor


class FactorLowRes(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.adjLevel = 2
        self.validMinutes = ([int((dt.datetime(1949, 10, 1, 9, 30) + dt.timedelta(minutes=i)).strftime("%H%M%S") + "000") for i in range(120)]
                             + [int((dt.datetime(1949, 10, 1, 13) + dt.timedelta(minutes=i)).strftime("%H%M%S") + "000") for i in range(120)])

    def _onNewDay(self):
        openM = self._getAllHistoricalMinuteData("OpenPrice")
        lowM = self._getAllHistoricalMinuteData("LowPrice")
        timeM = self._getAllHistoricalMinuteData("Time")
        lowSwing = lowM / openM

        lowSwingMean = []
        for i in range(len(self.validMinutes)):
            lowSwingMean.append(np.nanmean(lowSwing[timeM == self.validMinutes[i]]))

        self.lowSwing = lowSwingMean

    def calculate(self):
        askP = self._getLastTickData("AskPrice")
        askV = self._getLastTickData("AskVolume")
        maxP = self._getLastTickData("MaxPrice")

        askVSum = askV[:self.adjLevel].sum()
        askVWAP = (askP[:self.adjLevel] * askV[:self.adjLevel]).sum() / askVSum if askVSum > 0 else maxP

        lastP = np.mean(self._getLastNTickData("LastPrice", 10))
        lowP = lastP * self.lowSwing[min(int(len(self._getAllTodayTickData("LastPrice")) / 20), len(self.lowSwing) - 1)]

        factorValue = (askVWAP / lowP - 1) * 1000 if lowP > 0.001 else 0.0

        self._addFactorValue(factorValue)
