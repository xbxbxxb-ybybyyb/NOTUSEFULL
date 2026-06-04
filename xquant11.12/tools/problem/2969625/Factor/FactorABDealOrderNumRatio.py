from System.Factor import Factor
import numpy as np
import datetime as dt


class FactorABDealOrderNumRatio(Factor):
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
        import datetime as dt
        time = self._getLastTickData("Timestamp")
        time = dt.datetime.strftime(dt.datetime.fromtimestamp(time),'%H%M%S')
        if time == '131015':
            print('!')
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

        if (len(ao_list) > 0) or (len(bo_list) > 0):
            factorValue = len(bo_list) / (len(bo_list) + len(ao_list))
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
