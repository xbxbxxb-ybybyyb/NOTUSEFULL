from System.Factor import Factor
import numpy as np


class FactorPnlVolumeReturnsAmp(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__rlag = self._getParameter("ReturnsLag")
        self.__ilag = self._getParameter("IndexReturnsLag")
        self.__svlag = self._getParameter("ShortVolumeLag")
        self.__lvlag = self._getParameter("LongVolumeLag")
        self.__index_name = self._getParameter("IndexName")

        self._addIntermediate("ReturnsStock", [])
        self._addIntermediate("ReturnsIndex", [])

    def calculate(self):

        rtns_s = self.getIntermediate("ReturnsStock")
        rtns_g = self.getIntermediate("ReturnsIndex")

        lastp = self._getLastNTickData("LastPrice", self.__rlag)
        lastp_g = self._getLastNINFTickData(self.__index_name, "LastPrice", self.__ilag)
        volume = self._getLastNTickData("Volume", self.__lvlag)

        if len(lastp_g) > 0:
            rtns_s.append(lastp[-1] / lastp[0] - 1)
            rtns_g.append(lastp_g[-1] / lastp_g[0] - 1)
            returns_amp = np.nanstd(rtns_s[-self.__lag:]) / np.nanstd(rtns_g[-self.__lag:]) \
                if np.nanstd(rtns_g[-self.__lag:]) > 1e-7 else 0.

            if len(volume) <= self.__svlag:
                vol_amp = np.nanmean(volume[-len(volume)//2:]) / np.nanmean(volume) if np.nanmean(volume) != 0 else 0
            else:
                vol_amp = np.nanmean(volume[-self.__svlag:]) / np.nanmean(volume) if np.nanmean(volume) != 0 else 0
            factorValue = vol_amp * returns_amp
        else:
            rtns_s.append(np.nan)
            rtns_g.append(np.nan)
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)
