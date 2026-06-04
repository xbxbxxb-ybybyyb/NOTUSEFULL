from System.Factor import Factor
import numpy as np


class FactorCBConvPremiumRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):

        convp = self._getLastNHistoricalDailyData("Convprice", 1)[0]
        midp = self.__midPrice.getLastFactorValue()
        lastp_udly = self._getLastTickDataUA("LastPrice")

        if not np.isnan(convp):
            if not np.isnan(lastp_udly):
                convv = lastp_udly * 100 / convp
                factorValue = midp / convv - 1
            else:
                factorValue = 0
        else:
            factorValue = 0  # 上市第一天无法计算

        self._addFactorValue(factorValue)
