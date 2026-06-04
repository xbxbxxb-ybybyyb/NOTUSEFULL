import numpy as np
from L3FactorFrame.FactorBase import FactorBase
from L3FactorFrame.tools.DecimalUtil import isEqual, notEqual
from L3FactorFrame.tools.helper_functions import trade_field_agg


class FactorSecOrderBook(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.bid_qty_list = []
        self.ask_qty_list = []

    def calculate(self):
        sample_1s_flag = self.getPrevTick("sample_1s_flag")
        if sample_1s_flag == 1:
            bidVolume = self.getPrevNTick("BidVolume",2)[0]
            askVolume = self.getPrevNTick("AskVolume",2)[0]

            self.bid_qty_list.append(bidVolume)
            self.ask_qty_list.append(askVolume)

        # Nonfactor的结果不用存
        # self.addFactorValue(0.0)
