from System.Factor import Factor


class FactorVolumeAmp(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("VolumeShort", [])
        self._addIntermediate("VolumeLong", [])

    def calculate(self):
        volumeArray = self._getAllTodayTickData("Volume")
        size = volumeArray.shape[0]
        tickVolume = volumeArray[-1]

        volumeShortList = self.getIntermediate("VolumeShort")
        volumeShort = self._EMA_calculate(tickVolume, volumeShortList, self.__lag)
        volumeShortList.append(volumeShort)
        volumeLongList = self.getIntermediate("VolumeLong")
        volumeLong = self._EMA_calculate(tickVolume, volumeLongList, size)
        volumeLongList.append(volumeLong)

        if size == 1:
            value = 1.
        else:
            if volumeLong <=0:
                value = 0.
            else:
                value = volumeShort / volumeLong
        self._addFactorValue(value)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])

