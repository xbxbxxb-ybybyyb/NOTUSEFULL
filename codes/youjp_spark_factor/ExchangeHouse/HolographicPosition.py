import pandas as pd
import numpy as np
import copy


class HolographicData:
    ''''
    (1) 主要耗时在matchmaking_tradeoff中
    (2) transaction比order提前到来，存储历史的transaction，order来了后再交易掉；order比transaction提起到来，只能等待，模拟盘口比实际盘口厚。
    '''
    def __init__(self, position_num=10):

        self.last_price = None  # 当前区间结束时的价格
        self.vol = 0  # 当前区间内的成交量
        self.amt = 0  # 当前区间内的成交额
        self.total_vol = 0  # 当天截止到目前为止的成交量
        self.total_amt = 0  # 当天截止到目前为止的成交额
        self.time = None
        self.position_num = position_num  # 盘口档位数，默认为十档盘口

        self.history_order_cols = ["OrderBSFlag", "OrderPrice", "OrderQty", "OrderType", "OrderIndex"]
        self.history_order_cols_index = dict(zip(self.history_order_cols, np.arange(len(self.history_order_cols))))
        self.history_order = np.array([])
        self.buy_order_qty = dict()
        self.sell_order_qty = dict()
        self.buy_order_index = dict()
        self.sell_order_index = dict()
        self.market_price_buy_order_qty = dict()  ## market_price = {index:qty}
        self.market_price_sell_order_qty = dict()  ## market_price = {index:qty}
        self.market_price_buy_order_type = dict()  ## market_price = {index:type}，更细致处理需要用到。
        self.market_price_sell_order_type = dict()  ## market_price = {index:type}，更细致的处理需要用到

        # 依据buy_order_qty，buy_order_index和market_price_buy_order_qty生成每次的全息盘口
        self.holographic_buy_qty = dict()
        self.holographic_sell_qty = dict()

        ## transaction比order提前到来，找不到订单号。
        self.transaction_before_order = dict()

    def on_new_period(self, transaction_data_new, order_data_new, time):
        self.time = time
        self.update_pv_info(transaction_data_new)
        self.update_orderbook(order_data_new)
        self.matchmaking_tradeoff(transaction_data_new)
        self.process_abnormal_order()

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

    def get_holographic_detail(self):
        """返回全息盘口，每一个价格的详细挂单信息"""
        buy_num = len(self.market_price_buy_order_qty)
        sell_num = len(self.market_price_sell_order_qty)
        if (buy_num == 0) and (sell_num == 0):
            return self.buy_order_qty, self.sell_order_qty
        elif (buy_num != 0) and (sell_num == 0):
            holographic_buy_qty = self.composite_holographic(bsflag=1)
            return holographic_buy_qty, self.sell_order_qty
        elif (buy_num == 0) and (sell_num != 0):
            holographic_sell_qty = self.composite_holographic(bsflag=2)
            return self.buy_order_qty, holographic_sell_qty
        else:
            holographic_buy_qty = self.composite_holographic(bsflag=1)
            holographic_sell_qty = self.composite_holographic(bsflag=2)
            return holographic_buy_qty, holographic_sell_qty

    def composite_holographic(self, bsflag):
        '''
        composite
        self.market_price_buy_order_qty
        self.buy_order_qty
        '''
        if bsflag == 1:
            holographic_buy_qty = copy.deepcopy(self.buy_order_qty)
            min_buy_price = min(holographic_buy_qty)
            market_price_index = sorted(self.market_price_buy_order_qty)
            for index in market_price_index:
                holographic_buy_qty[min_buy_price].append(self.market_price_buy_order_qty[index])
            return holographic_buy_qty
        elif bsflag == 2:
            holographic_sell_qty = copy.deepcopy(self.sell_order_qty)
            max_sell_price = max(holographic_sell_qty)
            market_price_index = sorted(self.market_price_sell_order_qty)
            for index in market_price_index:
                holographic_sell_qty[max_sell_price].append(self.market_price_sell_order_qty[index])
            return holographic_sell_qty

    def get_pv_info(self):
        """ 获取当前区间成交量、成交额、累计成交量、累计成交额,
        以及买卖10档盘口的价格和成交量信息，返回一个dict结果"""
        ask_p_list, ask_v_list, bid_p_list, bid_v_list = [], [], [], []
        sell_price_list = sorted(self.sell_order_qty)
        buy_price_list = sorted(self.buy_order_qty)
        market_buy_vol = sum(self.market_price_buy_order_qty.values())
        market_sell_vol = sum(self.market_price_sell_order_qty.values())
        for i in range(1, self.position_num + 1):
            if len(sell_price_list) > i - 1:
                ask_p = sell_price_list[i - 1]
                ask_p_list.append(ask_p)
                ask_v_list.append(sum(self.sell_order_qty[ask_p]))
            else:
                ask_p_list.append(0)
                ask_v_list.append(0)
            if len(buy_price_list) > i - 1:
                bid_p = buy_price_list[-i]
                bid_p_list.append(bid_p)
                bid_v_list.append(sum(self.buy_order_qty[bid_p]))
            else:
                bid_p_list.append(0)
                bid_v_list.append(0)
        if len(sell_price_list) < self.position_num:
            ask_v_list[-1] = ask_v_list[-1] + market_sell_vol
        if len(buy_price_list) < self.position_num:
            bid_v_list[-1] = bid_v_list[-1] + market_buy_vol
        return {"LastPrice": self.last_price,
                "Volume": self.vol, "Amount": self.amt,
                "TotalVolume": self.total_vol, "TotalAmount": self.total_amt,
                "AskPrice": ask_p_list, "AskVolume": ask_v_list,
                "BidPrice": bid_p_list, "BidVolume": bid_v_list}

    def update_orderbook(self, order_df):
        '''
        update history_order:先按OrderPrice分类；再按OrderBSFlag
        主要是针对市价委托不同策略的处理
        上交所2种: 五档即成剩余转限，五档即成剩余撤销
        深交所5种:本方最优，对手方最优，五档即成剩余撤销，即时成交剩余撤销，全额成交或撤销
        self.history_order_cols =  ["OrderBSFlag", "OrderPrice", "OrderQty", "OrderType", "OrderIndex"]
        '''
        order_df = order_df[self.history_order_cols].values
        if len(self.history_order) == 0:
            self.history_order = order_df
        else:
            self.history_order = np.r_[self.history_order, order_df]

        ## update history_order_book
        order_bsflag = order_df[:, self.history_order_cols_index['OrderBSFlag']]
        order_price = order_df[:, self.history_order_cols_index['OrderPrice']]
        order_qty = order_df[:, self.history_order_cols_index['OrderQty']]
        order_type = order_df[:, self.history_order_cols_index['OrderType']]
        order_index = order_df[:, self.history_order_cols_index['OrderIndex']]

        for i in range(order_df.shape[0]):
            if order_type[i] == 2:
                ## limit_price_order
                if order_bsflag[i] == 1:
                    if order_price[i] in self.buy_order_qty.keys():
                        self.buy_order_qty[order_price[i]].append(order_qty[i])
                        self.buy_order_index[order_price[i]].append(order_index[i])
                    else:
                        self.buy_order_qty[order_price[i]] = [order_qty[i]]
                        self.buy_order_index[order_price[i]] = [order_index[i]]
                elif order_bsflag[i] == 2:
                    if order_price[i] in self.sell_order_qty.keys():
                        self.sell_order_qty[order_price[i]].append(order_qty[i])
                        self.sell_order_index[order_price[i]].append(order_index[i])
                    else:
                        self.sell_order_qty[order_price[i]] = [order_qty[i]]
                        self.sell_order_index[order_price[i]] = [order_index[i]]
            else:
                if order_bsflag[i] == 1:
                    self.market_price_buy_order_qty[order_index[i]] = order_qty[i]
                    self.market_price_buy_order_type[order_index[i]] = order_type[i]
                elif order_bsflag[i] == 2:
                    self.market_price_sell_order_qty[order_index[i]] = order_qty[i]
                    self.market_price_sell_order_type[order_index[i]] = order_type[i]

    def matchmaking_tradeoff(self, transaction_df):
        '''
        撮合：按TradeBuy/SellNo分别处理，通过history_order找到OrderPrice后，按此分类。
        '''
        transaction_df = transaction_df[['TradeBuyNo', 'TradeSellNo', 'TradeQty']].values
        buy_tradeno = transaction_df[:, 0]
        sell_tradeno = transaction_df[:, 1]
        trade_qty = transaction_df[:, 2]
        OrderIndex_index = self.history_order_cols_index['OrderIndex']
        OrderPrice_index = self.history_order_cols_index['OrderPrice']
        OrderType_index = self.history_order_cols_index['OrderType']
        for i in range(transaction_df.shape[0]):
            buy_no = buy_tradeno[i]
            if (buy_no != 0):
                try:
                    buy_price, order_type = self.history_order[self.history_order[:, OrderIndex_index] == buy_no, :][
                        0, [OrderPrice_index, OrderType_index]]
                    if order_type == 2:
                        buy_index = self.buy_order_index[buy_price].index(buy_no)
                        remain_qty = max(self.buy_order_qty[buy_price][buy_index] - trade_qty[i], 0)
                        if remain_qty == 0:
                            del self.buy_order_qty[buy_price][buy_index]
                            del self.buy_order_index[buy_price][buy_index]
                        else:
                            self.buy_order_qty[buy_price][buy_index] = remain_qty
                        if len(self.buy_order_qty[buy_price]) == 0:
                            del self.buy_order_qty[buy_price]
                            del self.buy_order_index[buy_price]
                    else:
                        remain_qty = self.market_price_buy_order_qty[buy_no] - trade_qty[i]
                        if remain_qty == 0:
                            del self.market_price_buy_order_qty[buy_no]
                            del self.market_price_buy_order_type[buy_no]
                        else:
                            self.market_price_buy_order_qty[buy_no] = remain_qty
                except IndexError:
                    self.transaction_before_order[buy_no]=trade_qty[i]
                    print("不存在买盘订单号：Index[{}]".format(buy_no))

            sell_no = sell_tradeno[i]
            if (sell_no != 0):
                try:
                    sell_price, order_type = self.history_order[self.history_order[:, OrderIndex_index] == sell_no, :][
                        0, [OrderPrice_index, OrderType_index]]
                    if order_type == 2:
                        sell_index = self.sell_order_index[sell_price].index(sell_no)
                        remain_qty = max(self.sell_order_qty[sell_price][sell_index] - trade_qty[i], 0)
                        if remain_qty == 0:
                            del self.sell_order_qty[sell_price][sell_index]
                            del self.sell_order_index[sell_price][sell_index]
                        else:
                            self.sell_order_qty[sell_price][sell_index] = remain_qty
                        if len(self.sell_order_qty[sell_price]) == 0:
                            del self.sell_order_qty[sell_price]
                            del self.sell_order_index[sell_price]
                    else:
                        remain_qty = self.market_price_sell_order_qty[sell_no] - trade_qty[i]
                        if remain_qty == 0:
                            del self.market_price_sell_order_qty[sell_no]
                            del self.market_price_sell_order_type[sell_no]
                        else:
                            self.market_price_sell_order_qty[sell_no] = remain_qty
                except IndexError:
                    self.transaction_before_order[sell_no] = trade_qty[i]
                    print("不存在卖盘订单号：Index[{}]".format(sell_no))

        if len(self.transaction_before_order)!=0:
            OrderBSFlag_index= self.history_order_cols_index["OrderBSFlag"]
            for trans_no in self.transaction_before_order:
                try:
                    trans_price, order_type,bsflag = self.history_order[self.history_order[:, OrderIndex_index] == trans_no, :][
                        0, [OrderPrice_index, OrderType_index,OrderBSFlag_index]]
                    if bsflag==1:
                        if order_type == 2:
                            buy_index = self.buy_order_index[trans_price].index(trans_no)
                            remain_qty = max(
                                self.buy_order_qty[trans_price][buy_index] - self.transaction_before_order[trans_no], 0)
                            if remain_qty == 0:
                                del self.buy_order_qty[trans_price][buy_index]
                                del self.buy_order_index[trans_price][buy_index]
                            else:
                                self.buy_order_qty[trans_price][buy_index] = remain_qty
                            if len(self.buy_order_qty[trans_price]) == 0:
                                del self.buy_order_qty[trans_price]
                        else:
                            remain_qty = self.market_price_buy_order_qty[trans_no] - self.transaction_before_order[
                                trans_no]
                            if remain_qty == 0:
                                del self.market_price_buy_order_qty[trans_no]
                                del self.market_price_buy_order_type[trans_no]
                            else:
                                self.market_price_buy_order_qty[trans_no] = remain_qty
                        del self.transaction_before_order[trans_no]
                    elif bsflag==2:
                        if order_type == 2:
                            sell_index = self.sell_order_index[trans_price].index(trans_no)
                            remain_qty = max(self.sell_order_qty[trans_price][sell_index] - self.transaction_before_order[trans_no], 0)
                            if remain_qty == 0:
                                del self.sell_order_qty[trans_price][sell_index]
                                del self.sell_order_index[trans_price][sell_index]
                            else:
                                self.sell_order_qty[trans_price][sell_index] = remain_qty
                            if len(self.sell_order_qty[trans_price]) == 0:
                                del self.sell_order_qty[trans_price]
                        else:
                            remain_qty = self.market_price_sell_order_qty[trans_no] - self.transaction_before_order[trans_no]
                            if remain_qty == 0:
                                del self.market_price_sell_order_qty[trans_no]
                                del self.market_price_sell_order_type[trans_no]
                            else:
                                self.market_price_sell_order_qty[trans_no] = remain_qty
                        del self.transaction_before_order[trans_no]
                except IndexError:
                    print("历史transaction不存在订单号：Index[{}]".format(trans_no))

    def process_abnormal_order(self):
        if ('092500000' < self.time < '145700000') or self.time > '150000000':
            if len(self.buy_order_qty) != 0 and len(self.sell_order_qty) != 0:
                if max(self.buy_order_qty) > min(self.sell_order_qty):
                    print(
                        "{}: 数据存在异常，买一价为{}，卖一价为{}".format(self.time, max(self.buy_order_qty), min(self.sell_order_qty)))
                    buy_price = sorted(self.buy_order_qty.keys())
                    sell_price = sorted(self.sell_order_qty.keys())
                    while buy_price[-1] > sell_price[0]:
                        # 使用价格优先原则进行撮合，以卖盘往买盘撮合为例
                        b_price = buy_price[-1]
                        s_price = sell_price[0]
                        b_vol = self.buy_order_qty[b_price]
                        s_vol = self.sell_order_qty[s_price]
                        b_index = self.buy_order_index[b_price]
                        s_index = self.sell_order_index[s_price]
                        trade_vol = min(sum(b_vol), sum(s_vol))
                        self.buy_order_qty[b_price], self.buy_order_index[b_price] = self.list_reduce(b_vol, b_index,
                                                                                                      trade_vol)
                        self.sell_order_qty[s_price], self.sell_order_index[s_price] = self.list_reduce(s_vol, s_index,
                                                                                                        trade_vol)
                        if len(self.buy_order_qty[b_price]) == 0:
                            del self.buy_order_qty[b_price]
                            del self.buy_order_index[b_price]
                            buy_price = buy_price[:-1]
                            if len(buy_price) == 0:
                                print('buy_order has been eaten')
                                break
                        if len(self.sell_order_qty[s_price]) == 0:
                            del self.sell_order_qty[s_price]
                            del self.sell_order_index[s_price]
                            sell_price = sell_price[1:]
                            if len(sell_price) == 0:
                                print('sell_order has been eaten')
                                break

    @staticmethod
    def list_reduce(ori_list, index_list, reduce_num):
        """举例：ori_list = [2, 5, 9, 10, 1]， reduce_num=8， 返回[8, 10, 1]"""
        while ori_list[0] <= reduce_num:
            reduce_num -= ori_list[0]
            ori_list = ori_list[1:]
            index_list = index_list[1:]
            if len(ori_list) == 0:
                return [], []
        ori_list[0] = ori_list[0] - reduce_num
        return ori_list, index_list



