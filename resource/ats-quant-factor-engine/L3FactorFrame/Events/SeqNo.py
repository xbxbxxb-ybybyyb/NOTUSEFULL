import numpy as np
from L3FactorFrame.FactorBase import FactorBase

class SeqNo(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)

    def calculate(self):
        ts = self.getPrevTick("SeqNo")
        self.addFactorValue(ts)
