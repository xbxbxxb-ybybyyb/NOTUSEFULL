from System.Factor import Factor
import numpy as np


class FactorTickJump(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__hisTickJump = None
        self._addIntermediate("TickJump", [])

    def calculate(self):
        tick_jump = self.getIntermediate("TickJump")
        tick_time_crt = self._getAllTodayTickData("Time")

        if len(tick_time_crt) == 1:
            temp_lastp = self._getLastNHistoricalTickData("LastPrice", 4800)
            self.__hisTickJump = list(temp_lastp[1:] - temp_lastp[:-1])
            tick_jump.append(None)
        else:
            temp_lastp = self._getLastNTickData("LastPrice", 2)
            tick_jump.append(temp_lastp[-1] - temp_lastp[0])

        tick_jump_all = self.__hisTickJump + tick_jump[1:]
        sub_tick_jump = tick_jump_all[-4800:]
        if np.nanmean(np.abs(sub_tick_jump)) > 0:
            factorValue = np.nanmean(sub_tick_jump[-self.__lag:]) / np.nanmean(np.abs(sub_tick_jump))
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
