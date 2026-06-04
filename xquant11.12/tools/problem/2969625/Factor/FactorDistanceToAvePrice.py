from System.Factor import Factor


class FactorDistanceToAvePrice(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )
        self.__vwapPrice = self._getFactor(
            {
                "ClassName": "AvePrice"
            }
        )

    def calculate(self):
        midPrice = self.__midPrice.getLastFactorValue()
        vwapPrice = self.__vwapPrice.getLastFactorValue()

        if vwapPrice <= 0.01 or midPrice <= 0.01:
            if len(self.getFactorValueList()) == 0:
                value = 0
            else:
                value = self.getFactorValueList()[-1]
        else:
            value = midPrice / vwapPrice - 1

        self._addFactorValue(value)

