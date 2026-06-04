#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/11/17 15:26
import pandas as pd
from DataIO.DataConfig import DataConfig
from DataIO.DataLoader import DataLoader
from DataIO.Tick2SliceData import Tick2SliceData


class DataManager(object):
    def __init__(self, code, start_date, end_date, data_config=None):
        self.code = code
        self.start_date = start_date
        self.end_date = end_date
        self.data_config = data_config if data_config is not None else DataConfig()
        self.tick_data_source = self.data_config.tick_data_source
        self.tick_hbase_library = self.data_config.tick_hbase_library
        self.tran_data_source = self.data_config.tran_data_source
        self.tran_hbase_library = self.data_config.tran_hbase_library
        if self.tran_data_source == "hbase" and self.tran_hbase_library is None:
            self.tran_hbase_library = self.tick_hbase_library
        self.order_data_source = self.data_config.order_data_source
        self.order_hbase_library = self.data_config.order_hbase_library
        if self.order_data_source == "hbase" and self.order_hbase_library is None:
            self.order_hbase_library = self.tran_hbase_library if self.tran_hbase_library is not None else self.tick_hbase_library

        self.dl = DataLoader(self.code, self.start_date, self.end_date, self.tick_data_source, self.tick_hbase_library,
                             self.tran_data_source, self.tran_hbase_library, self.order_data_source, self.order_hbase_library)
        self.trade_dates = self.dl.load_valid_dates()

        self.__target_timestamp_dict = None
        self.__tick = None
        self.__transaction = None
        self.__tick_dict = None
        self.__freq_tick_dict = None
        self.__freq_list = ["036", "147", "258"]

    def prepare_data(self):
        self.__tick, self.__transaction = self.load_tick_data(), self.load_transaction_data()
        data_converter = Tick2SliceData(self.code)
        data_converter.convert_tick_data(self.__tick)
        self.__tick_dict = data_converter.get_data_dict()

    def prepare_data_with_freq(self):
        self.__target_timestamp_dict = self.dl.load_target_timestamp_dict(self.trade_dates)

        self.__tick, self.__transaction = self.load_tick_data(), self.load_transaction_data()
        data_converter = Tick2SliceData(self.code)
        data_converter.convert_tick_data(self.__tick)
        total_tick_dict = data_converter.get_data_dict()

        self.__tick_dict = {freq: dict() for freq in self.__freq_list}
        for timestamp, slice_data in total_tick_dict.items():
            target_timestamp = self.__target_timestamp_dict.get(timestamp)
            freq = self.__freq_list[int(target_timestamp % 3)]
            self.__tick_dict[freq].update({timestamp: slice_data})

        # Convert Tick Data To Three Freq Ticks
        self.__freq_tick_dict = {freq: [] for freq in self.__freq_list}
        for date_tick_dict in self.__tick:
            tick_df = pd.DataFrame(date_tick_dict)
            tick_df["Freq"] = tick_df["Timestamp"].apply(lambda x: self.__freq_list[int( self.__target_timestamp_dict.get(x) % 3)])
            for freq in self.__freq_list:
                freq_tick_df = tick_df[tick_df["Freq"] == freq]
                self.__freq_tick_dict[freq].append({col: freq_tick_df[col].tolist() for col in tick_df.columns.tolist()})

    def get_tick(self):
        return self.__tick

    def get_transaction(self):
        return self.__transaction

    def get_tick_dict(self):
        return self.__tick_dict

    def get_freq_tick_dict(self):
        return self.__freq_tick_dict

    def get_target_timestamp_dict(self):
        return self.__target_timestamp_dict

    def load_tick_data(self):
        """"""
        ticks_df = self.dl.load_tick_data()
        ticks_df = ticks_df.astype({"Date": int, "Time": int})

        tick_data_list = []
        for date in self.trade_dates:
            daily_tick = ticks_df[ticks_df["Date"] == int(date)].reset_index(drop=True)
            tick_data_list.append(daily_tick.to_dict("list"))

        return tick_data_list

    def load_transaction_data(self):
        """"""
        transactions_df = self.dl.load_transaction_data()

        # 删除撤单数据，主卖成交BSFlag重置为 -1
        transactions_df = transactions_df.loc[transactions_df["TradeType"] == 0, :]
        transactions_df.loc[transactions_df["BSFlag"] == 2, "BSFlag"] = -1
        transactions_df = transactions_df.astype({"Date": int, "Time": int})

        transaction_data_list = []

        for date in self.trade_dates:
            daily_transaction = transactions_df[transactions_df["Date"] == int(date)].reset_index(drop=True)
            transaction_data_list.append(daily_transaction.to_dict("list"))

        return transaction_data_list

    def load_order_data(self):
        """"""
        orders_df = self.dl.load_order_data()
        orders_df = orders_df.astype({"Date": int, "Time": int})

        order_data_list = []

        for date in self.trade_dates:
            daily_order = orders_df[orders_df["Date"] == int(date)].reset_index(drop=True)
            order_data_list.append(daily_order.to_dict("list"))

        return order_data_list