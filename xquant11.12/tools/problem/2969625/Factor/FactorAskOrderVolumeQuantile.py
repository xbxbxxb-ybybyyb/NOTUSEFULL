from System.Factor import Factor
import numpy as np


class FactorAskOrderVolumeQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self._addIntermediate("AskOrderVolume", [])

    def calculate(self):

        ovs = self.getIntermediate("AskOrderVolume")

        orders = self._getLastTickData("Orders")
        if orders is not None:
            ov = self._getOrderData("Volume", orders)
            of = self._getOrderData("BSFlag", orders)
            ovs.append(np.nansum(ov[of == 2]))
        else:
            ovs.append(0.)

        factorValue = np.nansum(ovs[-1] > np.array(ovs)) / len(ovs)

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)
