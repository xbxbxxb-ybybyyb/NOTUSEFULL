import numpy as np
from L3FactorFrame.FactorBase import FactorBase
from L3FactorFrame.tools.DecimalUtil import isEqual, notEqual
from L3FactorFrame.tools.helper_functions import trade_field_agg


class FactorSecTradeAgg(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.trade_buy_money_list = []
        self.trade_sell_money_list = []
        self.trade_buy_num_list = []
        self.trade_sell_num_list = []
        self.trade_buy_volume_list = []
        self.trade_sell_volume_list = []


    def calculate(self):
        timestamps = self.getPrevNTick("Timestamp", 2)
        sample_1s_flag = self.getPrevTick("sample_1s_flag")
        seq_no = self.getPrevTick("SeqNo")
        if seq_no==920706:
            a = 1
        if sample_1s_flag == 1:
            if len(timestamps)==2:
                sec_elapse = int(timestamps[1])-int(timestamps[0])
                for i in range(sec_elapse-1):
                    self.trade_buy_money_list.append(0)
                    self.trade_sell_money_list.append(0)
                    self.trade_buy_num_list.append(0)
                    self.trade_sell_num_list.append(0)
                    self.trade_buy_volume_list.append(0)
                    self.trade_sell_volume_list.append(0)
                
            trade_time = self.getPrevTrade("Timestamp")
            # sample_1s_flag表示超过这一秒的第一条数据，需要扣除这一条
            trade_qtys = self.getPrevSecTrade("Volume", 1, end_timestamp=trade_time)
            trade_moneys = self.getPrevSecTrade("Amount", 1, end_timestamp=trade_time)
            trade_sides = self.getPrevSecTrade("BSFlag", 1, end_timestamp=trade_time)

            active_buy_money, active_sell_money, active_buy_num, active_sell_num, active_buy_volume, active_sell_volume = \
                trade_field_agg(trade_qtys, trade_moneys, trade_sides)

            self.trade_buy_money_list.append( active_buy_money)
            self.trade_sell_money_list.append(active_sell_money)
            self.trade_buy_num_list.append(active_buy_num)
            self.trade_sell_num_list.append(active_sell_num)
            self.trade_buy_volume_list.append(active_buy_volume)
            self.trade_sell_volume_list.append(active_sell_volume)

        # Nonfactor的结果不用存
        # self.addFactorValue(0.0)
