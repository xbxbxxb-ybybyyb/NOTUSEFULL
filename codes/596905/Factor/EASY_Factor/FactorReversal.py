import numpy as np
from System.Factor import Factor


class FactorReversal(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__shortLag = self._getParameter("ShortLag")
        self.__longLag = self._getParameter("LongLag")
        self.__emaLag = self._getParameter("EMALag")
        self.__lookBack = self._getParameter("LookBack")

        self.__emaMidPrice = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__emaLag,
                    "OriginalData": {
                        "ClassName": "MidPrice"
                    }
                }
            }
        )

        self.__emaVolumeTiny = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__emaLag,
                    "OriginalData": {
                        "ClassName": "Volume"
                    }
                }
            }
        )

        self.__emaVolumeShort = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__shortLag,
                    "OriginalData": {
                        "ClassName": "Volume"
                    }
                }
            }
        )

        self.__emaVolumeLong = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__longLag,
                    "OriginalData": {
                        "ClassName": "Volume"
                    }
                }
            }
        )

    def calculate(self):
        emaMidPrice = self.__emaMidPrice.getLastFactorValue()
        emaVolumeTiny = self.__emaVolumeTiny.getLastFactorValue()
        emaVolumeShort = self.__emaVolumeShort.getLastFactorValue()
        emaVolumeLong = self.__emaVolumeLong.getLastFactorValue()

        historyVolumeArray = self._getAllHistoricalTickData("Volume")
        volumeArray = self._getAllTodayTickData("Volume")
        allVolumeArray = np.append(historyVolumeArray, volumeArray)

        historyAmountArray = self._getAllHistoricalTickData("Amount")
        amountArray = self._getAllTodayTickData("Amount")
        allAmountArray = np.append(historyAmountArray, amountArray)

        volumeShort = np.nanmean(allVolumeArray[-self.__shortLag:])
        volumeLong = np.nanmean(allVolumeArray[-self.__longLag:])
        amountShort = np.nanmean(allAmountArray[-self.__shortLag:])
        amountLong = np.nanmean(allAmountArray[-self.__longLag:])
        averagePriceShort = self._calculate_average_price(amountShort, volumeShort)
        averagePriceLong = self._calculate_average_price(amountLong, volumeLong)

        dayMaVolume = np.nanmean(allVolumeArray[-min(historyVolumeArray.shape[0], self.__lookBack):])

        if dayMaVolume > 0:
            volumeRatioShort = volumeShort / dayMaVolume
            volumeRatioLong = volumeLong / dayMaVolume
        else:
            volumeRatioShort = 0.
            volumeRatioLong = 0.

        valueLong = self._calculate_factor_value_long(emaMidPrice, averagePriceLong, emaVolumeLong, emaVolumeTiny, volumeRatioLong)
        valueShort = self._calculate_factor_value_short(emaMidPrice, averagePriceShort, emaVolumeShort, emaVolumeTiny, volumeRatioShort)
            
        if valueLong == 0 or valueShort == 0:
            value = 0.0
        else:
            value = (valueLong + valueShort) / 2.

        self._addFactorValue(value)

    @staticmethod
    def _calculate_average_price(amount, volume):
        if volume == 0:
            average_price = 0.
        else:
            average_price = amount * 1.0 / volume
        return  average_price

    @staticmethod
    def _calculate_factor_value_long(ema_price, average_price, ma_volume, ema_volume, volume_ratio):
        if ema_volume == 0 or average_price == 0 or volume_ratio == 0:
            return 0.0
        return (1. - float(ema_price / average_price)) * np.sqrt(ma_volume / (ema_volume * volume_ratio)) * 1000

    @staticmethod
    def _calculate_factor_value_short(ema_price, average_price, ma_volume, ema_volume, volume_ratio):
        if ma_volume == 0 or average_price == 0 or volume_ratio == 0:
            return 0.0
        return (float(ema_price / average_price) - 1.) * np.sqrt(ema_volume / ma_volume * volume_ratio) * 1000