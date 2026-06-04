from System.Factor import Factor


class FactorPriceChangeSpeed(Factor):
    def __init__(self, para, factorManager):
        super().__init__(para, factorManager)
        self.__fastLag = self._getParameter("FastLag")
        self.__slowLag = self._getParameter("SlowLag")

        self.__priceChange = self._getFactor(
            {
                "ClassName": "PriceChange",
                "Parameters": {
                    "FastLag": self.__fastLag,
                    "SlowLag": self.__slowLag
                }
            }
        )

    def calculate(self):
        _, value = self.__priceChange.getLastFactorValue()
        self._addFactorValue(value)