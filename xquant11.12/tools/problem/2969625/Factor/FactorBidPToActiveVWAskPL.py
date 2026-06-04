# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/18
from System.Factor import Factor
import numpy as np


class FactorBidPToActiveVWAskPL(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("AskTradeAmount", [])
        self._addIntermediate("AskTradeVolume", [])

    def calculate(self):
        askm_list = self.getIntermediate("AskTradeAmount")
        askv_list = self.getIntermediate("AskTradeVolume")

        trade = self._getLastTickData("Transactions")
        if trade is not None:
            tradef = self._getTransactionData("BSFlag", trade)
            tradem = self._getTransactionData("Amount", trade)
            tradev = self._getTransactionData("Volume", trade)
            askm_list.append(np.nansum(tradem[tradef == 2]))
            askv_list.append(np.nansum(tradev[tradef == 2]))
        else:
            askm_list.append(0.)
            askv_list.append(0.)

        bidp = self._getLastTickData("BidPrice")[0]
        if bidp < 0.01:  # 跌停
            last_facv = self.getLastFactorValue()
            if last_facv is not None:
                factorValue = last_facv
            else:
                factorValue = 0.
        else:
            v = np.nansum(askv_list[-self.__lag:])
            if v < 0.01:
                last_facv = self.getLastFactorValue()
                if last_facv is not None:
                    factorValue = last_facv
                else:
                    factorValue = 0.
            else:
                m = np.nansum(askm_list[-self.__lag:])
                trade_vwap = m / v
                factorValue = -(bidp / trade_vwap - 1) * 100

        self._addFactorValue(factorValue)

