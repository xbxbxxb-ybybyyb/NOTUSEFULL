import numpy as np
from FactorBase import FactorBase
from DecimalUtil import isEqual, notEqual

class Timestamp(FactorBase):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        ts = self.getPrevTick("Timestamp")
        self.addFactorValue(ts)
