from System.Factor import Factor
import numpy as np
import datetime as dt


class FactorABDealAmountStructure(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__mlag = self._getParameter("MinLag")
        self.__transDAOQ = self._getFactor(
            {
                "ClassName": "TransDelegateAsk1OrderQueue",
            }
        )
        self.__transDBOQ = self._getFactor(
            {
                "ClassName": "TransDelegateBid1OrderQueue",
            }
        )

    def calculate(self):
        tsp = self._getLastTickData("Timestamp")
        aoq = self.__transDAOQ.getLastFactorValue()[::-1]
        boq = self.__transDBOQ.getLastFactorValue()[::-1]
        ltsp = self.__getLastNMinTimestamp(tsp, self.__mlag)

        ao_list = []
        bo_list = []
        for each in aoq:
            if each[3] > ltsp:
                ao_list.append(each)
            else:
                break
        for each in boq:
            if each[3] > ltsp:
                bo_list.append(each)
            else:
                break

        if len(ao_list) > 0:
            ao_array = np.array(ao_list)
            amt_per_ao = np.nansum(ao_array[:, 1] * ao_array[:, 2]) / len(ao_array)
        else:
            amt_per_ao = 0.
        if len(bo_list) > 0:
            bo_array = np.array(bo_list)
            amt_per_bo = np.nansum(bo_array[:, 1] * bo_array[:, 2]) / len(bo_array)
        else:
            amt_per_bo = 0.

        if (amt_per_ao > 1e-6) or (amt_per_bo > 1e-6):
            factorValue = amt_per_bo / (amt_per_bo + amt_per_ao)
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    @staticmethod
    def __getLastNMinTimestamp(timestamp, nmin):
        hour = dt.datetime.fromtimestamp(timestamp - nmin * 60).hour
        if hour == 12:
            last_timestamp = timestamp - 5400 - nmin * 60
        else:
            last_timestamp = timestamp - nmin * 60
        return last_timestamp
