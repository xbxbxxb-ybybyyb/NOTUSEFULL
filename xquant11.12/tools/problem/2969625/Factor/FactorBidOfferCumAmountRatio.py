from System.Factor import Factor
import numpy as np


class FactorBidOfferCumAmountRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidCumAmountList", [])
        self._addIntermediate("OfferCumAmountList", [])

    def calculate(self):
        bcas = self.getIntermediate("BidCumAmountList")
        ocas = self.getIntermediate("OfferCumAmountList")

        amount = self._getAllTodayTickData("Amount")
        cbqty = self._getLastNTickData("BidQty", 2)
        bqty = self.__process_last_n_qty(cbqty, 1)[-1]
        avgbp = self._getLastTickData("AvgBidPrice")
        coqty = self._getLastNTickData("OfferQty", 2)
        oqty = self.__process_last_n_qty(coqty, 1)[-1]
        avgop = self._getLastTickData("AvgOfferPrice")

        if len(bcas) == 0:
            bcas.append(bqty * avgbp)
            ocas.append(oqty * avgop)
        else:
            bcas.append(bqty * avgbp + bcas[-1])
            ocas.append(oqty * avgop + ocas[-1])

        if np.nanmean(amount) > 1e-4:
            factorValue = (bcas[-1] - ocas[-1]) / np.nanmean(amount)
        else:
            factorValue = 0.

        self._addFactorValue(factorValue)

    @staticmethod
    def __process_last_n_qty(x, lag):
        x_new = np.clip(np.diff(x), a_min=0, a_max=np.inf)
        if len(x_new) < lag:
            x_new = np.hstack((0, x_new))
        return x_new
