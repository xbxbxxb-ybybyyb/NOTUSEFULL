from System.Factor import Factor
import numpy as np
from scipy.fftpack import fft


class FactorBidDistanceFFTAngle(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwap"
            }
        )
        self._addIntermediate("bid_distance", [])

    def calculate(self):
        bid_price = self._getLastTickData("BidPrice")[0]
        bid_price_adjust = self.__bid_vwap.getLastFactorValue()
        bid_distance_list = self.getIntermediate("bid_distance")
        bid_distance_list.append(bid_price_adjust - bid_price)
        bid_price_adjust_fft = fft(np.array(bid_distance_list[-self.__lag:]))
        bid_price_adjust_fft_angle = np.angle(bid_price_adjust_fft)
        factor_value = bid_price_adjust_fft_angle[-1]

        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
