# -*- coding: utf-8 -*-
"""
@author: 012807
"""
from System.Factor import Factor
import math
import numpy as np
#
# {"name": "factorMomentum", "className": "FactorMomentum",
#          "indexTradingUnderlying": [0], "indexFactorUnderlying": [],
#          "paraLag": 3, "paraEmaMidPriceLag": 3, "save": True}


class FactorMomentumModified(Factor):  # 因子类
    def __init__(self, para, factorManagement):  # 传入因子参数,归属的因子管理模块，需要用到的其他因子或非因子
        Factor.__init__(self, para, factorManagement)
        # 因子参数
        self.__paraEmaMidPriceLag = para['paraEmaMidPriceLag']
        self.__paraLag = para['paraLag']
        # 因子计算会用到的中间变量,取数据时候要注意会不会出现取出的因子还没有计算出值
        # 如果需要实例化因子作为中间变量，则name不要以factor开头，否则会输出到最终的结果中
        # 如果需要实例化因子或者非因子，需要考虑注册因子的先后顺序，即factorManagement.registerFactor(self)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        paraEmaMidPrice = {"name": "emaMidPrice", "className": "Ema",
                           "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                           "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                           "paraLag": self.__paraEmaMidPriceLag,
                           "paraOriginalData": {"name": "midPrice", "className": "MidPrice",
                                                "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__emaMidPrice = self.getFactorData(paraEmaMidPrice)
        self.__paraMAAmountLag = para["paraMAAmountLag"]
        self.__historyAmount = self.getFactorData({"name": "historyAmount", "className": "HistoryAmount",
                                                   "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                   "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        self.__eps = 1e-5
        factorManagement.registerFactor(self, para)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])

    def calculate(self):
        length = min(len(self.__data.getContent()), self.__paraLag)
        if length > 1:
            ema_price_list = self.__emaMidPrice.getContent()[-length:]
            is_not_valid = False
            for p in ema_price_list:
                if p < 0.01:
                    is_not_valid = True
                    break

            if not is_not_valid:
                for a in self.__historyAmount.getContent()[-length:]:
                    if a < 0:
                        is_not_valid = True
                        break

            if is_not_valid:
                factor_momentum = 0.0
            else:
                lastFactorSpeed = (ema_price_list[-1] / ema_price_list[-length] - 1) / (length / 20)
                amount = math.log((sum(self.__historyAmount.getContent()[-length:]) + self.__eps) / (sum(self.__historyAmount.getContent()[-self.__paraMAAmountLag:]) + self.__eps))
                factor_momentum = lastFactorSpeed * amount
        else:
            factor_momentum = 0.0
        self.addData(factor_momentum, self.__data.getLastTimeStamp())
