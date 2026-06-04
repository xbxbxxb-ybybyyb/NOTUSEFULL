import numpy as np
from Calc.System.Factor import Factor


class FactorNetTradeRet(Factor):
    def calculate(self):
        askP = self.getLastTickData("AskPrice")
        bidP = self.getLastTickData("BidPrice")
        askV = self.getLastTickData("AskVolume")
        bidV = self.getLastTickData("BidVolume")
        maxP = self.getLastTickData("MaxPrice")
        minP = self.getLastTickData("MinPrice")

        tradeBS = self.getLastNSecTradeData("BSFlag", 30)
        tradeQty = self.getLastNSecTradeData("Volume", 30)

        netTradeQty = np.sum(tradeQty[tradeBS == 1]) - np.sum(tradeQty[tradeBS == 2])

        askVCum = np.cumsum(askV)
        bidVCum = np.cumsum(bidV)

        newAskP = askP[askVCum > netTradeQty]
        newAskP = newAskP[0] if newAskP.shape[0] > 0 else (askP[-1] if askP[-1] > 1e-4 else maxP)
        newBidP = bidP[bidVCum > -netTradeQty]
        newBidP = newBidP[0] if newBidP.shape[0] > 0 else (bidP[-1] if bidP[-1] > 1e-4 else minP)

        askP1 = askP[0] if askP[0] > 1e-4 else maxP
        bidP1 = bidP[0] if bidP[0] > 1e-4 else minP

        fv = ((newAskP + newBidP) / (askP1 + bidP1) - 1) * 1000

        self.addFactorValue(fv)
