from System.Factor import Factor
import numpy as np


class FactorBidPerValMdf(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__ask_vwap = self._getFactor(
            {
                "ClassName": "AskVwap"
            }
        )
        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwap"
            }
        )

    def calculate(self):
        bid_price_adjust = self.__bid_vwap.getFactorValueList()[-self.__lag:]
        ask_price_adjust = self.__ask_vwap.getFactorValueList()[-self.__lag:]
        bid_price_adjust = [x for x in bid_price_adjust if not np.isnan(x) and x != 0]
        ask_price_adjust = [x for x in ask_price_adjust if not np.isnan(x) and x != 0]
        if len(bid_price_adjust) > 0 and len(ask_price_adjust) > 0:
            if len(bid_price_adjust) < 10 or len(ask_price_adjust) < 10:
                bid_p10 = np.max(bid_price_adjust)
            else:
                bid_p10 = np.nanpercentile(bid_price_adjust, 10)
            factor_value = (ask_price_adjust[0] / bid_p10 - 1) * 100 if bid_p10 > 1e-3 else 0.7
        else:
            factor_value = 0
        self._addFactorValue(factor_value)
