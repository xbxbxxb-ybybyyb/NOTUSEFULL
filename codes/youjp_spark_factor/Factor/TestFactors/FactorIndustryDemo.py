#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/4/21 14:22

from System.Factor import Factor
import numpy as np


class FactorIndustryDemo(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag1 = self._getParameter("Lag1")
        self.__lag2 = self._getParameter("Lag2")
        self.ret_list = []
        self.index_ret_list = []

    def calculate(self):
        price_array = self._getLastNTickData("LastPrice", self.__lag1)
        index_price_array = self._getLastNIndexTickData("SHENWAN2", "LastPrice", self.__lag1)
        self.ret_list.append(self.get_ret(price_array))
        self.index_ret_list.append(self.get_ret(index_price_array))
        if len(self.ret_list) > self.__lag2:
            self.ret_list = self.ret_list[-self.__lag2:]
        if len(self.index_ret_list) > self.__lag2:
            self.index_ret_list = self.index_ret_list[-self.__lag2:]
        factorValue = (np.nanmean(self.ret_list) - np.nanmean(self.index_ret_list)) * 100
        if np.isnan(factorValue):
            factorValue = 0
        self._addFactorValue(factorValue)

    @staticmethod
    def get_ret(price_list):
        if price_list[0] is None or price_list[-1] is None or price_list[0] == 0:
            return 0
        else:
            return price_list[-1] / price_list[0] - 1