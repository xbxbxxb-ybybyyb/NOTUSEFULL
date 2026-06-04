from System.Factor import Factor
import numpy as np


class BidIncremtDelegateVolume(Factor):
    def calculate(self):
        bidp = self._getLastNTodayTickData("BidPrice", 2)
        bidv = self._getLastNTodayTickData("BidVolume", 2)
        if len(bidp) == 1:
            factorValue = np.nansum(bidv[0])
        else:
            ck = sorted(set(bidp[0]).intersection(set(bidp[-1])))
            bid_dict_old = dict(zip(bidp[0], bidv[0]))
            bid_dict_new = dict(zip(bidp[-1], bidv[-1]))
            bidv_old = [bid_dict_old[each] for each in ck]
            bidv_new = [bid_dict_new[each] for each in ck]
            factorValue = np.nansum(np.subtract(bidv_new, bidv_old))

        self._addFactorValue(factorValue)

