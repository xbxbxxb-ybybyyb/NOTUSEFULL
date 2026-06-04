import numpy as np
from System.Factor import Factor


# 流量：相邻两个Tick新增卖方打对价单量
class AskVolumeDeltaOtherSide(Factor):

    def calculate(self):
        bidp = self._getLastNTickData("BidPrice", 2)
        trans = self._getLastTickData("Transactions")
        if len(bidp) > 1:
            if trans is not None:
                flag = self._getTransactionData("BSFlag", trans)
                tp = self._getTransactionData("Price", trans)
                tv = self._getTransactionData("Volume", trans)
                dealv = np.nansum(tv[(flag == 2) & (tp == bidp[0][0])])
                factorValue = dealv
            else:
                factorValue = 0
        else:
            if trans is not None:
                flag = self._getTransactionData("BSFlag", trans)
                tv = self._getTransactionData("Volume", trans)
                dealv = np.nansum(tv[flag == 2])
                factorValue = dealv
            else:
                factorValue = 0

        self._addFactorValue(factorValue)
