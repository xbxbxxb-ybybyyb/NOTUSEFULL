import math
from System.Factor import Factor


class FactorTransSellBuy(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__decayNum = self._getParameter("DecayNum")
        self.__eps = 1e-5

        self.__transactionDistribution = self._getFactor(
            {
                "ClassName": "TransactionDistribution",
                "Parameters": {
                    "DecayNum": self.__decayNum
                }
            }
        )

        self._addIntermediate("BuyVolume", [])
        self._addIntermediate("SellVolume", [])

    def calculate(self):
        buyVolumeList = self.getIntermediate("BuyVolume")
        sellVolumeList = self.getIntermediate("SellVolume")

        lastBuyVolume = buyVolumeList[-1] if len(buyVolumeList) > 0 else None
        lastSellVolume = sellVolumeList[-1] if len(sellVolumeList) > 0 else None

        buyVolume = self.ema(lastBuyVolume, self.__transactionDistribution.getLastFactorValue()[0], self.__lag)
        sellVolume = self.ema(lastSellVolume, self.__transactionDistribution.getLastFactorValue()[2], self.__lag)

        buyVolumeList.append(buyVolume)
        sellVolumeList.append(sellVolume)

        if buyVolume < 0 or sellVolume < 0:
            factorValue = 0
        else:
            factorValue = math.log((sellVolume + self.__eps) / (buyVolume + self.__eps))

        self._addFactorValue(factorValue)

    @staticmethod
    def ema(lastEMA, value, n):
        alpha = 2 / (n + 1)
        lastEMA = value if lastEMA is None else lastEMA

        return value * alpha + lastEMA * (1 - alpha)
