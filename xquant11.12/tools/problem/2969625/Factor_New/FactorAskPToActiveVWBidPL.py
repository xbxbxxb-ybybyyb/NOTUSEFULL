# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/18
from System.Factor import Factor
import numpy as np


class FactorAskPToActiveVWBidPL(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidTradeAmount", [])
        self._addIntermediate("BidTradeVolume", [])

    def calculate(self):
        bidm_list = self.getIntermediate("BidTradeAmount")
        bidv_list = self.getIntermediate("BidTradeVolume")

        trade = self._getLastTickData("Transactions")
        if trade is not None:
            tradef = self._getTransactionData("BSFlag", trade)
            tradem = self._getTransactionData("Amount", trade)
            tradev = self._getTransactionData("Volume", trade)
            bidm_list.append(np.nansum(tradem[tradef == 1]))
            bidv_list.append(np.nansum(tradev[tradef == 1]))
        else:
            bidm_list.append(0.)
            bidv_list.append(0.)

        askp = self._getLastTickData("AskPrice")[0]
        if askp < 0.01:  # 涨停
            last_facv = self.getLastFactorValue()
            if last_facv is not None:
                factorValue = last_facv
            else:
                factorValue = 0.
        else:
            v = np.nansum(bidv_list[-self.__lag:])
            if v < 0.01:
                last_facv = self.getLastFactorValue()
                if last_facv is not None:
                    factorValue = last_facv
                else:
                    factorValue = 0.
            else:
                m = np.nansum(bidm_list[-self.__lag:])
                trade_vwap = m / v
                factorValue = -(askp / trade_vwap - 1) * 100

        self._addFactorValue(factorValue)

