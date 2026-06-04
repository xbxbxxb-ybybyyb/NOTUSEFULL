from System.Factor import Factor


class FactorDemo(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )


    def calculate(self):
        free_float_shares = self._getLastNHistoricalDailyData("FreeFloatShares", 1)[0]
        midPrice = self.__midPrice.getLastFactorValue()

        value = 0.

        self._addFactorValue(value)

