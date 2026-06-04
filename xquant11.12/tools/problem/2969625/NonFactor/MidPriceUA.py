from System.Factor import Factor


class MidPriceUA(Factor):
    def calculate(self):
        askP = self._getLastTickDataUA("AskPrice")
        bidP = self._getLastTickDataUA("BidPrice")
        if len(askP) > 0:
            askP0 = askP[0]
            bidP0 = bidP[0]
            if askP0 == 0 or bidP0 == 0:
                lastMidPrice = self.getLastFactorValue()
                if lastMidPrice is None or lastMidPrice == 0:
                    factorValue = askP0 + bidP0
                else:
                    factorValue = lastMidPrice
            else:
                factorValue = (askP0 + bidP0) / 2
        else:
            factorValue = None

        self._addFactorValue(factorValue)
