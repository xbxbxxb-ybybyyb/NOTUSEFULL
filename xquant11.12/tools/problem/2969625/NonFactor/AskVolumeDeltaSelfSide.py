import numpy as np
from System.Factor import Factor


# 流量：相邻两个Tick新增卖方本方单量
class AskVolumeDeltaSelfSide(Factor):

    def calculate(self):
        askv = self._getLastNTickData("AskVolume", 2)
        askp = self._getLastNTickData("AskPrice", 2)
        trans = self._getLastTickData("Transactions")
        if len(askv) > 1:
            if trans is not None:
                flag = self._getTransactionData("BSFlag", trans)
                tp = self._getTransactionData("Price", trans)
                tv = self._getTransactionData("Volume", trans)
                dealv = np.nansum(tv[(flag == 1) & (tp == askp[0][0])])
                ind = askp[-1] == askp[0][0]
                if np.any(ind):
                    factorValue = askv[-1][ind][0] - askv[0][0] + dealv
                else:
                    factorValue = 0 - askv[0][0] + dealv
            else:
                factorValue = 0
        else:
            factorValue = askv[0][0]

        self._addFactorValue(factorValue)
