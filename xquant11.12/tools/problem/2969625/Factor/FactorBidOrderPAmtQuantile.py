from System.Factor import Factor
import numpy as np


class FactorBidOrderPAmtQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__smlag = self._getParameter("SmoothLag")
        self.__transBOI = self._getFactor(
            {
                "ClassName": "TransActiveBidOrderInfo"
            }
        )
        self._addIntermediate("AmtPerBidOrderList", [])

    def calculate(self):

        abo_list = self.getIntermediate("AmtPerBidOrderList")

        boi = self.__transBOI.getLastFactorValue()
        if boi is not None:
            abo_list.append(np.nanmean(list(boi.values())))
        else:
            abo_list.append(0.)

        if abo_list[-1] != 0:
            factorValue = np.nansum(np.array(abo_list) < abo_list[-1] - 1e-6) / len(abo_list)
        else:
            lastValueList = self.getFactorValueList()
            if lastValueList is not None:
                factorValue = np.nanmean(lastValueList[-self.__smlag:])
            else:
                factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
