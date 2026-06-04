from System.Factor import Factor
import numpy as np


class FactorACTNetTailQuantile(Factor):
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

        self._addIntermediate("NetTailAmount", [])

    def calculate(self):

        net_tail_amount = self.getIntermediate("NetTailAmount")
        bid_amount_dict = self.__actBAOS.getLastFactorValue()
        ask_amount_dict = self.__actAAOS.getLastFactorValue()

        bid_tail_amount = [each for each in bid_amount_dict.values() if each < self.__cutoff]
        ask_tail_amount = [each for each in ask_amount_dict.values() if each < self.__cutoff]
        net_tail_amount.append(np.nansum(ask_tail_amount) - np.nansum(bid_tail_amount))

        factorValue = sum(np.array(net_tail_amount) < net_tail_amount[-1]) / len(net_tail_amount)

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        mamount = self._getAllHistoricalMinuteData("Amount")
        mdnum = self._getAllHistoricalMinuteData("NumTrades")
        if len(mamount) > 0:
            self.__cutoff = np.round(np.nanpercentile(mamount / mdnum, 30))
        else:  # 如果前一天没有分钟频数据
            self.__cutoff = 4e4
