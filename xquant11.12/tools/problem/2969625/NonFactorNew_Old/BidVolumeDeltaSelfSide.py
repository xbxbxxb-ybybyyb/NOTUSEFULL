import numpy as np
from System.Factor import Factor


# 流量：相邻两个Tick新增买方本方单量
class BidVolumeDeltaSelfSide(Factor):

    def calculate(self):
        bidv = self._getLastNTickData("BidVolume", 2)
        bidp = self._getLastNTickData("BidPrice", 2)
        trans = self._getLastTickData("Transactions")
        if len(bidv) > 1:
            if trans is not None:
                flag = self._getTransactionData("BSFlag", trans)
                tp = self._getTransactionData("Price", trans)
                tv = self._getTransactionData("Volume", trans)
                dealv = np.nansum(tv[(flag == 2) & (tp == bidp[0][0])])
                ind = bidp[-1] == bidp[0][0]
                if np.any(ind):
                    factorValue = bidv[-1][ind][0] - bidv[0][0] + dealv
                else:
                    factorValue = 0 - bidv[0][0] + dealv
            else:
                factorValue = 0
        else:
            factorValue = bidv[0][0]

        self._addFactorValue(factorValue)
