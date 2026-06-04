import numpy as np
from L3FactorFrame.FactorBase import FactorBase
from L3FactorFrame.tools.DecimalUtil import isEqual, notEqual

class Sample1sFlag(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)

    def calculate(self):
        sample_1s_flag = self.getPrevTick("sample_1s_flag")
        self.addFactorValue(sample_1s_flag)
