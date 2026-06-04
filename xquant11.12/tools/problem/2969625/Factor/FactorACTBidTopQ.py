from System.Factor import Factor
import numpy as np


class FactorACTBidTopQ(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__cutoffs = None

        self.__activeTradeBidIdxM = self._getFactor(
            {
                "ClassName": "ActiveTradeBidIdxM",
            }
        )
        self._addIntermediate("TopAmount", [])

    def calculate(self):

        top_amount = self.getIntermediate("TopAmount")
        bid_amount = np.array(list(self.__activeTradeBidIdxM.getLastFactorValue().values()))

        top_amount.append(np.nansum(bid_amount[bid_amount > self.__cutoffs]))

        if len(top_amount) > 10:
            nv = np.nansum(top_amount[-self.__lag:] < top_amount[-1]) / len(top_amount[-self.__lag:])
            facv = self.getFactorValueList()
            factorValue = self.__ema(nv, facv, 5)
        else:
            factorValue = 0.5

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        mamount = self._getAllHistoricalMinuteData("Amount")
        mdnum = self._getAllHistoricalMinuteData("NumTrades")
        if len(mamount) > 0:
            self.__cutoffs = np.round(np.nanpercentile(mamount / mdnum, 70))
        else:  # 如果前一天没有分钟频数据
            self.__cutoffs = 2e5

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x
