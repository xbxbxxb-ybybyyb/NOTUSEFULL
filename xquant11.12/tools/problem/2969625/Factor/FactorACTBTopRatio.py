from System.Factor import Factor
import numpy as np


class FactorACTBTopRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__tlag = self._getParameter("TransLag")
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
        self._addIntermediate("TopAmount", [])

    def calculate(self):

        top_amount = self.getIntermediate("TopAmount")
        bid_amount_dict = self.__actBAOS.getLastFactorValue()

        top_amount.append(np.nansum([each for each in bid_amount_dict.values() if each > self.__cutoffs]))

        if np.nanmean(top_amount[-self.__lag:]) > 0:
            factorValue = top_amount[-1] / np.nanmean(top_amount[-self.__lag:])
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        mamount = self._getAllHistoricalMinuteData("Amount")
        mdnum = self._getAllHistoricalMinuteData("NumTrades")
        if len(mamount) > 0:
            self.__cutoffs = np.round(np.nanpercentile(mamount / mdnum, 70))
        else:  # 如果前一天没有分钟频数据
            self.__cutoffs = 2e5