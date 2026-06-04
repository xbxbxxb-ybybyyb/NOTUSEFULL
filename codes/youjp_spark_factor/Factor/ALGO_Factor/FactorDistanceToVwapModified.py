from System.Factor import Factor


class FactorDistanceToVwapModified(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )
        self.__vwapPrice = self._getFactor(
            {
                "ClassName": "VWAPPrice",
                "Parameters": {
                    "Lag": self.__lag
                }
            }
        )

    def calculate(self):
        midPrice = self.__midPrice.getLastFactorValue()
        vwapPrice = self.__vwapPrice.getLastFactorValue()

        if vwapPrice <= 0.01 or midPrice <= 0.01:
            if len(self.getFactorValueList()) == 0:
                factorValue = 0
            else:
                factorValue = self.getLastFactorValue()
        else:
            factorValue = midPrice / vwapPrice - 1

        self._addFactorValue(factorValue)
