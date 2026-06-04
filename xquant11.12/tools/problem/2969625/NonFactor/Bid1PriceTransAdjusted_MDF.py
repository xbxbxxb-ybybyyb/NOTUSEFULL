from System.Factor import Factor


class Bid1PriceTransAdjusted_MDF(Factor):
    def calculate(self):
        # minp = self._getLastTickData("MinPrice")
        trans = self._getLastTickData("Transactions")
        ask1 = self._getLastTickData('AskPrice')[0]
        bid1 = self._getLastTickData('BidPrice')[0]

        if trans is not None:
            tp = self._getTransactionData("Price", trans)
            tf = self._getTransactionData("BSFlag", trans)
            last_tp = tp[tf == 2]
            last_tp = last_tp[-1] if len(last_tp) > 1e-4 else 0.
        else:
            last_tp = 0.

        bid1 = bid1 if bid1 > 1e-4 else ask1

        factorValue = max(bid1, last_tp)

        self._addFactorValue(factorValue)
