from System.Factor import Factor
import numpy as np


class FactorACTATailQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__tlag = self._getParameter("TransLag")
        self.__cutoffs = None

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
        self._addIntermediate("TailAmount", [])

    def calculate(self):

        tail_amount = self.getIntermediate("TailAmount")
        ask_amount_dict = self.__actAAOS.getLastFactorValue()

        tail_amount.append(np.nansum([each for each in ask_amount_dict.values() if each < self.__cutoffs]))

        factorValue = sum(np.array(tail_amount) < tail_amount[-1]) / len(tail_amount)

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        mamount = self._getAllHistoricalMinuteData("Amount")
        mdnum = self._getAllHistoricalMinuteData("NumTrades")
        if len(mamount) > 0:
            self.__cutoffs = np.round(np.nanpercentile(mamount / mdnum, 30))
        else:  # 如果前一天没有分钟频数据
            self.__cutoffs = 4e4
