import numpy as np
from System.Factor import Factor


class TickBidAmt(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        bid_vol = self._getLastTickData('BidVolume')
        bid_price = self._getLastTickData('BidPrice')
        amt = np.nansum(bid_vol * bid_price)

        self._addFactorValue(amt)

