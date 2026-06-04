"""
2020.1.14修复问题：临近涨跌停状态时，买或卖没有10档盘口，全部以0填充
2020.1.20修复问题：order委托，以市价单委托的价格为0.0或1.0，需要进行处理
2020.1.20发现问题：存在order数据与transaction数据不同时到来的问题
"""
from HFDataLoader.Config import MAX_FRAME_LENGTH
from HFDataLoader.Config import STOCK_RAW_TICK_COLUMNS, STOCK_RAW_TRANSACTIONS_COLUMNS, STOCK_RAW_ORDER_COLUMNS
from HFDataLoader.Config import CBOND_RAW_TICK_COLUMNS, CBOND_RAW_TRANSACTIONS_COLUMNS, CBOND_RAW_ORDER_COLUMNS
from HFDataLoader.Config import ALIGN_STOCK_COLUMNS, ALIGN_CBOND_COLUMNS
from HFDataLoader.Config import TickMonitor
from HFDataLoader.DataUtil import tickdata_OHL_filter, generate_timestamp
from ExchangeHouse.HolographicPosition import HolographicData

import os
import datetime as dt
import numpy as np
import pandas as pd
import Utils.HelpFunc as Util
from xquant.factordata import FactorData
from xquant.marketdata import MarketData
from xquant.bonddata import BondData
from xquant.compute.sparkmr import remote_print


