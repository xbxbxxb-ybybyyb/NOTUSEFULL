from System.Factor import Factor


class FactorCrossPriceChangeSpeed(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__fastLag = self._getParameter("FastLag")
        self.__slowLag = self._getParameter("SlowLag")

        self.__crossPoint = self._getFactor(
            {
                "ClassName": "CrossPoint",
                "Parameters": {
                    "FastLag": self.__fastLag,
                    "SlowLag": self.__slowLag
                }
            }
        )

    def calculate(self):
        factorValue = 20 * self.__crossPoint.getLastFactorValue()[1]

        self._addFactorValue(factorValue)
