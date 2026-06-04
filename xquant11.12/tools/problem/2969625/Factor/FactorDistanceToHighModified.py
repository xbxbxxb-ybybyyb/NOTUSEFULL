from System.Factor import Factor


class FactorDistanceToHighModified(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        highPrice = max(self.__midPrice.getFactorValueList()[-self.__lag:])

        if highPrice < 0.01:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is None:
                factorValue = 0
            else:
                factorValue = lastFactorValue
        else:
            factorValue = self.__midPrice.getLastFactorValue() / highPrice - 1

        self._addFactorValue(factorValue)
