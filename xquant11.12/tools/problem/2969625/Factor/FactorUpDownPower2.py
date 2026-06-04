from System.Factor import Factor
import numpy as np

class FactorUpDownPower2(Factor):
    # 价格高的地方成交量越多，说明做空力量越强，短期价格下降
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__MALag = self._getParameter("MALag")

    def calculate(self):
        lastPrice = self._getLastNHistoricalTickData("LastPrice", self.__MALag)
        lastVolume = self._getLastNHistoricalTickData("Volume", self.__MALag)
        todayPrice = self._getLastNTickData("LastPrice", 2)[-1]
        if len(lastPrice) > 10:
            highPrice = np.percentile(lastPrice, 90)
        else:
            highPrice = todayPrice
        if np.sum(lastVolume) > 0:
            volumeRatio = np.sum(lastVolume[lastPrice >= highPrice]) / np.sum(lastVolume) - 0.1
        else:
            volumeRatio = 0
        
        if todayPrice > 0:
            factorValue = highPrice / todayPrice * volumeRatio * 100
        else:
            factorValue = 0
        if np.isnan(factorValue):
            factorValue = 0
        self._addFactorValue(factorValue)
