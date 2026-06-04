

import numpy as np
from FactorBase import FactorBase
from DecimalUtil import isEqual, greaterThan, lessThan, equalGreaterThan, equalLessThan, EPSILON
from xquant.xqutils.perf_profile import profile
import pandas as pd

class OneBigOrderExtend(FactorBase):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        symbol = self.marketDataManager.getSymbol()
        date = self.marketDataManager.getDate()
        self._quantile_df = pd.read_parquet(f"/dfs/group/800657/library/l3_event/event_params/{symbol}.parquet")
        self._quantile_df = self._quantile_df[self._quantile_df["Date"]==date]
        self.askv0_quantile = self._quantile_df["AskV0Q50"].iloc[0]
        self.bidv0_quantile = self._quantile_df["BidV0Q50"].iloc[0]#np.floor(self.getDailyParameterData(f"TBV0Q{self.__quantile}"))
        self.__spread_ratio = config.get("spread_ratio", 3) #连吃多档之间的价差
        self.__interval = config.get("interval", 20)
        self.a = config.get("a", 2) #连吃多档之间的价差
        self.b = config.get("b", 2) #连吃多档之间的价差
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

        if orderIndex>=248790:
            a = 1

        columns = ["P0Change", "OneBigTradeVol", "NetBidTrade", "NetBidOrder", "BreakNum", "BreakPricePct", "AskV0", "BidV0"]
        if len(tickAskPriceList) < 2:
            factorValue = 0
        else:
            factorValue = 0
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
                        # 买单吃了多档
                        if lastTickAskV0 >= self.a*askv0_quantile and cum_vol >= self.b* max(currentTickAskV0, askv0_quantile) and currentTickAskP0 > lastTickAskP0+EPSILON:# and (currentTickAskP0/lastTickAskP0-1)*1000>self.__spread_ratio:
                            localOrderBSFlag = self.getPrevSecOrder("BSFlag", self.__interval)
                            localOrderType = self.getPrevSecOrder("OrderType", self.__interval)
                            localOrderPrice = self.getPrevSecOrder("Price", self.__interval)
                            localOrderVolume = self.getPrevSecOrder("Volume", self.__interval)
                            netBidVolume = np.sum(localOrderVolume[(localOrderBSFlag == 1) & (
                                        (localOrderPrice >= lastTickAskP0 - EPSILON) | (localOrderType == 1))]) \
                                           - np.sum(localOrderVolume[(localOrderBSFlag == 2) & (
                                        (localOrderPrice <= lastTickAskP0 + EPSILON) | (localOrderType == 1))])-localOrderVolume[-1]/2#扣除大单本身影响
                            if netBidVolume >= max(currentTickAskV0, 2*askv0_quantile):
                                factorValue = 1
                    elif isEqual(orderBSFlag, 2):
                        if lastTickBidV0 >= self.a*bidv0_quantile and cum_vol >= self.b * max(currentTickBidV0, bidv0_quantile)  and currentTickBidP0 < lastTickBidP0-EPSILON:# and (1-currentTickBidP0/lastTickBidP0)*1000 > self.__spread_ratio:
                            localOrderBSFlag = self.getPrevSecOrder("BSFlag", self.__interval)
                            localOrderType = self.getPrevSecOrder("OrderType", self.__interval)
                            localOrderPrice = self.getPrevSecOrder("Price", self.__interval)
                            localOrderVolume = self.getPrevSecOrder("Volume", self.__interval)
                            netAskVolume = np.sum(localOrderVolume[(localOrderBSFlag == 2) & (
                                        (localOrderPrice <= lastTickBidP0 + EPSILON) | (localOrderType == 1))]) \
                                           - np.sum(localOrderVolume[(localOrderBSFlag == 1) & (
                                        (localOrderPrice >= lastTickBidP0 - EPSILON) | (localOrderType == 1))])-localOrderVolume[-1]/2#扣除大单本身影响
                            if netAskVolume>=max(currentTickBidV0, 2*bidv0_quantile):
                                factorValue = -1
                # elif isEqual(tickDataIndex, cancelIndex):
                #     if isEqual(cancelBSFlag, 2):
                #         if greaterThan(currentTickAskP0-EPSILON, lastTickAskP0) and lastTickAskV0>askv0_quantile:
                #             # 撤掉卖一
                #             factorValue = lastTickAskV0/askv0_quantile
                #     elif isEqual(cancelBSFlag, 1):
                #         if lessThan(currentTickBidP0+EPSILON, lastTickBidP0) and lastTickAskP0>bidv0_quantile:
                #             # 撤掉买一
                #             factorValue = -lastTickBidV0/bidv0_quantile
                else:
                    pass#raise IndexError("Tick SeqNo not Equal to OrderIndex or CancelIndex!")
        self.addFactorValue(factorValue)
