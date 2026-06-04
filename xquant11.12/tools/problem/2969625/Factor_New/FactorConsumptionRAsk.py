from System.Factor import Factor
import numpy as np
import datetime as dt


class FactorConsumptionRAsk(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        askp = self._getLastNTickData("AskPrice", self.__lag + 1)
        askv = self._getLastNTickData("AskVolume", self.__lag + 1)
        ctime = self._getLastTickData("Timestamp")

        if len(askv) == 1:
            factorValue = 0.
        else:
            if askp[0][0] < 0.01:  # 涨停
                facv = self.getFactorValueList()
                if len(facv) > 0:
                    factorValue = np.nanmin(facv)
                else:
                    factorValue = 0.
            else:
                trades = self._getLastNTickData("Transactions", self.__lag)
                bvs = np.array([])
                bts = np.array([])
                avs = np.array([])
                ats = np.array([])
                for trade in trades:
                    if trade is not None:
                        tradef = self._getTransactionData("BSFlag", trade)
                        tradep = self._getTransactionData("Price", trade)
                        tradem = self._getTransactionData("Amount", trade)
                        tradet = self._getTransactionData("Timestamp", trade)
                        bv = tradem[(tradef == 1) & (tradep >= askp[0][0])]
                        bt = tradet[(tradef == 1) & (tradep >= askp[0][0])]
                        av = tradem[(tradef == 2) & (tradep <= askp[0][0])]
                        at = tradet[(tradef == 2) & (tradep <= askp[0][0])]
                        bvs = np.append(bvs, bv)
                        bts = np.append(bts, bt)
                        avs = np.append(avs, av)
                        ats = np.append(ats, at)
                if len(bvs) > 0 and len(avs) > 0:
                    bts_diff = np.array([self.__timediff(each, ctime) for each in bts])
                    ats_diff = np.array([self.__timediff(each, ctime) for each in ats])
                    wb = np.power(np.e, bts_diff / self.__lag / 3 * np.log(0.5))
                    wa = np.power(np.e, ats_diff / self.__lag / 3 * np.log(0.5))
                    factorValue = np.log(np.nansum(bvs * wb) / np.nansum(avs * wa))
                elif len(bvs) > 0:
                    facv = self.getFactorValueList()[-self.__lag:]
                    if len(facv) > 0:
                        factorValue = np.nanmax(facv)
                    else:
                        factorValue = 0.
                else:
                    facv = self.getFactorValueList()[-self.__lag:]
                    if len(facv) > 0:
                        factorValue = np.nanmin(facv)
                    else:
                        factorValue = 0.

        self._addFactorValue(factorValue)

    @staticmethod
    def __timediff(time1, time2):
        hour1 = dt.datetime.fromtimestamp(time1).hour
        hour2 = dt.datetime.fromtimestamp(time2).hour

        if hour1 < 12 < hour2:
            return time2 - time1 - 5400
        else:
            return time2 - time1
