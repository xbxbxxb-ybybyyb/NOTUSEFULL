from System.Factor import Factor
import numpy as np


class FactorWeightedBuyDis(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self._addIntermediate("buy_dis", [])

    def calculate(self):
        bid0_price = self._getLastTickData("BidPrice")[0]
        avg_bid_price = self._getLastTickData('AvgBidPrice')
        buy_dis_list = self.getIntermediate("buy_dis")

        buy_dis = (avg_bid_price / bid0_price - 1) * 100 if bid0_price > 1e-6 else 0
        buy_dis_list.append(buy_dis)

        factor_value = np.nanmean(buy_dis_list[-self.__lag:])

        self._addFactorValue(factor_value)
