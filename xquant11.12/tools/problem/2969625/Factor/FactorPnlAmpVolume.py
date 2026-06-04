from System.Factor import Factor
import numpy as np


class FactorPnlAmpVolume(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__slag = self._getParameter("ShortVLag")
        self.__llag = self._getParameter("LongVLag")
        self.__ilag = self._getParameter("IndexLag")
        self.__index_name = self._getParameter("IndexName")

        self._addIntermediate("MinVolume", [])

    def calculate(self):

        m_volume_list = self.getIntermediate("MinVolume")
        vol = self._getLastNTickData("Volume", self.__slag)
        lastp_g = self._getLastNINFTickData(self.__index_name, "LastPrice", self.__ilag)

        vol = np.nanmean(vol)
        m_volume_list.append(vol)

        if len(lastp_g) > 0:
            vol_list = np.array(m_volume_list[-self.__llag:])
            vol_qtl = np.nansum(vol_list < vol_list[-1]) / len(vol_list)
            rtns_g = (lastp_g[-1] / lastp_g[0] - 1) * 1e2
            factorValue = rtns_g * vol_qtl * 1e2
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
