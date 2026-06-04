from System.Factor import Factor
import numpy as np
from scipy.fftpack import fft


class FactorBidFFTAngle(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwap"
            }
        )

    def calculate(self):
        bid_price_adjust = self.__bid_vwap.getFactorValueList()
        bid_price_adjust_fft = fft(np.array(bid_price_adjust))
        bid_price_adjust_fft_angle = np.angle(bid_price_adjust_fft)
        factor_value = np.nanmean(bid_price_adjust_fft_angle[-self.__lag:])
        
        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
