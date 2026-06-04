from System.Factor import Factor
import numpy as np

class FactorUpDownPower(Factor):
    # 价格低的地方成交量越大，说明反转力量越强
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__MALag = self._getParameter("MALag")

    def calculate(self):
        lastPrice = self._getLastNHistoricalTickData("LastPrice", self.__MALag)
        lastVolume = self._getLastNHistoricalTickData("Volume", self.__MALag)
        todayPrice = self._getLastNTickData("LastPrice", 2)[-1]
        if len(lastPrice) > 10:
            lowPrice = np.percentile(lastPrice, 10)
        else:
            lowPrice = todayPrice
        if np.sum(lastVolume) > 0:
            volumeRatio = np.sum(lastVolume[lastPrice <= lowPrice]) / np.sum(lastVolume) - 0.1
        else:
            volumeRatio = 0
        
        if todayPrice > 0:
            factorValue = lowPrice / todayPrice * volumeRatio * 100
        else:
            factorValue = 0
        if np.isnan(factorValue):
            factorValue = 0
        self._addFactorValue(factorValue)
