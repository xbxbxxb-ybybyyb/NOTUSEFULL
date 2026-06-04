from System.Factor import Factor


class Volume(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        factorValue = self._getLastTickData("Volume")
        self._addFactorValue(factorValue)
