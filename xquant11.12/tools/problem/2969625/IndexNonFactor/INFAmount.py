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
        factorValue = thisTotalAmountG - totalAmountG

        self._setIntermediate("TotalAmountG", thisTotalAmountG)

        self._addFactorValue(factorValue)
