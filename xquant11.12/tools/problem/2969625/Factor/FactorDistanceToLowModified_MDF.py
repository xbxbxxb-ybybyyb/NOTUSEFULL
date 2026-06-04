from System.Factor import Factor


class FactorDistanceToLowModified_MDF(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        midLow = min(self.__midPrice.getFactorValueList()[-self.__lag:])
        lowPrice = self._getLastTickData('LowPrice')
        # avgAskPrice = self._getLastTickData("AvgOfferPrice")
        # avgBidPrice = self._getLastTickData("AvgBidPrice")
        # midAvgPrice = (avgAskPrice + avgBidPrice) / 2
        if lowPrice <= 0.01:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is None:
                factorValue = 0
            else:
                factorValue = lastFactorValue
        else:
            #factorValue = self.__midPrice.getLastFactorValue() / lowPrice - 1
            factorValue = midLow / lowPrice - 1

        self._addFactorValue(factorValue)
