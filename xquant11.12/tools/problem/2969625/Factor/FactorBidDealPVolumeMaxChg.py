from System.Factor import Factor
import numpy as np


class FactorBidDealPVolumeMaxChg(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__mlag = self._getParameter("MinLag")

        self.__askPVolume = self._getFactor(
            {
                "ClassName": "AskPVolume",
            }
        )
        self._addIntermediate("AskDPriceList", [])

    def calculate(self):

        tick_time_crt = self._getAllTodayTickData("Time")
        bidp = self._getLastTickData("BidPrice")[0]
        askdpv = self.__askPVolume.getFactorValueList()[-self.__mlag * 20 - 1:]
        askdp_list = self.getIntermediate("AskDPriceList")
        askdp_dict = askdp_list[-1].copy() if len(askdp_list) > 0 else dict()

        if len(tick_time_crt) <= self.__mlag * 20:
            askdp_dict = self.__update_price_dict(askdp_dict, askdpv[-1])
        else:
            askdp_dict = self.__update_price_dict(askdp_dict, askdpv[-1], askdpv[0])
        askdp_list.append(askdp_dict)

        temp_askp = np.array(list(askdp_dict.items())).astype(float)
        if len(temp_askp) > 0:
            maxv = np.nanmax(temp_askp[:, 1])
            askp_maxv = np.nanmin(temp_askp[temp_askp[:, 1] == maxv, 0])
            factorValue = (bidp / askp_maxv - 1) * 100
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
