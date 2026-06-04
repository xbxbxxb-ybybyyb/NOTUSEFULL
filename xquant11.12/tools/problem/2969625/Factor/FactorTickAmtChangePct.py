import numpy as np
from System.Factor import Factor


class FactorTickAmtChangePct(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter('Window')

        self.__tickBidAmt = self._getFactor(
            {
                "ClassName": "TickBidAmt"
            }
        )
        self._addIntermediate('ema_ratio', [])

    def calculate(self):
        ema_ratio = self.getIntermediate('ema_ratio')
        tick_bid_amt = self.__tickBidAmt.getFactorValueList()
        if len(tick_bid_amt) > 1:
            last_tick_amt = tick_bid_amt[-2]
            tick_amt = tick_bid_amt[-1]
            if last_tick_amt != 0:
                res = (tick_amt / last_tick_amt - 1) * 100
            else:
                res = 0
        else:
            res = 0
        ema_res = self.ema(res, ema_ratio, self.__window)
        ema_ratio.append(ema_res)

        self._addFactorValue(ema_res)

    def ema(self, input_value, ema_list, length):
        if len(ema_list) == 0:
            return input_value
        elif len(ema_list) < length:
            para = 2.0 / (len(ema_list) + 1)
            value = ema_list[-1] + para * (input_value - ema_list[-1])
            return value
        elif len(ema_list) >= length:
            para = 2.0 / (length + 1)
            value = ema_list[-1] + para * (input_value - ema_list[-1])
            return value


