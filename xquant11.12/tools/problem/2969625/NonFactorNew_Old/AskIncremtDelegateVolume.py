from System.Factor import Factor
import numpy as np


class AskIncremtDelegateVolume(Factor):
    def calculate(self):
        askp = self._getLastNTodayTickData("AskPrice", 2)
        askv = self._getLastNTodayTickData("AskVolume", 2)
        if len(askp) == 1:
            factorValue = np.nansum(askv[0])
        else:
            ck = sorted(set(askp[0]).intersection(set(askp[-1])))
            ask_dict_old = dict(zip(askp[0], askv[0]))
            ask_dict_new = dict(zip(askp[-1], askv[-1]))
            askv_old = [ask_dict_old[each] for each in ck]
            askv_new = [ask_dict_new[each] for each in ck]
            factorValue = np.nansum(np.subtract(askv_new, askv_old))

        self._addFactorValue(factorValue)
