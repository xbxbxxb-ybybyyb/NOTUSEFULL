from System.Factor import Factor


class Amount(Factor):
    def calculate(self):
        factorValue = self._getLastTickData("Amount")

        self._addFactorValue(factorValue)
