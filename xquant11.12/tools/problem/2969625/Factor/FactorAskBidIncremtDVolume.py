from System.Factor import Factor
import numpy as np


class FactorAskBidIncremtDVolume(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lltlag = self._getParameter("LltLag")
        self.__a = 2 / (1 + self.__lltlag)
        self.__askDVolume = self._getFactor(
            {
                "ClassName": "AskIncremtDelegateVolume",
            }
        )
        self.__bidDVolume = self._getFactor(
            {
                "ClassName": "BidIncremtDelegateVolume",
            }
        )
        self._addIntermediate("AskBidIDVolumeRatio", [])

    def calculate(self):

        abidvrList = self.getIntermediate("AskBidIDVolumeRatio")
        adv = self.__askDVolume.getLastFactorValue()
        bdv = self.__bidDVolume.getLastFactorValue()
        factorValueList = self.getFactorValueList()
        if np.abs(adv) + np.abs(bdv) != 0:
            abidvr = (bdv - adv) / (np.abs(adv) + np.abs(bdv))
            abidvrList.append(abidvr)

            abidvrFilterList = list(filter(lambda x: x is not None, abidvrList))
            if (len(factorValueList) < 2) or (len(abidvrFilterList) < 3):
                factorValue = abidvrFilterList[-1]
            else:
                factorValue = self.llt_filter(factorValueList, abidvrFilterList, self.__a)
        else:
            abidvrList.append(None)
            if len(factorValueList) > 0:
                factorValue = factorValueList[-1]
            else:
                factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    @staticmethod
    def llt_filter(llts: list, new_items: list, a: float):
        llt = (a - a * a / 4) * new_items[-1] + a * a / 2 * new_items[-2] - (a - 3 * a * a / 4) * new_items[-3] + \
                  2 * (1 - a) * llts[-1] - (1 - a) ** 2 * llts[-2]
        return llt

