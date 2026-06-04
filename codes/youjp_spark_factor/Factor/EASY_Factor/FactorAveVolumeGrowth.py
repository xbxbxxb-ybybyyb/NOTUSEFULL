import numpy as np
from System.Factor import Factor


class FactorAveVolumeGrowth(Factor):
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
        volumeSum = np.nansum(allVolumeArray[-(historyVolumeSize+1):-1])

        if maVolume < 0 or volumeSum <= 0:
            value = 0.0
        else:
            value = maVolume * 1000. / volumeSum

        self._addFactorValue(value)



