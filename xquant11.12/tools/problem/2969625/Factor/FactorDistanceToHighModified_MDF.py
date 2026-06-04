from System.Factor import Factor


class FactorDistanceToHighModified_MDF(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        midHigh = max(self.__midPrice.getFactorValueList()[-self.__lag:])
        highPrice = self._getLastTickData('HighPrice')
        # avgAskPrice = self._getLastTickData("AvgOfferPrice")
        # avgBidPrice = self._getLastTickData("AvgBidPrice")
        # midAvgPrice = (avgAskPrice + avgBidPrice) / 2
        if highPrice < 0.01:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is None:
                factorValue = 0
            else:
                factorValue = lastFactorValue
        else:
            factorValue = midHigh / highPrice - 1

        self._addFactorValue(factorValue)
