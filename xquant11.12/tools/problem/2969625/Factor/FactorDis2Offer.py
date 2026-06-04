from System.Factor import Factor


class FactorDis2Offer(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__midpW = self._getFactor(
            {
                "ClassName": "MidPriceWeighted",
                "Parameters": {
                    "Grade": 1,
                }
            }
        )

    def calculate(self):
        offer_price = self._getLastTickData("AvgOfferPrice")
        if offer_price < 0.01:
            offer_price = self._getLastTickData("BidPrice")[0]
        midpw = self.__midpW.getLastFactorValue()
        factor_value = (offer_price / midpw - 1) * 100
        self._addFactorValue(factor_value)
