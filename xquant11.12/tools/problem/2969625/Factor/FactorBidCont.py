import numpy as np
from System.Factor import Factor


class FactorBidCont(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self._addIntermediate("bidP1List", [])

    def calculate(self):
        minP = self._getLastTickData("MinPrice")
        bidP1 = self._getLastTickData("BidPrice")[0]
        if bidP1 <= 0:
            bidP1 = minP

        bidP1List = self.getIntermediate("bidP1List")
        bidP1List.append(bidP1)

        bidSign = np.diff([bidP1List[0]] + bidP1List)
        bidSign = np.sign(bidSign)

        if len(bidSign) < 2:
            fv = 0
        else:
            fv = np.corrcoef(np.cumsum(bidSign), np.arange(len(bidSign)))[0, 1]
        if np.isnan(fv):
            fv = 0

        self._addFactorValue(fv)