class MockTickData:
    def __init__(self, code, mock_freq=3, mock_lag=None, monitor=False):
        self.code = code
        self.mock_freq = mock_freq
        self.mock_lag = mock_lag
        self.monitor = monitor
        self.code_type = Util.get_code_type(self.code)
        assert self.code_type in ["CBOND", "STOCK"], " Only CBond or Stock in SZ Support Mock Data "
        self.is_sz_code = Util.is_sz_code(self.code)
        assert self.is_sz_code, " Only Codes in SZ Support Mock Data "

        self.fa = FactorData()
        self.mdp = None
        self.bd = None
        if self.code_type == "STOCK":
            self.mdp = MarketData()
        elif self.code_type == "CBOND":
            self.bd = BondData()

        self.is_executor = "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ

    def load_stock_tick_by_frame(self, start_date, end_date):
        '''
        载入股票一段交易日中所有Tick数据
        '''
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, MAX_FRAME_LENGTH)
        # 对各个分组分别取数据
        sub_tick_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            # 读取原始股票的Tick数据
            start_date_time = "{0} {1}".format(sub_start_date, "000001000")
            end_date_time = "{0} {1}".format(sub_end_date, "235959000")
            sub_tick_df = self.mdp.get_data_by_time_frame("Stock", self.code, start_date_time, end_date_time, ['1','2','3','4','5'])
            # 对关键字段进行抽取并重命名
            if sub_tick_df.empty:
                sub_tick_df = pd.DataFrame(columns=STOCK_RAW_TICK_COLUMNS)
            else:
                sub_tick_df = sub_tick_df[STOCK_RAW_TICK_COLUMNS]
                sub_tick_df = sub_tick_df.replace({'PreClosePx': 0.0}, np.nan)  # 如遇PreClose为0的，以前值填充之
                sub_tick_df = sub_tick_df.fillna(method='ffill')
                # 将连续竞价期间OpenPrice, HighPrice和LowPrice为0的条目删掉
                sub_tick_df = tickdata_OHL_filter(sub_tick_df)
            sub_tick_list.append(sub_tick_df)
        tick_df = pd.concat(sub_tick_list, axis=0).sort_values(["MDDate", "MDTime"],ascending=True)
        return tick_df

    def load_stock_transactions_by_frame(self, start_date, end_date):
        '''
        载入股票的一段交易日中的所有逐笔成交数据
        '''
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, MAX_FRAME_LENGTH)
        # 对各个分组分别取数据
        sub_transactions_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            # 读取原始股票的Tick数据
            start_date_time = "{0} {1}".format(sub_start_date, "000001000")
            end_date_time = "{0} {1}".format(sub_end_date, "235959000")
            sub_transactions_df = self.mdp.get_data_by_time_frame("Transaction", self.code, start_date_time, end_date_time, ['1','2','3','4','5'])
            # 对关键字段进行抽取并重命名
            if sub_transactions_df.empty:
                sub_transactions_df = pd.DataFrame(columns=STOCK_RAW_TRANSACTIONS_COLUMNS)
            else:
                sub_transactions_df = sub_transactions_df[STOCK_RAW_TRANSACTIONS_COLUMNS]
            sub_transactions_list.append(sub_transactions_df)
        transactions_df = pd.concat(sub_transactions_list, axis=0)
        return transactions_df

    def load_stock_order_by_frame(self, start_date, end_date):
        '''
        载入股票的一段交易日中的所有Order数据
        '''
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, MAX_FRAME_LENGTH)
        # 对各个分组分别取数据
        sub_order_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            # 读取原始股票的Tick数据
            start_date_time = "{0} {1}".format(sub_start_date, "000001000")
            end_date_time = "{0} {1}".format(sub_end_date, "235959000")
            sub_order_df = self.mdp.get_data_by_time_frame("Order", self.code, start_date_time, end_date_time,
                                                      ['1', '2', '3', '4', '5'])
            # 对关键字段进行抽取并重命名
            if sub_order_df.empty:
                sub_order_df = pd.DataFrame(columns=STOCK_RAW_ORDER_COLUMNS)
            else:
                sub_order_df = sub_order_df[STOCK_RAW_ORDER_COLUMNS]
            sub_order_list.append(sub_order_df)
        order_df = pd.concat(sub_order_list, axis=0).sort_values(["MDDate", "OrderIndex"],ascending=True)
        return order_df

    def load_cbond_tick_by_frame(self, start_date, end_date):
        '''
        载入股票一段交易日中所有Tick数据
        '''
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, MAX_FRAME_LENGTH)
        # 对各个分组分别取数据
        sub_tick_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            # 读取原始股票的Tick数据
            start_date_time = "{0} {1}".format(sub_start_date, "000001000")
            end_date_time = "{0} {1}".format(sub_end_date, "235959000")
            sub_tick_df = self.bd.get_bond_data(self.code, start_date_time, end_date_time, "TICK")
            # 对关键字段进行抽取并重命名
            if sub_tick_df.empty:
                sub_tick_df = pd.DataFrame(columns=CBOND_RAW_TICK_COLUMNS)
            else:
                sub_tick_df = sub_tick_df[CBOND_RAW_TICK_COLUMNS]
                sub_tick_df = sub_tick_df.replace({'PreClosePx': 0.0}, np.nan)  # 如遇PreClose为0的，以前值填充之
                sub_tick_df = sub_tick_df.fillna(method='ffill')
                # 将连续竞价期间OpenPrice, HighPrice和LowPrice为0的条目删掉
                sub_tick_df = tickdata_OHL_filter(sub_tick_df)
            sub_tick_list.append(sub_tick_df)
        tick_df = pd.concat(sub_tick_list, axis=0).sort_values(["MDDate", "MDTime"],ascending=True)
        if self.code_type == "CBOND" and self.code.endswith(".SH"):
            volume_adjust_columns = [x for x in tick_df.columns.tolist() if "Qty" in x or x in ["TotalVolumeTrade", "TotalValueTrade"]]
            tick_df[volume_adjust_columns] = tick_df[volume_adjust_columns] * 10
        return tick_df

    def load_cbond_transactions_by_frame(self, start_date, end_date):
        '''
        载入股票的一段交易日中的所有逐笔成交数据
        '''
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, MAX_FRAME_LENGTH)
        # 对各个分组分别取数据
        sub_transactions_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            # 读取原始股票的Tick数据
            start_date_time = "{0} {1}".format(sub_start_date, "000001000")
            end_date_time = "{0} {1}".format(sub_end_date, "235959000")
            sub_transactions_df = self.bd.get_bond_data(self.code, start_date_time, end_date_time, "TRANSACTION")
            # 对关键字段进行抽取并重命名
            if sub_transactions_df.empty:
                sub_transactions_df = pd.DataFrame(columns=CBOND_RAW_TRANSACTIONS_COLUMNS)
            else:
                sub_transactions_df = sub_transactions_df[CBOND_RAW_TRANSACTIONS_COLUMNS]
            sub_transactions_list.append(sub_transactions_df)
        transactions_df = pd.concat(sub_transactions_list, axis=0)
        if self.code_type == "CBOND" and self.code.endswith(".SH"):
            volume_adjust_columns = [x for x in transactions_df.columns.tolist() if "Qty" in x ]
            transactions_df[volume_adjust_columns] = transactions_df[volume_adjust_columns] * 10
        return transactions_df

    def load_cbond_order_by_frame(self, start_date, end_date):
        '''
        载入股票的一段交易日中的所有Order数据
        '''
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, MAX_FRAME_LENGTH)
        # 对各个分组分别取数据
        sub_order_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            # 读取原始股票的Tick数据
            start_date_time = "{0} {1}".format(sub_start_date, "000001000")
            end_date_time = "{0} {1}".format(sub_end_date, "235959000")
            sub_order_df = self.bd.get_bond_data(self.code, start_date_time, end_date_time,"ORDER")
            # 对关键字段进行抽取并重命名
            if sub_order_df.empty:
                sub_order_df = pd.DataFrame(columns=CBOND_RAW_ORDER_COLUMNS)
            else:
                sub_order_df = sub_order_df[CBOND_RAW_ORDER_COLUMNS]
            sub_order_list.append(sub_order_df)
        order_df = pd.concat(sub_order_list, axis=0).sort_values(["MDDate", "OrderIndex"],ascending=True)
        if self.code_type == "CBOND" and self.code.endswith(".SH"):
            volume_adjust_columns = [x for x in order_df.columns.tolist() if "Qty" in x ]
            order_df[volume_adjust_columns] = order_df[volume_adjust_columns] * 10
        return order_df

    def load_tick_data(self, start_date, end_date):
        t1 = dt.datetime.now()
        if self.code_type == "STOCK":
            tick_df = self.load_stock_tick_by_frame(start_date, end_date)
        elif self.code_type == "CBOND":
            tick_df = self.load_cbond_tick_by_frame(start_date, end_date)
        t2 = dt.datetime.now()
        self.my_print("{}-{}-{} Load Tick Data Time Cost: {}, Data Size: {}".format(self.code, start_date, end_date,
                                                                            (t2 - t1).total_seconds(), tick_df.shape))
        return tick_df

    def load_transactions_data(self, start_date, end_date):
        t1 = dt.datetime.now()
        if self.code_type == "STOCK":
            transaction_df = self.load_stock_transactions_by_frame(start_date, end_date)
        elif self.code_type == "CBOND":
            transaction_df = self.load_cbond_transactions_by_frame(start_date, end_date)
        t2 = dt.datetime.now()
        self.my_print("{}-{}-{} Load Transaction Data Time Cost: {}, Data Size: {}".format(self.code, start_date, end_date,
                                                                            (t2 - t1).total_seconds(), transaction_df.shape))
        return transaction_df

    def load_orders_data(self, start_date, end_date):
        t1 = dt.datetime.now()
        if self.code_type == "STOCK":
            order_df = self.load_stock_order_by_frame(start_date, end_date)
        elif self.code_type == "CBOND":
            order_df = self.load_cbond_order_by_frame(start_date, end_date)
        t2 = dt.datetime.now()
        self.my_print("{}-{}-{} Load Order Data Time Cost: {}, Data Size: {}".format(self.code, start_date, end_date,
                                                                            (t2 - t1).total_seconds(), order_df.shape))
        return order_df

    def load_mock_tick_data(self, start_date, end_date):
        """
        获取一段交易日内深交所股票还原盘口数据
        """
        mock_tick_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)

        ### 加载辅助TICK数据，Order和Transactions数据
        tick_df = self.load_tick_data(start_date, end_date)
        transactions_df = self.load_transactions_data(start_date, end_date)
        order_df = self.load_orders_data(start_date, end_date)

        ### 循环进行每日盘口还原
        mock_tick_df_list = []
        for trading_day in trading_day_list:
            daily_tick_df = tick_df[tick_df["MDDate"] == trading_day]
            daily_transactions_df = transactions_df[transactions_df["MDDate"] == trading_day]
            daily_order_df = order_df[order_df["MDDate"] == trading_day]
            if daily_tick_df.empty or daily_transactions_df.empty or daily_order_df.empty:
                self.my_print(" Empty Data: {}-{} ".format(self.code, trading_day))
                if self.code_type == "STOCK":
                    daily_mock_tick_df = pd.DataFrame(columns=ALIGN_STOCK_COLUMNS)
                elif self.code_type == "CBOND":
                    daily_mock_tick_df = pd.DataFrame(columns=ALIGN_CBOND_COLUMNS)
            else:
                daily_mock_tick_df = self.run_mock_daily(trading_day, daily_tick_df, daily_transactions_df, daily_order_df)

            if self.monitor:
                if daily_mock_tick_df.empty:
                    mock_tick_monitor.update({trading_day: TickMonitor.EMPTY})
                else:
                    mock_tick_monitor.update({trading_day: TickMonitor.NORMAL})

            mock_tick_df_list.append(daily_mock_tick_df)
        mock_tick_df = pd.concat(mock_tick_df_list, axis=0)
        return mock_tick_df, mock_tick_monitor

    def run_mock_daily(self, date, tick_data, transaction_data, order_data):
        ### raw transaction_data and order_data
        t1 = dt.datetime.now()
        ### 添加Timestamp字段, 对齐Transactions字段需要
        transaction_data["Timestamp"] = (transaction_data["MDDate"] + transaction_data["MDTime"]).apply(
            lambda x: dt.datetime.strptime(x+"000", "%Y%m%d%H%M%S%f").timestamp())
        ### 获取价格信息，分别来自TICK数据和逐笔数据计算
        max_price, min_price, pre_close = self.get_MaxMinPreClosePrice(tick_data)

        ### 生成TICK时间
        md_time_list = self.generate_mock_tick_time(date, tick_data)
        timestamp_list = [self.to_timestamp(date, md_time) for md_time in md_time_list]
        mock_tick_data = {var: [] for var in ALIGN_STOCK_COLUMNS}

        hd = HolographicData()
        high_price, low_price = 0, 10000
        for i in range(1, len(md_time_list)):
            trans_data_slice = self.get_new_data(transaction_data, md_time_list[i-1], md_time_list[i])
            order_data_slice = self.get_new_data(order_data, md_time_list[i-1], md_time_list[i])
            if i == 1:
                open_price = self.get_OpenPrice_from_transdata(trans_data_slice)
            high_price, low_price = self.get_HLPrice_from_transdata(trans_data_slice, high_price, low_price)
            hd.on_new_period(trans_data_slice, order_data_slice, md_time_list[i])
            pv_info = hd.get_pv_info()

            # 更新 Mock Tick 数据
            mock_tick_data["Code"].append(self.code)
            mock_tick_data["Timestamp"].append(timestamp_list[i])
            mock_tick_data["Date"].append(date)
            mock_tick_data["Time"].append(md_time_list[i])
            mock_tick_data["OpenPrice"].append(open_price)
            mock_tick_data["HighPrice"].append(high_price)
            mock_tick_data["LowPrice"].append(low_price)
            mock_tick_data["MaxPrice"].append(max_price)
            mock_tick_data["MinPrice"].append(min_price)
            mock_tick_data["LastPrice"].append(pv_info["LastPrice"])
            mock_tick_data["Volume"].append(pv_info["Volume"])
            mock_tick_data["Amount"].append(pv_info["Amount"])
            mock_tick_data["TotalVolume"].append(pv_info["TotalVolume"])
            mock_tick_data["TotalAmount"].append(pv_info["TotalAmount"])
            mock_tick_data["PreviousClose"].append(pre_close)
            mock_tick_data["BidPrice"].append(np.array(pv_info["BidPrice"], dtype=np.float64))
            mock_tick_data["AskPrice"].append(np.array(pv_info["AskPrice"], dtype=np.float64))
            mock_tick_data["BidVolume"].append(np.array(pv_info["BidVolume"], dtype=np.float64))
            mock_tick_data["AskVolume"].append(np.array(pv_info["AskVolume"], dtype=np.float64))
            mock_tick_data["Transactions"].append(self.get_transaction_slice_array(trans_data_slice))
            mock_tick_data["IsMock"] = 0

        daily_mock_tick_df = pd.DataFrame(mock_tick_data)
        mstart = generate_timestamp(date, "093015")
        mend = generate_timestamp(date, "112959")
        pstart = generate_timestamp(date, "130015")
        if self.code_type == "STOCK":
            daily_mock_tick_df = daily_mock_tick_df.reindex(columns=ALIGN_STOCK_COLUMNS)
            pend = generate_timestamp(date, "145659")
        elif self.code_type == "CBOND":
            daily_mock_tick_df = daily_mock_tick_df.reindex(columns=ALIGN_CBOND_COLUMNS)
            pend = generate_timestamp(date, "145959")

        daily_mock_tick_df = daily_mock_tick_df[(daily_mock_tick_df["Timestamp"] >= mstart) &
                                                (daily_mock_tick_df["Timestamp"] <= mend) |
                                                (daily_mock_tick_df["Timestamp"] >= pstart) &
                                                (daily_mock_tick_df["Timestamp"] <= pend) ]

        daily_mock_tick_df = daily_mock_tick_df.reset_index(drop=True)

        t2 = dt.datetime.now()
        self.my_print("{}-{} Mock Tick Data Time Cost: {}".format(self.code, date, t2 - t1))

        return daily_mock_tick_df

    @staticmethod
    def get_new_data(data_df, st_time: str, ed_time: str):
        st_index = np.searchsorted(data_df["MDTime"], st_time)
        ed_index = np.searchsorted(data_df["MDTime"], ed_time)
        return data_df.iloc[st_index:ed_index, :]

    @staticmethod
    def to_timestamp(date: str, md_time: str):
        time_str = date + md_time
        timestamp = dt.datetime.strptime(time_str+"000", "%Y%m%d%H%M%S%f").timestamp()
        return timestamp

    def generate_mock_tick_time(self, date, tick_data=None):
        """"""
        timestamp_list = []
        mstart = generate_timestamp(date, "093000")
        mend = generate_timestamp(date, "112959")
        pstart = generate_timestamp(date, "130000")
        if self.code_type == "STOCK":
            pend = generate_timestamp(date, "145659")
        elif self.code_type == "CBOND":
            pend = generate_timestamp(date, "145959")

        if self.mock_lag is None:
            timestamp = mstart
            while timestamp <= mend:
                timestamp_list.append(timestamp)
                timestamp += self.mock_freq

            timestamp = pstart
            while timestamp <= pend:
                timestamp_list.append(timestamp)
                timestamp += self.mock_freq
        else:
            tick_timestamp_list = (tick_data["MDDate"] + tick_data["MDTime"]).apply(
                                   lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp()).tolist()
            for timestamp in tick_timestamp_list:
                if (timestamp >= mstart and timestamp <= mend) or (timestamp >= pstart and timestamp <= pend):
                    lag_timestamp = timestamp + self.mock_lag
                    timestamp_list.append(lag_timestamp)

        # 增加早盘和尾盘集合竞价的2个数据
        timestamp_list.insert(0, generate_timestamp(date, "091500"))
        timestamp_list.append(generate_timestamp(date, "150000"))
        md_time_list = [dt.datetime.fromtimestamp(x).strftime("%H%M%S%f")[:-3] for x in timestamp_list]

        return md_time_list

    @staticmethod
    def get_MaxMinPreClosePrice(daily_tick_df):
        daily_tick_df = daily_tick_df[["MaxPx", "MinPx", "PreClosePx"]]
        if daily_tick_df.empty:
            max_price, min_price, pre_close = 0., 0., 0.,
        else:
            max_price, min_price, pre_close = daily_tick_df.iloc[0].values
        return max_price, min_price, pre_close

    @staticmethod
    def get_HLPrice_from_transdata(transaction_data, high_price, low_price):
        trade_price = transaction_data[transaction_data["TradeType"]==0]["TradePrice"]
        if trade_price.empty:
             high_price_, low_price_ = 0., 100000
        else:
            high_price_, low_price_ = trade_price.max(), trade_price.min()
        if high_price_ > high_price:
            high_price = high_price_
        if low_price_ < low_price:
            low_price = low_price_
        return high_price, low_price

    @staticmethod
    def get_OpenPrice_from_transdata(transaction_data):
        trade_price = transaction_data[transaction_data["TradeType"]==0]["TradePrice"]
        if trade_price.empty:
            open_price =0
        else:
            open_price = trade_price.iloc[0]
        return open_price

    @staticmethod
    def get_transaction_slice_array(trans_data_slice):
        ### 与原始数据处理保持一致，删除逐笔中撤单数据
        trans_data_slice = trans_data_slice[trans_data_slice["TradeType"]==0]
        del trans_data_slice["MDDate"]
        del trans_data_slice["MDTime"]
        if trans_data_slice.empty:
            ### 逐笔数据缺失，补None
            return None
        else:
            return trans_data_slice.values.astype(np.float64)

    def my_print(self, x_str):
        if self.is_executor:
            remote_print(x_str)
        else:
            print(x_str)
