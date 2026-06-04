from System.Factor import Factor
import numpy as np


class FactorQuoteVMBidPChg(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidPV", [])

    def calculate(self):

        bidpv_list = self.getIntermediate("BidPV")
        bidpv_dict = bidpv_list[-1] if len(bidpv_list) > 0 else dict()

        bidp = self._getLastNTickData("BidPrice", self.__lag + 1)
        bidv = self._getLastNTickData("BidVolume", self.__lag + 1)

        if len(bidp) < self.__lag + 1:
            addv = {bp: bv for bp, bv in zip(bidp[-1], bidv[-1]) if bp > 0.01}
            new_bidpv_dict = self.__update_pv_dict(bidpv_dict, addv)
        else:
            addv = {bp: bv for bp, bv in zip(bidp[-1], bidv[-1]) if bp > 0.01}
            delv = {bp: bv for bp, bv in zip(bidp[0], bidv[0]) if bp > 0.01}
            new_bidpv_dict = self.__update_pv_dict(bidpv_dict, addv, delv)
        bidpv_list.append(new_bidpv_dict)

        if bidp[-1][0] < 0.01:
            last_facv = self.getLastFactorValue()
            if last_facv is not None:
                factorValue = last_facv
            else:
                factorValue = 0.
        else:
            cp = 0.
            cv = 0.
            for p, v in new_bidpv_dict.items():
                if v > cv and p > cp:
                    cv, cp = v, p
            if cp < 0.01:  # 长时间跌停后开板
                last_facv = self.getLastFactorValue()
                if last_facv is not None:
                    factorValue = last_facv
                else:
                    factorValue = 0.
            else:
                factorValue = -(bidp[-1][0] / cp - 1) * 100

        self._addFactorValue(factorValue)

    @staticmethod
    def __update_pv_dict(oldv: dict, addv: dict, delv: dict = None):
        item_p = np.array(sorted(set(oldv.keys()).union(set(addv.keys()))))
        oldv_s = np.array([oldv.get(each, 0) for each in item_p])
        addv_s = np.array([addv.get(each, 0) for each in item_p])
        newv_s = oldv_s + addv_s
        if delv is not None:
            delv_s = np.array([delv.get(each, 0) for each in item_p])
            newv_s = newv_s - delv_s
        item_p = item_p[newv_s != 0]
        newv_s = newv_s[newv_s != 0]
        newv = dict(zip(item_p, newv_s))
        return newv
