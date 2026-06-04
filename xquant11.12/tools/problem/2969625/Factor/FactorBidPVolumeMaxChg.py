from System.Factor import Factor
import numpy as np


class FactorBidPVolumeMaxChg(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__mlag = self._getParameter("MinLag")

        self._addIntermediate("BidPriceList", [])

    def calculate(self):
        tick_time_crt = self._getAllTodayTickData("Time")
        bidp = self._getLastNTickData("BidPrice", self.__mlag * 20 + 1)
        bidv = self._getLastNTickData("BidVolume", self.__mlag * 20 + 1)
        bidp_list = self.getIntermediate("BidPriceList")
        bidp_dict = bidp_list[-1].copy() if len(bidp_list) > 0 else dict()

        if len(tick_time_crt) < self.__mlag * 20:
            bidp_dict.update(self.__update_price_dict(bidp_dict, dict(zip(bidp[-1], bidv[-1]))))
        else:
            bidp_dict.update(self.__update_price_dict(bidp_dict, dict(zip(bidp[-1], bidv[-1])), dict(zip(bidp[0], bidv[0]))))
        bidp_list.append(bidp_dict)

        temp_bidp = np.array(list(bidp_dict.items())).astype(float)
        if len(temp_bidp) > 0:
            maxv = np.nanmax(temp_bidp[:, 1])
            bidp_maxv = np.nanmin(temp_bidp[temp_bidp[:, 1] == maxv, 0])
            factorValue = (bidp[-1][0] / bidp_maxv - 1) * 10
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    @staticmethod
    def __update_price_dict(oldv: dict, addv: dict, delv: dict = None):
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
