import numpy as np
from L3FactorFrame.FactorBase import FactorBase
from L3FactorFrame.tools.regression import simpleRegression


class FacNetVCorr2(FactorBase):
    def __init__(self, config, marketDataManager):
        super().__init__(config, marketDataManager)
        self.lag = config.get("lag", 2)*10
        self.net_vol_sec_list = []

    def calculate(self):
        value = 0
        sample_1s_flag = self.getPrevTick("sample_1s_flag")# 说明上一秒的订单已接收完
        tickVolumeList = self.getPrevNTick("ttl_volume", 2)

        if sample_1s_flag == 1:
            order_time = self.getPrevOrder("Timestamp")
            order_bs = self.getPrevOrder("BSFlag")
            order_vol = self.getPrevOrder("Volume")
            if len(tickVolumeList)>1:
                bs_flags = self.getPrevSecOrder("BSFlag", 1+order_time-int(order_time))
                volume = self.getPrevSecOrder("Volume", 1+order_time-int(order_time))

                net_volume = volume[bs_flags==1].sum()-volume[bs_flags==2].sum()
                # 扣除当前订单的影响
                net_volume = net_volume - order_vol if order_bs == 1 else net_volume + order_vol

                self.net_vol_sec_list.append(net_volume)
                if len(self.net_vol_sec_list) > 5:
                    y = np.array(self.net_vol_sec_list[-self.lag:])
                    X = np.arange(1, len(y)+1)
                    value = simpleRegression(y, X)

        self.addFactorValue(value)
