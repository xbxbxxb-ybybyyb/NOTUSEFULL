from System.Factor import Factor
import numpy as np


class FactorPnlRevBidVolRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__rlag = self._getParameter("ReturnsLag")
        self.__tlag = self._getParameter("TransLag")
        self.__index_name = self._getParameter("IndexName")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice",
            }
        )

    def calculate(self):

        midp = self.__midPrice.getFactorValueList()[-self.__rlag:]
        bvr_s = self._getLastNINFTickData(self.__index_name, "TransBidVolumeRatio", self.__tlag)

        if (len(bvr_s) > 0) and (np.nanmean(bvr_s) != 0):
            rtns = midp[-1] / midp[0] - 1
            bvr = np.nanmean(bvr_s)
            if (bvr > 0.5) and (rtns < 0):
                factorValue = - (bvr - 0.5) * rtns * 1e3
            elif (bvr < 0.5) and (rtns > 0):
                factorValue = (0.5 - bvr) * rtns * 1e3
            else:
                factorValue = bvr * rtns / 1e1
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
