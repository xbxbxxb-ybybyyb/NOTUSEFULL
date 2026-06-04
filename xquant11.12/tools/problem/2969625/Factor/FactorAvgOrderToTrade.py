import numpy as np
from System.Factor import Factor

class FactorAvgOrderToTrade(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        # self.__dLag = self._getParameter('DayLag')
        self.__lag = self._getParameter('Lag')

    def calculate(self):
        totalAmount = np.nansum(self._getLastNTickData('Amount', self.__lag))
        totalVolume = np.nansum(self._getLastNTickData('Volume', self.__lag))
        avgTradePrice = (totalAmount) / (totalVolume) if totalVolume > 0 else 0
        avgAskPrice = np.nanmean(self._getLastNTickData("AvgOfferPrice", self.__lag))
        avgBidPrice = np.nanmean(self._getLastNTickData("AvgBidPrice", self.__lag))
        if avgAskPrice == 0 or avgBidPrice == 0:
            midAvgOrderPrice = avgBidPrice + avgAskPrice
        else:
            midAvgOrderPrice = (avgAskPrice + avgBidPrice) / 2
        last_price = self._getLastTickData('LastPrice')
        ceiling, floor = self._getLastTickData('HighPrice'), self._getLastTickData('LowPrice')
        price_ratio = (last_price - floor) / (ceiling - floor) if (ceiling - floor) > 1e-4 else 0.5

        factorValue = - (avgTradePrice / midAvgOrderPrice - 1) * price_ratio * 1000 if midAvgOrderPrice > 1e-4 else 0

        self._addFactorValue(factorValue)