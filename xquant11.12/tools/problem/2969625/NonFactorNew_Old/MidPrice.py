from System.Factor import Factor


class MidPrice(Factor):
    def calculate(self):
        askP0 = self._getLastTickData("AskPrice")[0]
        bidP0 = self._getLastTickData("BidPrice")[0]
        if askP0 == 0 or bidP0 == 0:
            lastMidPrice = self.getLastFactorValue()
            if lastMidPrice is None or lastMidPrice == 0:
                factorValue = askP0 + bidP0
            else:
                factorValue = lastMidPrice
        else:
            factorValue = (askP0 + bidP0) / 2

        self._addFactorValue(factorValue)
