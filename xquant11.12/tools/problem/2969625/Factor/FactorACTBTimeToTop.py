from System.Factor import Factor
import numpy as np
import datetime as dt


class FactorACTBTimeToTop(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__cutoff = None

        self.__actBIO = self._getFactor(
            {
                "ClassName": "ActiveBidInfoByOrder",
            }
        )
        self._addIntermediate("TopTime", [])

    def calculate(self):

        top_time = self.getIntermediate("TopTime")
        current_timestamp = self._getLastTickData("Timestamp")
        actbao = self.__actBIO.getLastFactorValue()

        if actbao is not None:
            top_time_list = [each[2] for each in actbao.values() if each[0] > self.__cutoff]
            if top_time_list:
                top_time.append(np.nanmean(top_time_list))
            else:
                top_time.append(np.nan)
        else:
            top_time.append(np.nan)

        sub_top_time = top_time[-self.__lag:]
        time_diff = [self.__get_time_diff(each, current_timestamp) for each in sub_top_time if not np.isnan(each)]
        if time_diff:
            factorValue = np.nanmean(time_diff) / 1e2
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        mamount = self._getAllHistoricalMinuteData("Amount")
        mdnum = self._getAllHistoricalMinuteData("NumTrades")
        if len(mamount) > 0:
            self.__cutoff = np.round(np.nanpercentile(mamount / mdnum, 70))
        else:  # 如果前一天没有分钟频数据
            self.__cutoff = 2e5

    @staticmethod
    def __get_time_diff(time1, time2):
        hour1 = dt.datetime.fromtimestamp(time1).hour
        hour2 = dt.datetime.fromtimestamp(time2).hour

        if hour1 < 12 < hour2:
            return time2 - time1 - 5400
        else:
            return time2 - time1
