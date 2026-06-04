from System.Factor import Factor
import numpy as np


class TransVwapHistorical(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dir = self._getParameter("Direction")
        self.__lag = self._getParameter("Lag")

    def calculate(self):

        existed_tvwap = self.getFactorValueList()

        if len(existed_tvwap) == 0:
            transaction = self._getLastNHistoricalTickData("Transactions", self.__lag)
            trans_vwap_list = []
            for trans in transaction:
                if trans is not None:
                    flag = self._getTransactionData("BSFlag", trans)
                    vol = self._getTransactionData("Volume", trans)
                    dealp = self._getTransactionData("Price", trans)
                    if self.__dir == "Bid":
                        vol_sub = vol[flag == 1]
                        dealp_sub = dealp[flag == 1]
                    elif self.__dir == "Ask":
                        vol_sub = vol[flag == 2]
                        dealp_sub = dealp[flag == 2]
                    else:
                        vol_sub = vol
                        dealp_sub = dealp
                    if len(dealp_sub) > 0:
                        trans_vwap = np.dot(dealp_sub, vol_sub) / np.nansum(vol_sub)
                    else:
                        trans_vwap = np.nan
                else:
                    trans_vwap = np.nan

                trans_vwap_list.append(trans_vwap)

            factorValue = trans_vwap_list
        else:
            factorValue = None

        self._addFactorValue(factorValue)
