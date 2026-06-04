import numpy as np
from FactorBase import FactorBase
from DecimalUtil import isEqual, notEqual

class DateTime(FactorBase):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        ts = self.getPrevTick("DateTime")
        self.addFactorValue(ts)
