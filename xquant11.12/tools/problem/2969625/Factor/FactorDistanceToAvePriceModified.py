from System.Factor import Factor


class FactorDistanceToAvePriceModified(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )
        self.__avePrice = self._getFactor(
            {
                "ClassName": "AvePrice"
            }
        )

    def calculate(self):
        midPrice = self.__midPrice.getLastFactorValue()
        avePrice = self.__avePrice.getLastFactorValue()

        if avePrice > 0.01 and midPrice > 0.01:
            factorValue = midPrice / avePrice - 1
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is None:
                factorValue = 0
            else:
                factorValue = lastFactorValue

        self._addFactorValue(factorValue)
