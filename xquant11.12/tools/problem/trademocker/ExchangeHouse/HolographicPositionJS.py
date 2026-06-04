import pandas as pd
import numpy as np
from HFDataLoader.Config import STOCK_RAW_ORDER_COLUMNS


class HolographicData:
    def __init__(self):
        self.remain_order = pd.DataFrame(columns=STOCK_RAW_ORDER_COLUMNS + ["RemainQty"])

        self.holographic_buy_detail = dict()
        self.holographic_sell_detail = dict()
        self.holographic_buy_sum = dict()
        self.holographic_sell_sum = dict()
        self.last_price = None  # 当前区间结束时的价格
        self.vol = 0            # 当前区间内的成交量
        self.amt = 0            # 当前区间内的成交额
        self.total_vol = 0      # 当天截止到目前为止的成交量
        self.total_amt = 0      # 当天截止到目前为止的成交额
        self.time = None

    def on_new_period(self, transaction_data_new, order_data_new, time):
        self.time = time
        self.update_pv_info(transaction_data_new)
        self.update_remain_order(transaction_data_new, order_data_new)
        order_buy = self.remain_order[self.remain_order["OrderBSFlag"] == 1.0]
        order_sell = self.remain_order[self.remain_order["OrderBSFlag"] == 2.0]
        self.holographic_buy_detail = self.get_holographic_result(order_buy)
        self.holographic_sell_detail = self.get_holographic_result(order_sell)
        self.process_abnormal_order()  # 处理异常订单
        self.holographic_buy_sum = self.sum_holographic_result(self.holographic_buy_detail)
        self.holographic_sell_sum = self.sum_holographic_result(self.holographic_sell_detail)
    #
    # def get_order_position(self, my_order):
    #     """获取某一个序号的订单，在同一挂单价格中，之前和之后的订单数量"""
    #     my_order = {"MDTime": "094550000", "OrderBSFlag": 1, "OrderPrice": 4.83, "OrderQty": 100,
    #                 "OrderType": 2, "OrderIndex": 33250}

    def update_pv_info(self, transaction_data_new):
        p = transaction_data_new["TradePrice"].values
        v = transaction_data_new["TradeQty"].values
        p_valid = p[p > 0]
        if len(p_valid) > 0:
            self.last_price = p_valid[-1]
        self.vol = np.dot(p > 0, v)
        self.amt = np.dot(p, v)
        if self.vol is None:
            self.vol = 0
        if self.amt is None:
            self.amt = 0
        self.total_vol += self.vol
        self.total_amt += self.amt

    def update_remain_order(self, transaction_data_new, order_data_new):
        transaction_data, order_data = transaction_data_new.copy(), order_data_new.copy()
        order_data["RemainQty"] = order_data["OrderQty"]
        order_data.index = order_data["OrderIndex"]

        if self.remain_order.shape[0] == 0:
            self.remain_order = order_data.copy()
        else:
            self.remain_order = pd.concat([self.remain_order, order_data], axis=0)

        trade_buy_no = transaction_data["TradeBuyNo"].values
        trade_sell_no = transaction_data["TradeSellNo"].values
        trade_qty = transaction_data["TradeQty"].values
        for i in range(transaction_data.shape[0]):
            index_buy = int(trade_buy_no[i])
            index_sell = int(trade_sell_no[i])
            vol = trade_qty[i]
            if index_buy != 0:
                try:
                    self.remain_order.at[index_buy, "RemainQty"] -= vol
                except:
                    print("不存在买盘订单号：Index[{}], vol[{}]".format(index_buy, vol))
                    continue
            if index_sell != 0:
                try:
                    self.remain_order.at[index_sell, "RemainQty"] -= vol
                except:
                    print("不存在卖盘订单号：Index[{}], vol[{}]".format(index_sell, vol))
                    continue

        self.remain_order = self.remain_order[self.remain_order["RemainQty"] != 0]

    def get_holographic_detail(self):
        """返回全息盘口，每一个价格的详细挂单信息"""
        return self.holographic_buy_detail, self.holographic_sell_detail

    def get_holographic_sum(self):
        """返回全息盘口，每一个价格的挂单总量"""
        return self.holographic_buy_sum, self.holographic_sell_sum

    def get_pv_info(self):
        """ 获取当前区间成交量、成交额、累计成交量、累计成交额,
        以及买卖10档盘口的价格和成交量信息，返回一个dict结果"""
        ask_p_list, ask_v_list, bid_p_list, bid_v_list = [], [], [], []
        for i in range(1, 11):
            if len(self.holographic_sell_sum) > i - 1:
                ask_p = list(self.holographic_sell_sum.keys())[i - 1]
                ask_p_list.append(ask_p)
                ask_v_list.append(self.holographic_sell_sum[ask_p])
            else:
                ask_p_list.append(0)
                ask_v_list.append(0)
            if len(self.holographic_buy_sum) > i - 1:
                bid_p = list(self.holographic_buy_sum.keys())[-i]
                bid_p_list.append(bid_p)
                bid_v_list.append(self.holographic_buy_sum[bid_p])
            else:
                bid_p_list.append(0)
                bid_v_list.append(0)
        return {"LastPrice": self.last_price,
                "Volume": self.vol, "Amount": self.amt,
                "TotalVolume": self.total_vol, "TotalAmount": self.total_amt,
                "AskPrice": ask_p_list, "AskVolume": ask_v_list,
                "BidPrice": bid_p_list, "BidVolume": bid_v_list}

    @staticmethod
    def get_holographic_result(order_df):
        order_price = order_df["OrderPrice"].values
        remain_qty = order_df["RemainQty"].values
        price_bs = np.unique(order_price)
        holographic_bs = dict()
        for p in price_bs:
            holographic_bs[p] = []
        for i in range(order_df.shape[0]):
            holographic_bs[order_price[i]].append(remain_qty[i])
        return holographic_bs

    def process_abnormal_order(self):
        if ('092500000' < self.time < '145700000') or self.time > '150000000':
            buy_price = list(self.holographic_buy_detail.keys())
            sell_price = list(self.holographic_sell_detail.keys())
            if len(buy_price) !=0 and len(sell_price) != 0:
                if max(buy_price) > min(sell_price):
                    # print("{}: 数据存在异常，买一价为{}，卖一价为{}".format(self.time, max(buy_price), min(sell_price)))
                    while list(self.holographic_buy_detail.keys())[-1] > list(self.holographic_sell_detail.keys())[0]:
                        # 使用价格优先原则进行撮合，以卖盘往买盘撮合为例
                        b_price = buy_price[-1]
                        s_price = sell_price[0]
                        b_vol = self.holographic_buy_detail[b_price]
                        s_vol = self.holographic_sell_detail[s_price]
                        trade_vol = min(sum(b_vol), sum(s_vol))
                        self.holographic_buy_detail[b_price] = self.list_reduce(b_vol, trade_vol)
                        self.holographic_sell_detail[s_price] = self.list_reduce(s_vol, trade_vol)
                        if len(self.holographic_buy_detail[b_price]) == 0:
                            self.holographic_buy_detail.pop(b_price)
                            buy_price = buy_price[:-1]
                        if len(self.holographic_sell_detail[s_price]) == 0:
                            self.holographic_sell_detail.pop(s_price)
                            sell_price = sell_price[1:]

    @staticmethod
    def sum_holographic_result(holographic_bs):
        price_bs = list(holographic_bs.keys())
        holographic_bs_total = dict()
        for p in price_bs:
            holographic_bs_total[p] = []
        for p in price_bs:
            holographic_bs_total[p] = sum(holographic_bs[p])
        return holographic_bs_total

    @staticmethod
    def list_reduce(ori_list, reduce_num):
        """举例：ori_list = [2, 5, 9, 10, 1]， reduce_num=8， 返回[8, 10, 1]"""
        while ori_list[0] <= reduce_num:
            reduce_num -= ori_list[0]
            ori_list = ori_list[1:]
            if len(ori_list) == 0:
                return []
        ori_list[0] = ori_list[0] - reduce_num
        return ori_list
