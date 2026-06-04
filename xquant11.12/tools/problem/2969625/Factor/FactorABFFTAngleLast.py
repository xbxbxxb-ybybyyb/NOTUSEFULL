from System.Factor import Factor
import numpy as np
from scipy.fftpack import fft


class FactorABFFTAngleLast(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
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
        ask_price_adjust = self.__ask_vwap.getFactorValueList()
        ask_price_adjust_fft = fft(np.array(ask_price_adjust))
        bid_price_adjust = self.__bid_vwap.getFactorValueList()
        bid_price_adjust_fft = fft(np.array(bid_price_adjust))
        factor_value = (np.angle(bid_price_adjust_fft)[-1] + np.angle(ask_price_adjust_fft)[-1]) / 2
        
        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
