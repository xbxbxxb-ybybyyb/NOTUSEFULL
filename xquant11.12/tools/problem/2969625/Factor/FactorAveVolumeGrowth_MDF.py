import numpy as np
from System.Factor import Factor


class FactorAveVolumeGrowth_MDF(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__maLag = self._getParameter("MALag")

    def calculate(self):
        # 获取昨天成交量(TickLength=1)
        historyVolumeArray = self._getAllHistoricalTickData("Volume")
        volumeArray = self._getAllTodayTickData("Volume")
        allVolumeArray = np.append(historyVolumeArray, volumeArray)
        maVolume = np.nanmean(volumeArray[-self.__maLag:])
        historyVolumeSize = historyVolumeArray.shape[0]
        volumeSum = np.nansum(allVolumeArray[-(historyVolumeSize + 1):-1])

        ceiling = self._getLastTickData("HighPrice")
        floor = self._getLastTickData("LowPrice")
        lastPrice = self._getLastTickData("LastPrice")
        priceRatio = (lastPrice - floor) / (ceiling - floor) - 0.5 if (ceiling - floor) > 0.01 else 0

        # if maVolume < 0 or volumeSum <= 1e-6:
        #     value = 0.0
        # elif priceRatio > 0.5:
        #     value = - maVolume * 1000. / volumeSum
        # elif priceRatio < 0.5:
        #     value = - maVolume * 1000. / volumeSum
        # else:
        #     value = 0.0

        if maVolume < 0 or volumeSum <= 1e-6:
            value = 0.0
        else:
            value = - priceRatio * maVolume * 10000. / volumeSum

        self._addFactorValue(value)