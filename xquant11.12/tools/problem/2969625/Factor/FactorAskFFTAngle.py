from System.Factor import Factor
import numpy as np
from scipy.fftpack import fft


class FactorAskFFTAngle(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__ask_vwap = self._getFactor(
            {
                "ClassName": "AskVwap"
            }
        )

    def calculate(self):
        ask_price_adjust = self.__ask_vwap.getFactorValueList()
        ask_price_adjust_fft = fft(np.array(ask_price_adjust))
        ask_price_adjust_fft_angle = np.angle(ask_price_adjust_fft)
        weight_value = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6]) / 2.1
        if len(ask_price_adjust_fft_angle) >= 6:
            factor_value = (ask_price_adjust_fft_angle[-6:] * weight_value[-6:]).sum()
        else:
            factor_value = 0.

        if np.isnan(factor_value):
            factor_value = 0.

        self._addFactorValue(factor_value)

