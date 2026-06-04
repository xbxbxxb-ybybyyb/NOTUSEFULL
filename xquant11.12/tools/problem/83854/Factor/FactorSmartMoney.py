# -*- coding: utf-8 -*-
"""
Created on 2018/4/12
@author: 011668 JiangShuo
"""

from System.Factor import Factor
import numpy as np
import pandas as pd


class FactorSmartMoney(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraWindowSpan = para['TimeWindowSpan']
        self.__n = para['N']
        self.timeWindowSeries = self.getFactorData({"name": "timeWindow", "className": "TimeWindow",
                                                    "paraWindowSpan": self.__paraWindowSpan,
                                                    "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                    "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        self.bar = []
        self.__eps = 1e-5
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        factorManagement.registerFactor(self, para)

    def calculate(self):
        self.bar = self.timeWindowSeries.getLastContent()
        length = min(len(self.bar['close']), self.__n)
        if length > 1:
            open = self.bar['open'][-length:]
            close = self.bar['close'][-length:]
            volume = self.bar['volume'][-length:]
            amt = self.bar['amount'][-length:]
            is_not_valid = False
            for p in close:
                if p <= 0.01:
                    is_not_valid = True
                    break

            if not is_not_valid:
                for p in open:
                    if p <= 0.01:
                        is_not_valid = True
                        break

            if not is_not_valid:
                for v in volume:
                    if v < 0.0:
                        is_not_valid = True
                        break

            if not is_not_valid:
                for a in amt:
                    if a < 0.0:
                        is_not_valid = True
                        break

            if is_not_valid:
                if len(self.getContent()) == 0:
                    smart_money = 0.0
                else:
                    smart_money = self.getLastContent()
            else:
                st = []
                for i in range(0, length):
                    st.append([abs(close[i] / open[i] - 1) / np.sqrt(volume[i]) * 100000 if volume[i] != 0 else 0, volume[i], amt[i]])
                st_matrix = pd.DataFrame(np.array(st))
                st_matrix = st_matrix.sort_values(by=0, ascending=False)
                smart_n = length // 5
                vwap_smart = (sum(st_matrix.iloc[0:smart_n, 2]) + self.__eps) / (sum(st_matrix.iloc[0:smart_n, 1]) + self.__eps)
                vwap_all = (sum(st_matrix.iloc[:, 2]) + self.__eps) / (sum(st_matrix.iloc[:, 1]) + self.__eps)
                smart_money = (vwap_smart + self.__eps) / (vwap_all + self.__eps)
        else:
            smart_money = 0

        self.addData(smart_money, self.__data.getLastTimeStamp())
