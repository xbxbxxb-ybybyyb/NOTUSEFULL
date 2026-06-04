from System.Factor import Factor
import numpy as np
from scipy.fftpack import fft


class FactorFFTLoc_MDF(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):

        prec = self._getLastNHistoricalDailyData("PreviousClose", 1)[-1]
        lastp = self._getLastNTickData("LastPrice", self.__lag)
        lastp = lastp / prec

        ffts = fft(lastp)
        amp = np.abs(ffts)
        factorValue = 0
        if len(ffts) >= 2:
            fft_list = [- amp[-x] * np.angle(ffts[-x]) for x in range(1, min(100, len(ffts)))]
            factorValue = np.nanmean(fft_list)

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
