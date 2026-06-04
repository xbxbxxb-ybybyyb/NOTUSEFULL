

import numpy as np
from FactorBase import FactorBase
from DecimalUtil import isEqual, greaterThan, lessThan, equalGreaterThan, equalLessThan, EPSILON
from xquant.xqutils.perf_profile import profile
import pandas as pd

class OneBigOrderExtend1(FactorBase):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        symbol = self.marketDataManager.getSymbol()
        date = self.marketDataManager.getDate()
        self._quantile_df = pd.read_parquet(f"/dfs/group/800657/library/l3_event/event_params/{symbol}.parquet")
        self._quantile_df = self._quantile_df[self._quantile_df["Date"]==date]
        self.askv0_quantile = self._quantile_df["AskV0Q50"].iloc[0]
        self.bidv0_quantile = self._quantile_df["BidV0Q50"].iloc[0]#np.floor(self.getDailyParameterData(f"TBV0Q{self.__quantile}"))
        self.__spread_ratio = config.get("spread_ratio", 3) #连吃多档之间的价差
        self.__interval = config.get("interval", 0.055)
        self.a = config.get("a", 1) #连吃多档之间的价差
        self.b = config.get("b", 0.5) #连吃多档之间的价差
        self.i = 0

    def calculate(self):
        self.i = self.i+1

        askv0_quantile = self.askv0_quantile
        bidv0_quantile = self.bidv0_quantile
        tickDataIndex = self.getPrevTick("SeqNo")

        orderIndex = self.getPrevOrder("SeqNo")
        tradeIndex = self.getPrevTrade("SeqNo")
        cancelIndex = self.getPrevCancel("SeqNo")

        orderBSFlag = self.getPrevOrder("BSFlag")
        cancelBSFlag = self.getPrevCancel("BSFlag")

        tickAskPriceList = self.getPrevNTick("AskPrice", 2)
        tickBidPriceList = self.getPrevNTick("BidPrice", 2)
        tickAskVolumeList = self.getPrevNTick("AskVolume", 2)
        tickBidVolumeList = self.getPrevNTick("BidVolume", 2)

        tickVolumeList = self.getPrevNTick("ttl_volume", 2)

        if orderIndex==1159303:
            a = 1

        columns = ["P0Change", "OneBigTradeVol", "NetBidTrade", "NetBidOrder", "BreakNum", "BreakPricePct", "AskV0", "BidV0", "AskP0", "BidP0"]
        if len(tickAskPriceList) < 2:
            factorValue = [0]*len(columns)
        else:
            factorValue = [0]*len(columns)
            lastTickAskPrice, currentTickAskPrice = tickAskPriceList
            lastTickBidPrice, currentTickBidPrice = tickBidPriceList
            lastTickAskVolume, currentTickAskVolume = tickAskVolumeList
            lastTickBidVolume, currentTickBidVolume = tickBidVolumeList

            if True:#((0 not in currentTickAskPrice[:5]) and (0 not in currentTickBidPrice[:5])):
                lastTickAskP0, lastTickBidP0 = lastTickAskPrice[0], lastTickBidPrice[0]
                currentTickAskP0, currentTickBidP0 = currentTickAskPrice[0], currentTickBidPrice[0]
                lastTickAskV0, lastTickBidV0 = lastTickAskVolume[0], lastTickBidVolume[0]
                currentTickAskV0, currentTickBidV0 = currentTickAskVolume[0], currentTickBidVolume[0]
                cum_vol = tickVolumeList[1] - tickVolumeList[0]

                if isEqual(tickDataIndex, orderIndex):
                    if isEqual(orderBSFlag, 1):
                        localOrderBSFlag = self.getPrevNOrder("BSFlag", 1)
                        localOrderVolume = self.getPrevNOrder("TradeVolume", 1)
                        localOrderType = self.getPrevNOrder("OrderType", 1)
                        localOrderPrice = self.getPrevNOrder("Price", 1)
                        netBidTrade = np.sum(localOrderVolume[localOrderBSFlag == 1]) \
                                       - np.sum(localOrderVolume[(localOrderBSFlag == 2)])
                        netBidVolume = np.sum(localOrderVolume[(localOrderBSFlag == 1) & (
                                (localOrderPrice >= currentTickAskP0 - EPSILON) | (localOrderType == 1))]) \
                                       - np.sum(localOrderVolume[(localOrderBSFlag == 2) & (
                                (localOrderPrice <= currentTickAskP0 + EPSILON) | (localOrderType == 1))])

                        # 买单吃了多档
                        # if cum_vol >= self.a*askv0_quantile and cum_vol >= self.b* currentTickAskV0 and currentTickAskP0>lastTickAskP0+EPSILON:# and (currentTickAskP0/lastTickAskP0-1)*1000>self.__spread_ratio:
                        P0Change = 0
                        if currentTickAskP0>lastTickAskP0+EPSILON:
                            # 连续消耗多档连续性
                            P0Change = 1
                        AskV0 = currentTickAskV0
                        BidV0 = currentTickBidV0
                        AskP0 = currentTickAskP0
                        BidP0 = currentTickBidP0

                        BreakNum = 0
                        BreakPrice = lastTickAskPrice[0]
                        for aidx, askPrice in enumerate(lastTickAskPrice):
                            # 突破的挡位数量不能太小
                            if askPrice < currentTickAskP0 - EPSILON:
                                BreakNum += 1
                                BreakPrice = askPrice
                            else:
                                break
                        BreakPricePct = (BreakPrice-lastTickAskPrice[0])/lastTickAskPrice[0]*1000
                        factorValue = [P0Change, cum_vol, netBidTrade, netBidVolume, BreakNum,  BreakPricePct, AskV0, BidV0, AskP0, BidP0]

                    elif isEqual(orderBSFlag, 2):
                        # if isEqual(currentTickBidP0, lastTickBidP0) \
                        #         and lessThan(currentTickBidV0, lastTickBidV0) \
                        #         and equalGreaterThan(lastTickBidV0 - currentTickBidV0, lastTickBidV0 / 2) \
                        #         and equalGreaterThan(lastTickBidV0 - currentTickBidV0, bidv0_quantile):
                        #     factorValue = -1
                        localOrderBSFlag = self.getPrevNOrder("BSFlag", 1)
                        localOrderVolume = self.getPrevNOrder("TradeVolume", 1)
                        localOrderType = self.getPrevNOrder("OrderType", 1)
                        localOrderPrice = self.getPrevNOrder("Price", 1)

                        netBidTrade = np.sum(localOrderVolume[localOrderBSFlag == 1]) \
                                      - np.sum(localOrderVolume[(localOrderBSFlag == 2)])
                        netBidVolume = np.sum(localOrderVolume[(localOrderBSFlag == 1) & (
                                (localOrderPrice >= currentTickAskP0 - EPSILON) | (localOrderType == 1))]) \
                                       - np.sum(localOrderVolume[(localOrderBSFlag == 2) & (
                                (localOrderPrice <= currentTickAskP0 + EPSILON) | (localOrderType == 1))])

                        # if cum_vol >= self.a*bidv0_quantile and cum_vol >= self.b * currentTickBidV0  and currentTickBidP0<lastTickBidP0-EPSILON:# and (1-currentTickBidP0/lastTickBidP0)*1000 > self.__spread_ratio:
                        P0Change = 0
                        if currentTickBidP0 < lastTickBidP0 - EPSILON:
                            # 连续消耗多档连续性
                            P0Change = 1
                        AskV0 = currentTickAskV0
                        BidV0 = currentTickBidV0
                        AskP0 = currentTickAskP0
                        BidP0 = currentTickBidP0

                        BreakNum = 0  # 被突破的盘口档位
                        BreakPrice = lastTickBidPrice[0]
                        for bidx, bidPrice in enumerate(lastTickBidPrice):
                            if bidPrice > currentTickBidP0 + EPSILON:
                                BreakNum += 1
                                BreakPrice = bidPrice
                            else:
                                break
                        BreakPricePct = (BreakPrice-lastTickBidPrice[0])/lastTickBidPrice[0]*1000
                        factorValue = [P0Change, -cum_vol, netBidTrade, netBidVolume,-BreakNum,  BreakPricePct, AskV0, BidV0, AskP0, BidP0]
                # elif isEqual(tickDataIndex, cancelIndex):
                #     if isEqual(cancelBSFlag, 2):
                #         if greaterThan(currentTickAskP0-EPSILON, lastTickAskP0) and lastTickAskV0>askv0_quantile:
                #             # 撤掉卖一
                #             factorValue = lastTickAskV0/askv0_quantile
                #     elif isEqual(cancelBSFlag, 1):
                #         if lessThan(currentTickBidP0+EPSILON, lastTickBidP0) and lastTickAskP0>bidv0_quantile:
                #             # 撤掉买一
                #             factorValue = -lastTickBidV0/bidv0_quantile
                # else:
                #     pass#raise IndexError("Tick SeqNo not Equal to OrderIndex or CancelIndex!")
        self.addFactorValue(factorValue)
