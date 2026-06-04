# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/18
from System.Factor import Factor
import numpy as np


class FactorBidPToActiveVMAskPL(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__activeTradeAskPV = self._getFactor(
            {
                "ClassName": "ActiveTradeAskPV",
            }
        )

        self._addIntermediate("AskPV", [])

    def calculate(self):
        askpv_list = self.getIntermediate("AskPV")
        askpv_dict = askpv_list[-1] if len(askpv_list) > 0 else dict()

        trade_pv = self.__activeTradeAskPV.getFactorValueList()[-self.__lag-1:]
        if len(trade_pv) < self.__lag + 1:
            new_askpv_dict = self.__update_pv_dict(askpv_dict, trade_pv[-1])
        else:
            new_askpv_dict = self.__update_pv_dict(askpv_dict, trade_pv[-1], trade_pv[0])
        askpv_list.append(new_askpv_dict)

        bidp = self._getLastTickData("BidPrice")[0]
        if bidp < 0.01:
            last_facv = self.getLastFactorValue()
            if last_facv is not None:
                factorValue = last_facv
            else:
                factorValue = 0.
        else:
            cp = 0.
            cv = 0.
            for p, v in new_askpv_dict.items():
                if v > cv and p > cp:
                    cv, cp = v, p
            if cp < 0.01:  # 没有Trade
                factorValue = 0.
            else:
                factorValue = -(bidp / cp - 1) * 100

        self._addFactorValue(factorValue)

    @staticmethod
    def __update_pv_dict(oldv: dict, addv: dict, delv: dict = None):
        item_p = np.array(sorted(set(oldv.keys()).union(set(addv.keys()))))
        oldv_s = np.array([oldv.get(each, 0) for each in item_p])
        addv_s = np.array([addv.get(each, 0) for each in item_p])
        newv_s = oldv_s + addv_s
        if delv is not None:
            delv_s = np.array([delv.get(each, 0) for each in item_p])
            newv_s = newv_s - delv_s
        item_p = item_p[newv_s != 0]
        newv_s = newv_s[newv_s != 0]
        newv = dict(zip(item_p, newv_s))
        return newv
