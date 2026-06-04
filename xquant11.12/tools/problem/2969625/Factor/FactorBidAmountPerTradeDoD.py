from System.Factor import Factor
import numpy as np
import pandas as pd
import datetime as dt


class FactorBidAmountPerTradeDoD(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__amountPerTradeHistorical = None

        self.__bidDealAmount = self._getFactor(
            {
                "ClassName": "BidDealAmount",
            }
        )
        self._addIntermediate("BidDealAmountList", [])

    def calculate(self):

        bid_deal_amount = self.__bidDealAmount.getLastFactorValue()
        bid_deal_amount_list = self.getIntermediate("BidDealAmountList")
        current_time = self._getLastTickData("Time") // 1e5 * 1e5

        if bid_deal_amount is not None:
            bid_deal_amount_list.append(np.nanmean(list(bid_deal_amount.values())))
        else:
            bid_deal_amount_list.append(0.)

        if self.__amountPerTradeHistorical is not None:
            if current_time in self.__amountPerTradeHistorical and (self.__amountPerTradeHistorical.loc[current_time] > 1e-6):
                factorValue = np.nanmean(bid_deal_amount_list[-self.__lag:]) / self.__amountPerTradeHistorical.loc[current_time]
            elif np.nanmean(self.__amountPerTradeHistorical) > 1e-6:  # 如果没有当前Minute的用全天均值代替
                factorValue = np.nanmean(bid_deal_amount_list[-self.__lag:]) / np.nanmean(self.__amountPerTradeHistorical)
            else:
                factorValue = 0.
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        mamount = self._getAllHistoricalMinuteData("Amount")
        mdnum = self._getAllHistoricalMinuteData("NumTrades")
        mtime = self._getAllHistoricalMinuteData("Time")
        mdate = self._getAllHistoricalMinuteData("Date")

        if len(mamount) > 0:

            valid_minutes = ([int((dt.datetime(1949, 10, 1, 9, 30) + dt.timedelta(minutes=i)).strftime("%H%M%S") + "000") for i in range(120)]
                             + [int((dt.datetime(1949, 10, 1, 13) + dt.timedelta(minutes=i)).strftime("%H%M%S") + "000") for i in range(120)])

            mamt = mamount / mdnum
            np.place(mamt, mdnum == 0, np.nan)

            amount_per_trade_dict = {}
            for date in sorted(set(mdate)):
                idx = mdate == date
                amount_per_trade_dict[date] = pd.Series(mamt[idx], index=mtime[idx])
            amount_per_trade = pd.DataFrame(amount_per_trade_dict).mean(axis=1).reindex(index=valid_minutes)

            self.__amountPerTradeHistorical = amount_per_trade



