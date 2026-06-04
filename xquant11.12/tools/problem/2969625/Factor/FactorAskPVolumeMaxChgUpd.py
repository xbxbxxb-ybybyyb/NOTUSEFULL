from System.Factor import Factor
import numpy as np


class FactorAskPVolumeMaxChgUpd(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__mlag = self._getParameter("MinLag")

        self._addIntermediate("AskPriceList", [])

    def calculate(self):

        tick_time_crt = self._getAllTodayTickData("Time")
        askp = self._getLastNTickData("AskPrice", self.__mlag * 20 + 1)
        askv = self._getLastNTickData("AskVolume", self.__mlag * 20 + 1)
        askp_list = self.getIntermediate("AskPriceList")
        askp_dict = askp_list[-1].copy() if len(askp_list) > 0 else dict()

        if len(tick_time_crt) < self.__mlag * 20:
            askp_dict = self.__update_price_dict(askp_dict, dict(zip(askp[-1], askv[-1])))
        else:
            askp_dict = self.__update_price_dict(askp_dict, dict(zip(askp[-1], askv[-1])), dict(zip(askp[0], askv[0])))
        askp_list.append(askp_dict)

        temp_askp = np.array(list(askp_dict.items())).astype(float)
        if len(temp_askp) > 0:
            maxv = np.nanmax(temp_askp[:, 1])
            askp_maxv = np.nanmin(temp_askp[temp_askp[:, 1] == maxv, 0])
            factorValue = (askp[-1][0] / askp_maxv - 1) * 10
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
