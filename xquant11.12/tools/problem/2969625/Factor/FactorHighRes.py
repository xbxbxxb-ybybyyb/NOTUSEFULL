import datetime as dt
import numpy as np
from System.Factor import Factor


class FactorHighRes(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.adjLevel = 2
        self.validMinutes = ([int((dt.datetime(1949, 10, 1, 9, 30) + dt.timedelta(minutes=i)).strftime("%H%M%S") + "000") for i in range(120)]
                             + [int((dt.datetime(1949, 10, 1, 13) + dt.timedelta(minutes=i)).strftime("%H%M%S") + "000") for i in range(120)])

    def _onNewDay(self):
        openM = self._getAllHistoricalMinuteData("OpenPrice")
        highM = self._getAllHistoricalMinuteData("HighPrice")
        timeM = self._getAllHistoricalMinuteData("Time")
        highSwing = highM / openM

        highSwingMean = []
        for i in range(len(self.validMinutes)):
            highSwingMean.append(np.nanmean(highSwing[timeM == self.validMinutes[i]]))

        self.highSwing = highSwingMean

    def calculate(self):
        bidP = self._getLastTickData("BidPrice")
        bidV = self._getLastTickData("BidVolume")
        minP = self._getLastTickData("MinPrice")

        bidVSum = bidV[:self.adjLevel].sum()
        bidVWAP = (bidP[:self.adjLevel] * bidV[:self.adjLevel]).sum() / bidVSum if bidVSum > 0 else minP

        lastP = np.mean(self._getLastNTickData("LastPrice", 10))
        highP = lastP * self.highSwing[min(int(len(self._getAllTodayTickData("LastPrice")) / 20), len(self.highSwing) - 1)]

        factorValue = (bidVWAP / highP - 1) * 1000 if highP > 0.001 else 0.0

        self._addFactorValue(factorValue)
