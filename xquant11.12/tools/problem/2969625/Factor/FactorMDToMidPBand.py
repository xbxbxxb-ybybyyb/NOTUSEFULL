from System.Factor import Factor
import numpy as np


class FactorMDToMidPBand(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__mlag = self._getParameter("MinuteLag")
        self.__dlag = self._getParameter("DayLag")
        self.__scale = self._getParameter("Scale")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice",
            }
        )
        self.__historical_rtns = None
        self._addIntermediate("TReturn", [])

    def calculate(self):
        rtns_list = self.getIntermediate("TReturn")

        bidp = self._getLastTickData("BidPrice")[0]
        askp = self._getLastTickData("AskPrice")[0]
        bidp = bidp if bidp > 0.01 else self._getLastTickData("MinPrice")
        askp = askp if askp > 0.01 else self._getLastTickData("MaxPrice")

        midp = self.__midPrice.getFactorValueList()[- 20 * self.__mlag:]
        rtns = midp[-1] / midp[0] - 1

        # 加入最新
        if len(midp) == 20 * self.__mlag:
            rtns_list.append(rtns)
        else:
            rtns_list.append(np.nan)

        sub_rtn = np.append(self.__historical_rtns, rtns_list)[- 240 * self.__dlag:]
        mvol = np.nanstd(sub_rtn / 20 / self.__mlag * len(midp))

        if mvol > 0:

            expr_high = midp[0] * (1 + mvol * self.__scale)
            expr_low = midp[0] * (1 - mvol * self.__scale)

            if askp < expr_low:
                factorValue = -(askp / expr_low - 1) * 1e3
            elif bidp > expr_high:
                factorValue = -(bidp / expr_high - 1) * 1e3
            else:
                factorValue = - rtns

        else:
            factorValue = - rtns

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        mclosep = self._getAllHistoricalMinuteData("ClosePrice")
        mdate = self._getAllHistoricalMinuteData("Date")
        date_list = sorted(set(mdate))
        mrtns = np.array([])
        for date in date_list:
            sub_mclosep = mclosep[mdate == date]
            mrtns = np.append(mrtns, sub_mclosep[self.__mlag:] / sub_mclosep[:-self.__mlag] - 1)
        # 没有分钟数据时为全nan
        self.__historical_rtns = mrtns
