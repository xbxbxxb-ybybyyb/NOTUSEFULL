from System.Factor import Factor
import numpy as np


class FactorOrderAskBidTNumRatioX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.sLag = self._getParameter("sLag")
        self.lag = self._getParameter("Lag")

        self._addIntermediate("RatioList", [])

    def calculate(self):
        ratioList = self.getIntermediate("RatioList")
        askNumArray = self._getLastTickData("AskNum")
        bidNumArray = self._getLastTickData("BidNum")

        askNum = np.nansum(askNumArray)
        bidNum = np.nansum(bidNumArray)
        total = askNum + bidNum

        ratio = bidNum / total if total > 1e-4 else 0
        ratioList.append(ratio)

        if len(ratioList) < min(3, self.sLag):
            factorValue = 0.
        else:
            factorValue = self.amplify_zcore(ratioList, self.sLag, self.lag) * 100

        self._addFactorValue(factorValue)

    @staticmethod
    def amplify_zcore(valueList, sLag, lag):
        size = len(valueList)
        sLag = min(max(1, int(size * sLag / lag)), sLag)
        std = np.nanstd(valueList)
        if std < 1e-6 or np.isnan(std):
            return 0
        else:
            return (np.nanmean(valueList[-sLag:]) - np.nanmean(valueList[-lag:])) / std


