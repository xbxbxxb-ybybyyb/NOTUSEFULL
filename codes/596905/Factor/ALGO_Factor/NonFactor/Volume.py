from System.Factor import Factor


class Volume(Factor):
    def calculate(self):
        factorValue = self._getLastTickData("Volume")

        self._addFactorValue(factorValue)
