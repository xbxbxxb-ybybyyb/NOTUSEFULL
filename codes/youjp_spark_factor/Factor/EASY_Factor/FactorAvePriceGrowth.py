from System.Factor import Factor


class FactorAvePriceGrowth(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__fastLag = self._getParameter("FastLag")
        self.__slowLag = self._getParameter("SlowLag")

        self.__fastVWAPPrice = self._getFactor(
            {
                "ClassName": "VWAPPrice",
                "Parameters": {
                    "Lag": self.__fastLag
                }
            }
        )

        self.__slowVWAPPrice = self._getFactor(
            {
                "ClassName": "VWAPPrice",
                "Parameters": {
                    "Lag": self.__slowLag
                }
            }
        )

    def calculate(self):
        fastVWAPPrice = self.__fastVWAPPrice.getLastFactorValue()
        slowVWAPPrice = self.__slowVWAPPrice.getLastFactorValue()

        if fastVWAPPrice <= 0.01 or slowVWAPPrice <= 0.01:
            if len(self._getFactorValueList()) == 0:
                value = 0.
            else:
                value = self._getFactorValueList()[-1]
        else:
            value = 1000. * ( fastVWAPPrice / slowVWAPPrice - 1. )

        self._addFactorValue(value)

