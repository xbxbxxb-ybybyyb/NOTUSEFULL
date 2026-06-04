from System.Factor import Factor


class FactorSpeed(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__speedLag = self._getParameter("SpeedLag")

        self.__emaMidPrice = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__lag,
                    "OriginalData": {
                        "ClassName": "MidPrice"
                    }
                }
            }
        )

    def calculate(self):
        emaMidPriceList = self.__emaMidPrice.getFactorValueList()
        if len(emaMidPriceList) <= self.__speedLag:
            value = 0.
        else:
            value = ( emaMidPriceList[-1] / emaMidPriceList[-(self.__speedLag+1)] - 1. ) * ( 20. / self.__speedLag)

        self._addFactorValue(value)
