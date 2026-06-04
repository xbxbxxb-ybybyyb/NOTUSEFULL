from System.Factor import Factor


class FactorSpeedModified(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__EMAMidPriceLag = self._getParameter("EMAMidPriceLag")
        self.__lag = self._getParameter("Lag")

        self.__emaMidPrice = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__EMAMidPriceLag,
                    "OriginalData": {
                        "ClassName": "MidPrice"
                    }
                }
            }
        )

    def calculate(self):
        emaMidPriceList = self.__emaMidPrice.getFactorValueList()
        emaMidPriceListLength = len(emaMidPriceList)

        if emaMidPriceListLength > self.__lag:
            factorValue = (emaMidPriceList[-1] / emaMidPriceList[-self.__lag - 1] - 1) / (self.__lag / 20)
        else:
            factorValue = (emaMidPriceList[-1] / emaMidPriceList[0] - 1) / (emaMidPriceListLength / 20)

        self._addFactorValue(factorValue)
