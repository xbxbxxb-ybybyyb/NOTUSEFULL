import numpy as np
from System.Factor import Factor


class FactorBidOfferQtyRatioInc(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.lag = self._getParameter("Lag")

        self._addIntermediate("RatioList", [])

    def calculate(self):
        ratioList = self.getIntermediate("RatioList")
        bid = self._getLastTickData("BidQty")
        offer = self._getLastTickData("OfferQty")
        total = bid + offer

        if total > 1e-4:
            ratio = bid / total - 0.5
        else:
            if len(ratioList) > 0:
                ratio = ratioList[-1]
            else:
                ratio = 0.

        ratioList.append(ratio)

        factorValue = (ratioList[-1] - np.nanmean(ratioList[-self.lag:])) * 1000

        self._addFactorValue(factorValue)



