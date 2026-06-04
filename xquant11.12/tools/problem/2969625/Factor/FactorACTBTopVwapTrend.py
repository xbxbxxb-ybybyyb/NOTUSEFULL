from System.Factor import Factor
import numpy as np


class FactorACTBTopVwapTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__tlag = self._getParameter("TransLag")
        self.__lag = self._getParameter("Lag")
        self.__cutoffs = None

        self.__actBAOS = self._getFactor(
            {
                "ClassName": "ActiveABInfoByOrderSmoother",
                "Parameters": {
                    "Lag": self.__tlag,
                    "Target": "Amount",
                    "SmoothObject": "ActiveBidInfoByOrder",
                }
            }
        )

        self.__actBVOS = self._getFactor(
            {
                "ClassName": "ActiveABInfoByOrderSmoother",
                "Parameters": {
                    "Lag": self.__tlag,
                    "Target": "Volume",
                    "SmoothObject": "ActiveBidInfoByOrder",
                }
            }
        )

        self._addIntermediate("TopVwap", [])

    def calculate(self):
        import datetime as dt
        time = self._getLastTickData("Timestamp")
        time = dt.datetime.strftime(dt.datetime.fromtimestamp(time),'%H%M%S')
        if time == '132911':
            print('!')
        top_vwap = self.getIntermediate("TopVwap")
        bid_amount_dict = self.__actBAOS.getLastFactorValue()
        bid_volume_dict = self.__actBVOS.getLastFactorValue()

        tvol = np.nansum([each for bt, each in bid_volume_dict.items() if bid_amount_dict[bt] > self.__cutoffs])
        tamt = np.nansum([each for each in bid_amount_dict.values() if each > self.__cutoffs])

        if tvol > 0:
            top_vwap.append(tamt / tvol)
        else:
            if top_vwap:
                top_vwap.append(top_vwap[-1])
            else:
                top_vwap.append(np.nan)

        sub_top_vwap = top_vwap[-self.__lag:]
        x = np.array(list(range(len(sub_top_vwap))))[~np.isnan(sub_top_vwap)]
        sub_top_vwap = np.array(sub_top_vwap)[~np.isnan(sub_top_vwap)]

        if (len(x) > 2) and (max(sub_top_vwap) - min(sub_top_vwap) > 1e-6):
            factorValue = np.corrcoef(sub_top_vwap, x)[0, 1]
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        mamount = self._getAllHistoricalMinuteData("Amount")
        mdnum = self._getAllHistoricalMinuteData("NumTrades")
        if len(mamount) > 0:
            self.__cutoffs = np.round(np.nanpercentile(mamount / mdnum, 70))
        else:  # 如果前一天没有分钟频数据
            self.__cutoffs = 2e5
