from System.Factor import Factor


class FactorDistanceToLowModifiedOri_MDF(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        #lowPrice = min(self.__midPrice.getFactorValueList()[-self.__lag:])
        avgAskPrice = self._getLastNTickData("AvgOfferPrice", self.__lag)
        avgBidPrice = self._getLastNTickData("AvgBidPrice", self.__lag)
        avgMidPrice = [(x + y) / 2 if x > 0 and y > 0 else (x + y) for (x, y) in zip(avgAskPrice, avgBidPrice)]
        lowPrice = min(avgMidPrice)

        if lowPrice <= 0.01:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is None:
                factorValue = 0
            else:
                factorValue = lastFactorValue
        else:
            factorValue = 1000 * (1 - self.__midPrice.getLastFactorValue() / lowPrice)

        self._addFactorValue(factorValue)