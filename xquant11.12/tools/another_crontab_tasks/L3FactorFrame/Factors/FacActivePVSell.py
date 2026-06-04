import numpy as np
from L3FactorFrame.FactorBase import FactorBase

class FacActivePVSell(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.__interval = config.get("interval", 3) #10秒
        self.price_spread = config.get("price_spread", 0.0012) # 价差
        self.active_volume = config.get("active_volume", 400)

    def calculate(self):
        tickDataIndex = self.getPrevTick("SeqNo")
        tradeIndex = self.getPrevTrade("SeqNo")
        if tickDataIndex == 250002:
            a = 1

        asks_price = self.getPrevNTick("AskPrice", 2)
        bids_price = self.getPrevNTick("BidPrice", 2)

        trade_bs_flag = self.getPrevSecTrade("BSFlag", self.__interval)
        trade_price = self.getPrevSecTrade("Price", self.__interval)
        trade_volume = self.getPrevSecTrade("Volume", self.__interval)

        if len(asks_price) < 2:
            factor_value = 0.0
        else:
            factor_value = 0.0
            if tickDataIndex == tradeIndex:
                currentTickAskP0, currentTickBidP0 = asks_price[1][0], bids_price[1][0]

                # 条件1：价差
                mid_price = (currentTickAskP0+currentTickBidP0)/2
                if (currentTickAskP0-0.01-(currentTickBidP0+0.01))/ mid_price > self.price_spread:
                    # 条件2：主动买且买入价格高于基准价
                    bids_price = self.getPrevSecTick("BidPrice", self.__interval)
                    asks_price = self.getPrevSecTick("AskPrice", self.__interval)
                    bid_base_price = bids_price[0][0]+0.01
                    ask_base_price = asks_price[0][0]-0.01
                    active_buy_volume =  np.sum(trade_volume[(trade_bs_flag == 1) & (trade_price >= bid_base_price*1.0008)])
                    active_sell_volume =  np.sum(trade_volume[(trade_bs_flag == 2) & (trade_price <= ask_base_price*0.9992)])
                    # 条件3：主动买大于某个值
                    if active_sell_volume > self.active_volume:
                        factor_value = active_sell_volume/(active_buy_volume+active_sell_volume)

        self.addFactorValue(factor_value)
