from System.Factor import Factor
import numpy as np


class FactorAskBidOrderVolumeVolatility(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        volume = np.nanmean(self._getAllTodayTickData("Volume")[:5])
        volume_all = np.nanmean(self._getAllTodayTickData("Volume"))
        ask_deal_volume = []
        bid_deal_volume = []

        transactionData = self._getLastNTickData("Transactions", self.__lag)
        for transaction in transactionData:
            if transaction is not None:
                BSFlag = self._getTransactionData("BSFlag", transaction)
                transVolume = self._getTransactionData("Volume", transaction)
                ask_deal_volume_list = transVolume[BSFlag == 2].tolist()
                bid_deal_volume_list = transVolume[BSFlag == 1].tolist()
                ask_deal_volume.extend(ask_deal_volume_list)
                bid_deal_volume.extend(bid_deal_volume_list)

        if (len(ask_deal_volume) > 0) and (len(bid_deal_volume) > 0):
            if volume != 0:
                factorValue = (np.nanstd(bid_deal_volume) - np.nanstd(ask_deal_volume)) / volume
            elif volume_all != 0:
                factorValue = (np.nanstd(bid_deal_volume) - np.nanstd(ask_deal_volume)) / volume_all
            else:
                lastValue = self.getLastFactorValue()
                if lastValue is not None:
                    factorValue = lastValue
                else:
                    factorValue = 0
        else:
            lastValue = self.getLastFactorValue()
            if lastValue is not None:
                factorValue = lastValue
            else:
                factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
