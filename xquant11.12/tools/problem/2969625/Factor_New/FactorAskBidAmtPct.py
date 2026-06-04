from System.Factor import Factor
import numpy as np


class FactorAskBidAmtPct(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__windows = self._getParameter("Window")

    def calculate(self):
        Ask_amt, Bid_amt = self.__tran()
        if (len(Ask_amt) > 0) and (len(Bid_amt) > 0):
            price = self._getLastNTickData('LastPrice',self.__windows)
            if len(price) <= self.__windows:
                pre_price = self._getAllHistoricalTickData('LastPrice')
                price = np.append(pre_price[-(self.__windows - len(price)):], price)
            pct = (price[1:] / price[:-1] - 1) * 100
            if np.nanmean(pct) > 1e-6:
                factorValue = (np.nanmean(Ask_amt)-np.nanmean(Bid_amt))/np.nanstd(Bid_amt)
                factorValue = factorValue * np.nansum(pct)
            else:
                factorValue = (np.nanmean(Bid_amt)-np.nanmean(Ask_amt))/np.nanstd(Ask_amt)
                factorValue = factorValue * np.nansum(pct)
        else:
            factorValue = 0
        factorValue = factorValue * (-1)
        self._addFactorValue(factorValue)

    def __tran(self):
        volume_ask = self._getLastTickData("AskVolume")
        price_ask = self._getLastTickData("AskPrice")
        volume_bid = self._getLastTickData("BidVolume")
        price_bid = self._getLastTickData("BidPrice")
        Ask_amt = volume_ask * price_ask
        Bid_amt = volume_bid * price_bid
        return Ask_amt, Bid_amt