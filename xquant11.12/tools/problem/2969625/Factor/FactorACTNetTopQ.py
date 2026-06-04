from System.Factor import Factor
import numpy as np


class FactorACTNetTopQ(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__cutoff = None

        self.__activeTradeBidIdxM = self._getFactor(
            {
                "ClassName": "ActiveTradeBidIdxM",
            }
        )

        self.__activeTradeAskIdxM = self._getFactor(
            {
                "ClassName": "ActiveTradeAskIdxM",
            }
        )

        self._addIntermediate("NetTopAmount", [])

    def calculate(self):

        net_top_amount = self.getIntermediate("NetTopAmount")
        bid_amount = np.array(list(self.__activeTradeBidIdxM.getLastFactorValue().values()))
        ask_amount = np.array(list(self.__activeTradeAskIdxM.getLastFactorValue().values()))

        bid_top_amount = bid_amount[bid_amount > self.__cutoff]
        ask_top_amount = ask_amount[ask_amount > self.__cutoff]
        net_top_amount.append(np.nansum(bid_top_amount) - np.nansum(ask_top_amount))

        if len(net_top_amount) > 10:
            nv = sum(np.array(net_top_amount[-self.__lag:]) < net_top_amount[-1]) / len(net_top_amount[-self.__lag:])
            facv = self.getFactorValueList()
            factorValue = self.__ema(nv, facv, 5)
        else:
            factorValue = 0.5

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        mamount = self._getAllHistoricalMinuteData("Amount")
        mdnum = self._getAllHistoricalMinuteData("NumTrades")
        if len(mamount) > 0:
            self.__cutoff = np.round(np.nanpercentile(mamount / mdnum, 70))
        else:  # 如果前一天没有分钟频数据
            self.__cutoff = 2e5

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x
