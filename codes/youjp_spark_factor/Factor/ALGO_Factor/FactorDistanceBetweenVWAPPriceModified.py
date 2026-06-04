from System.Factor import Factor


class FactorDistanceBetweenVWAPPriceModified(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__fastLag = self._getParameter("FastLag")
        self.__slowLag = self._getParameter("SlowLag")

        self.__VWAPPriceFast = self._getFactor(
            {
                "ClassName": "VWAPPrice",
                "Parameters": {
                    "Lag": self.__fastLag
                }
            }
        )
        self.__VWAPPriceSlow = self._getFactor(
            {
                "ClassName": "VWAPPrice",
                "Parameters": {
                    "Lag": self.__slowLag
                }
            }
        )

    def calculate(self):
        priceFast = self.__VWAPPriceFast.getLastFactorValue()
        priceSlow = self.__VWAPPriceSlow.getLastFactorValue()

        if priceFast > 0.01 and priceSlow > 0.01:
            factorValue = 1000 * (1 - priceSlow / priceFast)
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is None:
                factorValue = 0
            else:
                factorValue = lastFactorValue

        self._addFactorValue(factorValue)
