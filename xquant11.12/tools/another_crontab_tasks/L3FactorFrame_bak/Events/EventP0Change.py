import numpy as np
from FactorBase import FactorBase
from DecimalUtil import isEqual, notEqual

class EventP0Change(FactorBase):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        tickDataIndex = self.getPrevTick("SeqNo")
        orderIndex = self.getPrevOrder("SeqNo")
        cancelIndex = self.getPrevCancel("SeqNo")

        tickAskP0List = self.getPrevNTick("AskP0", 2)
        tickBidP0List = self.getPrevNTick("BidP0", 2)
        if len(tickAskP0List) < 2:
            factorValue = 0
        else:
            factorValue = 0
            lastTickAskP0, currentTickAskP0 = tickAskP0List
            lastTickBidP0, currentTickBidP0 = tickBidP0List

            if (notEqual(currentTickAskP0, lastTickAskP0)
                    or notEqual(currentTickBidP0, lastTickBidP0)):
                    factorValue = 2

        self.addFactorValue(factorValue)
