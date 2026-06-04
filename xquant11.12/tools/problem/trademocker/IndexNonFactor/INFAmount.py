from System.Factor import Factor
import numpy as np


class INFAmount(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self._addIntermediate("TotalAmountG", None)

    def calculate(self):
        totalAmountG = self.getIntermediate("TotalAmountG")
        totalAmountG = 0. if totalAmountG is None else totalAmountG

        thisTotalAmountG = np.nansum(self._getLastTickDataForStockGroup("TotalAmount", isStacked=True))
        self._setIntermediate("TotalVolumeG", thisTotalAmountG)
        factorValue = thisTotalAmountG - totalAmountG

        self._addFactorValue(factorValue)
