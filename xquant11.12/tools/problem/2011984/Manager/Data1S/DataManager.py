#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/11/17 15:26
import pandas as pd
from Manager.Data1S.DataConfig import DataConfig
from Manager.Data1S.DataLoader import DataLoader
from Manager.Data1S.Tick2SliceData import Tick2SliceData


class DataManager(object):
    def __init__(self, code, start_date, end_date, data_config=None):
        self.code = code
        self.start_date = start_date
        self.end_date = end_date
        self.data_config = data_config if data_config is not None else DataConfig()
        self.tick_hbase_library = self.data_config.tick_hbase_library
        self.tran_hbase_library = self.data_config.tran_hbase_library

        self.dl = DataLoader(self.code, self.start_date, self.end_date, self.tick_hbase_library, self.tran_hbase_library)
        self.trade_dates = self.dl.load_valid_dates()
        self.__pre_close_dict = self.dl.load_pre_close_dict()

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
            try:
                target_timestamp = self.__target_timestamp_dict.get(timestamp)
                freq = self.__freq_list[int(target_timestamp % 3)]
                self.__tick_dict[freq].update({timestamp: slice_data})
            except:
                raise ValueError(self.code)

        # Convert Tick Data To Three Freq Ticks
        self.__freq_tick_dict = {freq: dict() for freq in self.__freq_list}
        for date_tick_dict in self.__tick:
            tick_df = pd.DataFrame(date_tick_dict)
            tick_df["Freq"] = tick_df["Timestamp"].apply(lambda x: self.__freq_list[int( self.__target_timestamp_dict.get(x) % 3)])
            for freq in self.__freq_list:
                freq_tick_df = tick_df[tick_df["Freq"] == freq].reset_index(drop=True)
                freq_tick_df["Volume"] = freq_tick_df["TotalVolume"].diff()
                freq_tick_df["Amount"] = freq_tick_df["TotalAmount"].diff()
                if not freq_tick_df.empty:
                    # 每日第1行的成交额、成交量等于累计成交额、累计成交量
                    freq_tick_df.loc[0, "Volume"] = freq_tick_df.TotalVolume.iloc[0]
                    freq_tick_df.loc[0, "Amount"] = freq_tick_df.TotalAmount.iloc[0]
                self.__freq_tick_dict[freq].update({timestamp: (volume, amount) for timestamp, volume, amount in zip(freq_tick_df["Timestamp"],
                                                    freq_tick_df["Volume"], freq_tick_df["Amount"])})

    def get_pre_close_dict(self):
        return self.__pre_close_dict

    def get_tick(self):
        map_ = {
            "Timestamp": "TimeStamp",
        }
        tick_data = []
        for tick_data_date in self.__tick:
            tick_data_date_new = {}
            for i, j in tick_data_date.items():
                if i in map_.keys():
                    tick_data_date_new.update({map_[i]: j})
                else:
                    tick_data_date_new.update({i: j})
            tick_data.append(tick_data_date_new)
        return tick_data

    def get_transaction(self):
        map_ = {
            "Timestamp": "TimeStamp",
        }
        trans_data = []
        for trans_data_date in self.__transaction:
            trans_data_date_new = {}
            for i, j in trans_data_date.items():
                if i in map_.keys():
                    trans_data_date_new.update({map_[i]: j})
                else:
                    trans_data_date_new.update({i: j})
            trans_data.append(trans_data_date_new)
        return trans_data

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