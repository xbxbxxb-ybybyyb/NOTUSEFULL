from System.Factor import Factor
import numpy as np


class FactorQuoteVMAskPChg(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("AskPV", [])

    def calculate(self):

        askpv_list = self.getIntermediate("AskPV")
        askpv_dict = askpv_list[-1] if len(askpv_list) > 0 else dict()

        askp = self._getLastNTickData("AskPrice", self.__lag + 1)
        askv = self._getLastNTickData("AskVolume", self.__lag + 1)

        if len(askp) < self.__lag + 1:
            addv = {ap: av for ap, av in zip(askp[-1], askv[-1]) if ap > 0.01}
            new_askpv_dict = self.__update_pv_dict(askpv_dict, addv)
        else:
            addv = {ap: av for ap, av in zip(askp[-1], askv[-1]) if ap > 0.01}
            delv = {ap: av for ap, av in zip(askp[0], askv[0]) if ap > 0.01}
            new_askpv_dict = self.__update_pv_dict(askpv_dict, addv, delv)
        askpv_list.append(new_askpv_dict)

        if askp[-1][0] < 0.01:
            last_facv = self.getLastFactorValue()
            if last_facv is not None:
                factorValue = last_facv
            else:
                factorValue = 0.
        else:
            cp = 0.
            cv = 0.
            for p, v in new_askpv_dict.items():
                if v > cv and p > cp:
                    cv, cp = v, p
            if cp < 0.01:  # 长时间涨停后开板
                last_facv = self.getLastFactorValue()
                if last_facv is not None:
                    factorValue = last_facv
                else:
                    factorValue = 0.
            else:
                factorValue = -(askp[-1][0] / cp - 1) * 100

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
