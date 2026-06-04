from System.Factor import Factor
import numpy as np


class INFVolume(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self._addIntermediate("TotalVolumeG", None)

    def calculate(self):

        totalVolumeG = self.getIntermediate("TotalVolumeG")
        totalVolumeG = 0. if totalVolumeG is None else totalVolumeG

        thisTotalVolumeG = np.nansum(self._getLastTickDataForStockGroup("TotalVolume", isStacked=True))
        factorValue = thisTotalVolumeG - totalVolumeG

        self._setIntermediate("TotalVolumeG", thisTotalVolumeG)

        self._addFactorValue(factorValue)

