from System.Factor import Factor
import numpy as np


class Factor40RealReverseAskAmt(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self.__askAmtPerTrade = self._getFactor(
            {
                "ClassName": "AskAmtPerTrade"
            }
        )
        self.__MidPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        price = np.array(self.__MidPrice.getFactorValueList()[-(self.__window + 1):])
        if len(price) >= 2:
            pct = (price[1:] / price[:-1] - 1) * 100
            askAmtPerTradeList = self.__askAmtPerTrade.getFactorValueList()
            long_amt = np.array(askAmtPerTradeList[-len(pct):])
            if len(long_amt) == len(pct):
                bottom_pct = np.nansum(
                    pct[long_amt < np.nanpercentile(long_amt, 40) + 1e-5])  # 取等号时Python浮点数漂移导致和Java代码计算结果对不上
                top_pct = np.nansum(pct[long_amt > np.nanpercentile(long_amt, 60) - 1e-5])
                factorValue = top_pct - bottom_pct
            else:
                factorValue = 0
        else:
            factorValue = 0
        factorValue = -1 * factorValue
        self._addFactorValue(factorValue)