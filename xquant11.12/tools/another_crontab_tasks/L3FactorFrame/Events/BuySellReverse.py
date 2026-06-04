

import numpy as np
from L3FactorFrame.FactorBase import FactorBase
from L3FactorFrame.tools.DecimalUtil import isEqual, greaterThan, lessThan, equalGreaterThan, equalLessThan, EPSILON
import pandas as pd

class BuySellReverse(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.__interval = config.get("interval", 0.055)
        self.pressure_multi = config.get("pressure_multi", 20)#买卖方盘口量不均衡
        self.net_multi = config.get("net_multi", 2)
        symbol = self.marketDataManager.getSymbol()
        date = self.marketDataManager.getDate()
        self._quantile_df = pd.read_parquet(f"/dfs/group/800657/library/l3_event/event_params/{symbol}.parquet")
        self._quantile_df = self._quantile_df[self._quantile_df["Date"]==date]
        self.askv0_quantile =self._quantile_df["AskV0Q50"].iloc[0]
        self.bidv0_quantile = self._quantile_df["BidV0Q50"].iloc[0]#np.floor(self.getDailyParameterData(f"TBV0Q{self.__quantile}"))


    def calculate(self):
        askv0_quantile = self.askv0_quantile
        bidv0_quantile = self.bidv0_quantile
        tickDataIndex = self.getPrevTick("SeqNo")
        if isEqual(tickDataIndex, 7425029):
            a = 1
        orderIndex = self.getPrevOrder("SeqNo")
        cancelIndex = self.getPrevCancel("SeqNo")

        orderBSFlag = self.getPrevOrder("BSFlag")

        tickAskPriceList = self.getPrevNTick("AskPrice", 2)
        tickBidPriceList = self.getPrevNTick("BidPrice", 2)
        tickAskVolumeList = self.getPrevNTick("AskVolume", 2)
        tickBidVolumeList = self.getPrevNTick("BidVolume", 2)
        tickVolumeList = self.getPrevNTick("ttl_volume" , 2)

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
                currentTickAskV1, currentTickBidV1 = currentTickAskVolume[1], currentTickBidVolume[1]
                changeVolume = tickVolumeList[1] - tickVolumeList[0] #当前逐笔变化的成交量

                if isEqual(tickDataIndex, orderIndex):
                    if isEqual(orderBSFlag, 1):
                        # 波段满足：当档位变化时，判断价差是否超过一定幅度。计算累计n秒内的主买否远小于当前卖方一档量【假设主买力量碰到对手方支撑位】
                        spreadRatio = (currentTickAskP0 - currentTickBidP0) / currentTickBidP0 * 1000
                        if changeVolume > 0:# and spreadRatio>self.__spread_ratio:
                            localOrderBSFlag = self.getPrevSecOrder("BSFlag", self.__interval)
                            localOrderType = self.getPrevSecOrder("OrderType", self.__interval)
                            localOrderPrice = self.getPrevSecOrder("Price", self.__interval)
                            localOrderVolume = self.getPrevSecOrder("Volume", self.__interval)
                            bidVolume = np.sum(localOrderVolume[(localOrderBSFlag == 1)])
                            askVolume = np.sum(localOrderVolume[(localOrderBSFlag == 2)])
                            netBidVolume = bidVolume-askVolume
                            #  and equalLessThan(askVolume, currentTickBidV0)
                            if netBidVolume<bidv0_quantile*self.net_multi and equalGreaterThan(currentTickAskV0, (bidv0_quantile)*self.pressure_multi):
                                factorValue = -1


                    elif isEqual(orderBSFlag, 2):
                        spreadRatio = (currentTickAskP0 - currentTickBidP0) / currentTickBidP0 * 1000
                        if changeVolume > 0:# and spreadRatio>self.__spread_ratio:
                            localOrderBSFlag = self.getPrevSecOrder("BSFlag", self.__interval)
                            localOrderType = self.getPrevSecOrder("OrderType", self.__interval)
                            localOrderPrice = self.getPrevSecOrder("Price", self.__interval)
                            localOrderVolume = self.getPrevSecOrder("Volume", self.__interval)
                            bidVolume = np.sum(localOrderVolume[(localOrderBSFlag == 1)])
                            askVolume = np.sum(localOrderVolume[(localOrderBSFlag == 2)])
                            netAskVolume = askVolume - bidVolume

                            # and (equalLessThan(bidVolume, currentTickAskV0)
                            if netAskVolume<askv0_quantile*self.net_multi and equalGreaterThan(currentTickBidV0, (askv0_quantile)*self.pressure_multi):
                                factorValue = 1

        self.addFactorValue(factorValue)
