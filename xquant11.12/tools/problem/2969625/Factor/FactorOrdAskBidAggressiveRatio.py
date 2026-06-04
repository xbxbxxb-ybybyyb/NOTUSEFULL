import numpy as np
from System.Factor import Factor


class FactorOrdAskBidAggressiveRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("AggressiveRatioList", [])

    def calculate(self):
        askP0 = self._getLastNTickData("AskPrice", 2)[0][0]
        bidP0 = self._getLastNTickData("BidPrice", 2)[0][0]
        if askP0 < 1e-4:
            askP0 = self._getLastTickData("MaxPrice")
        if bidP0 < 1e-4:
            bidP0 = self._getLastTickData("MinPrice")

        orderData = self._getLastTickData("Orders")
        if orderData is not None:
            bsFlag = self._getOrderData("BSFlag", orderData)
            price = self._getOrderData("Price", orderData)
            volume = self._getOrderData("Volume", orderData)
            activeSell = volume[(bsFlag == 2) & (price < bidP0 + 1e-6)].sum()
            activeBuy = volume[(bsFlag == 1) & (price > askP0 - 1e-6)].sum()
            aggressiveRatio = activeSell / activeBuy if activeBuy > 1e-6 else 0
        else:
            aggressiveRatio = None

        aggressiveRatioList = self.getIntermediate("AggressiveRatioList")
        aggressiveRatioList.append(aggressiveRatio)

        filterAggressiveRatioList = list(filter(lambda x: x is not None, aggressiveRatioList))

        factorValue = np.nanmean(np.array(filterAggressiveRatioList[-self.__lag:]))

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)






