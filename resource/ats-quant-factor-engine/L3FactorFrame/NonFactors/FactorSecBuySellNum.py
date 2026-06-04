import numpy as np
from L3FactorFrame.FactorBase import FactorBase
from L3FactorFrame.tools.DecimalUtil import isEqual, notEqual
from L3FactorFrame.tools.helper_functions import trade_field_agg


class FactorSecBuySellNum(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.num_bids_sec_list = []
        self.num_asks_sec_list = []

    def calculate(self):
        sample_1s_flag = self.getPrevTick("sample_1s_flag")
        if sample_1s_flag == 1:
            order_time = self.getPrevOrder("Timestamp")
            # sample_1s_flag表示超过这一秒的第一条数据，需要扣除这一条
            bs_flags = self.getPrevSecOrder("BSFlag", 1)
            buy_num = bs_flags[bs_flags == 1].sum()
            sell_num = bs_flags[bs_flags == 2].sum()
            self.num_bids_sec_list.append(buy_num)
            self.num_asks_sec_list.append(sell_num)

        # Nonfactor的结果不用存
        # self.addFactorValue(0.0)
