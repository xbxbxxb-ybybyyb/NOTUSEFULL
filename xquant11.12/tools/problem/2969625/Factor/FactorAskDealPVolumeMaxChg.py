from System.Factor import Factor
import numpy as np


class FactorAskDealPVolumeMaxChg(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__mlag = self._getParameter("MinLag")

        self.__bidPVolume = self._getFactor(
            {
                "ClassName": "BidPVolume",
            }
        )
        self._addIntermediate("BidDPriceList", [])

    def calculate(self):

        tick_time_crt = self._getAllTodayTickData("Time")
        askp = self._getLastTickData("AskPrice")[0]
        biddpv = self.__bidPVolume.getFactorValueList()[-self.__mlag * 20 - 1:]
        biddp_list = self.getIntermediate("BidDPriceList")
        biddp_dict = biddp_list[-1].copy() if len(biddp_list) > 0 else dict()

        if len(tick_time_crt) <= self.__mlag * 20:
            biddp_dict = self.__update_price_dict(biddp_dict, biddpv[-1])
        else:
            biddp_dict = self.__update_price_dict(biddp_dict, biddpv[-1], biddpv[0])
        biddp_list.append(biddp_dict)

        temp_bidp = np.array(list(biddp_dict.items())).astype(float)
        if len(temp_bidp) > 0:
            maxv = np.nanmax(temp_bidp[:, 1])
            bidp_maxv = np.nanmin(temp_bidp[temp_bidp[:, 1] == maxv, 0])
            factorValue = (askp / bidp_maxv - 1) * 100
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    @staticmethod
    def __update_price_dict(oldv: dict, addv: dict = None, delv: dict = None):
        newv = oldv.copy()
        if addv is not None:
            item_p = np.array(sorted(set(newv.keys()).union(set(addv.keys()))))
            newv_s = np.array([newv.get(each, 0) for each in item_p])
            addv_s = np.array([addv.get(each, 0) for each in item_p])
            newv_s = newv_s + addv_s
            newv = dict(zip(item_p, newv_s))
        if delv is not None:
            item_p = np.array(sorted(set(newv.keys()).union(set(delv.keys()))))
            newv_s = np.array([newv.get(each, 0) for each in item_p])
            delv_s = np.array([delv.get(each, 0) for each in item_p])
            newv_s = newv_s - delv_s
            item_p = item_p[newv_s != 0]
            newv_s = newv_s[newv_s != 0]
            newv = dict(zip(item_p, newv_s))
        return newv
