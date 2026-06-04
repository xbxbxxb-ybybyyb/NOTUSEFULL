from System.Factor import Factor
import numpy as np


class FactorPanFlowKM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("AskVolumeArray", [])
        self._addIntermediate("BidVolumeArray", [])

    def calculate(self):
        askVolumeArray = self.getIntermediate("AskVolumeArray")
        bidVolumeArray = self.getIntermediate("BidVolumeArray")
        askVolume = self._getLastTickData("AskVolume")
        bidVolume = self._getLastTickData("BidVolume")

        if len(askVolume) > 0:
            askVolumeArray.append(sum(askVolume))
        else:
            askVolumeArray.append(0)
        if len(bidVolume) > 0:
            bidVolumeArray.append(sum(bidVolume))
        else:
            bidVolumeArray.append(0)

        L = min(len(askVolumeArray), self.__lag)
        if L < 5:
            if len(self.getFactorValueList()) == 0:
                factorValue = 0
            else:
                factorValue = self.getLastFactorValue()
        else:
            askArray = np.array(askVolumeArray[-L:])
            bidArray = np.array(bidVolumeArray[-L:])
            flowArray = bidArray - askArray
            # panFlowDif = np.diff(flowArray)
            factorValue = np.corrcoef(np.arange(len(flowArray)), flowArray)[0][1]
            if np.isnan(factorValue):
                factorValue = 0

        self._addFactorValue(factorValue)

