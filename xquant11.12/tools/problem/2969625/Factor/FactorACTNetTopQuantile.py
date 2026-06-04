from System.Factor import Factor
import numpy as np


class FactorACTNetTopQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__tlag = self._getParameter("TransLag")
        self.__cutoff = None

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

        self.__actAAOS = self._getFactor(
            {
                "ClassName": "ActiveABInfoByOrderSmoother",
                "Parameters": {
                    "Lag": self.__tlag,
                    "Target": "Amount",
                    "SmoothObject": "ActiveAskInfoByOrder",
                }
            }
        )

        self._addIntermediate("NetTopAmount", [])

    def calculate(self):

        net_top_amount = self.getIntermediate("NetTopAmount")
        bid_amount_dict = self.__actBAOS.getLastFactorValue()
        ask_amount_dict = self.__actAAOS.getLastFactorValue()

        bid_top_amount = [each for each in bid_amount_dict.values() if each > self.__cutoff]
        ask_top_amount = [each for each in ask_amount_dict.values() if each > self.__cutoff]
        net_top_amount.append(np.nansum(bid_top_amount) - np.nansum(ask_top_amount))

        factorValue = sum(np.array(net_top_amount) < net_top_amount[-1]) / len(net_top_amount)

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
