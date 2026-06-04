from System.Factor import Factor
import numpy as np
import datetime as dt


class FactorBidDealWaitingTime(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidDealTime", [])
        self._early_order_dict = None
        self._noon_order_dict = None

    def calculate(self):

        bid_deal_time = self.getIntermediate("BidDealTime")
        trans = self._getLastTickData("Transactions")
        orders = self._getAllTodayTickData("Orders")[::-1]

        if (self._early_order_dict is None) and (self._getLastTickData("Time") < 113000000):
            early_order = self._getEarlyDataMorning("Orders")
            if early_order is not None:
                early_order_index = self._getOrderData("OrderIndex", early_order)
                early_order_time = self._getOrderData("Timestamp", early_order)
                self._early_order_dict = dict(zip(early_order_index, early_order_time))
            else:
                self._early_order_dict = dict()

        if (self._noon_order_dict is None) and (self._getLastTickData("Time") > 113000000):
            noon_order = self._getEarlyDataAfternoon("Orders")
            if noon_order is not None:
                noon_order_index = self._getOrderData("OrderIndex", noon_order)
                noon_order_time = self._getOrderData("Timestamp", noon_order)
                self._noon_order_dict = dict(zip(noon_order_index, noon_order_time))
            else:
                self._noon_order_dict = dict()

        if trans is not None:

            this_trans_index = list(self._getTransactionData("BidOrder", trans))
            this_trans_time = list(self._getTransactionData("Timestamp", trans))
            this_trans_time_dict = dict(zip(this_trans_index, this_trans_time))  # 成交时间，对于重复的BidOrder，取最后一笔时间
            remain_trans_index = set(this_trans_index)

            this_order_time_dict = dict()
            # 早盘的
            if self._early_order_dict is not None:
                this_order_time_dict.update({idx: self._early_order_dict[idx] for idx in remain_trans_index if idx in self._early_order_dict})
                remain_trans_index = remain_trans_index.difference(set(this_order_time_dict.keys()))
            # 午盘的
            if self._noon_order_dict is not None:
                this_order_time_dict.update({idx: self._noon_order_dict[idx] for idx in remain_trans_index if idx in self._noon_order_dict})
                remain_trans_index = remain_trans_index.difference(set(this_order_time_dict.keys()))
            # 从后往前查找
            for order in orders:
                if order is not None:
                    order_time = self._getOrderData("Timestamp", order)
                    order_index = self._getOrderData("OrderIndex", order)
                    order_dict = dict(zip(order_index, order_time))
                    this_order_time_dict.update({idx: order_dict[idx] for idx in remain_trans_index if idx in order_dict})
                    remain_trans_index = remain_trans_index.difference(set(this_order_time_dict.keys()))
                    if len(remain_trans_index) == 0:
                        break
                    if min(remain_trans_index) > min(order_index):
                        break

            this_deal_time = np.nanmean([self.__getTimeDiff(each_v, this_trans_time_dict[each_k])
                                         for each_k, each_v in this_order_time_dict.items()])

        else:
            this_deal_time = np.nan

        bid_deal_time.append(this_deal_time)

        if np.any(~np.isnan(bid_deal_time[-self.__lag:])):
            factorValue = np.nanmean(bid_deal_time[-self.__lag:]) / 10
        else:
            factorValue = 0.

        self._addFactorValue(factorValue)

    @staticmethod
    def __getTimeDiff(time1, time2):
        hour1 = dt.datetime.fromtimestamp(time1).hour
        hour2 = dt.datetime.fromtimestamp(time2).hour
        if hour1 < 12 < hour2:
            time_diff = time2 - time1 - 5400
        else:
            time_diff = time2 - time1
        return time_diff
