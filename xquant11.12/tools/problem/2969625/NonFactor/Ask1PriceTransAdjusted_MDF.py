from System.Factor import Factor


class Ask1PriceTransAdjusted_MDF(Factor):
    def calculate(self):
        # maxp = self._getLastTickData("MaxPrice")
        trans = self._getLastTickData("Transactions")
        ask1 = self._getLastTickData('AskPrice')[0]
        bid1 = self._getLastTickData('BidPrice')[0]

        if trans is not None:
            tp = self._getTransactionData("Price", trans)
            tf = self._getTransactionData("BSFlag", trans)
            last_tp = tp[tf == 1]
            last_tp = last_tp[-1] if len(last_tp) > 0 else 0.
        else:
            last_tp = 999999999.

        ask1 = ask1 if ask1 > 1e-4 else bid1

        factorValue = min(ask1, last_tp)

        self._addFactorValue(factorValue)
