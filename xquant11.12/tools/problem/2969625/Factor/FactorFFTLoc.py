from System.Factor import Factor
import numpy as np
from scipy.fftpack import fft


class FactorFFTLoc(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):

        prec = self._getLastNHistoricalDailyData("PreviousClose", 1)[-1]
        lastp = self._getLastNTickData("LastPrice", self.__lag) / prec

        ffts = fft(lastp)
        amp = np.abs(ffts)
        factorValue = - amp[-1] * np.angle(ffts[-1])

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
