from System.Factor import Factor
import numpy as np


class FactorVolumeOutbreakCurrent(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__vmlag = self._getParameter("VolumeMLag")
        self.__clag = self._getParameter("CompLag")
        self.__mpthrd = self._getParameter("MidPriceThrd")

        self._addIntermediate("MinVolume", [])

    def calculate(self):
        t_volume = self._getLastNTickData("Volume", self.__vmlag * 20)
        m_volume_crt = np.nanmean(t_volume)

        m_volume_list = self.getIntermediate("MinVolume")
        m_volume_list.append(m_volume_crt)
        m_volume_s = m_volume_list[-self.__clag * 20:]

        if np.nanmean(m_volume_s) == 0:
            factorValue = 0
        else:
            volume_qtl = m_volume_crt / np.nanmean(m_volume_s)
            lastp_s = self._getAllTodayTickData("LastPrice")
            if len(lastp_s) == 1:
                factorValue = 0
            else:
                lastp_crt = lastp_s[-1]
                lastp_s = lastp_s[:-1]
                lastp_qtl = sum(lastp_s <= lastp_crt) / len(lastp_s)

                if lastp_qtl < self.__mpthrd:
                    factorValue = volume_qtl * lastp_qtl * 1e1
                elif lastp_qtl > 1 - self.__mpthrd:
                    factorValue = - volume_qtl * lastp_qtl * 1e1
                else:
                    factorValue = volume_qtl * lastp_qtl / 1e3

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
