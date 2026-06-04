from HFDataLoader.Config import FLAG_COLUMNS
from HFDataLoader.Config import DAILY_MONITOR_HBASE_COLUMNS, MINUTE_MONITOR_HBASE_COLUMNS, TICK_MONITOR_HBASE_COLUMNS
from HFDataLoader.Config import MOCK_TICK_MONITOR_HBASE_COLUMNS
import pandas as pd
from xquant.factordata import FactorData


class DataMonitor(object):
    def __init__(self, lib_name, code):
        self.lib_name = lib_name
        self.code = code
        self.daily_monitor = {}   ### key: date, value: status
        self.minute_monitor = {}
        self.tick_monitor = {}
        self.mock_tick_monitor = {}
        self.fa = FactorData()

    def run_monitor(self):
        if self.daily_monitor:
            daily_flag = self.__dict2df(self.daily_monitor)
            self.save_monitor(daily_flag, DAILY_MONITOR_HBASE_COLUMNS)

        if self.minute_monitor:
            minute_flag = self.__dict2df(self.minute_monitor)
            self.save_monitor(minute_flag, MINUTE_MONITOR_HBASE_COLUMNS)

        if self.tick_monitor:
            tick_flag = self.__dict2df(self.tick_monitor)
            self.save_tick_monitor(tick_flag, TICK_MONITOR_HBASE_COLUMNS)

        if self.mock_tick_monitor:
            mock_tick_flag = self.__dict2df(self.mock_tick_monitor)
            self.save_tick_monitor(mock_tick_flag, MOCK_TICK_MONITOR_HBASE_COLUMNS)

    def update_daily_monitor(self, daily_monitor):
        self.daily_monitor.update(daily_monitor)

    def update_minute_monitor(self, minute_monitor):
        self.minute_monitor.update(minute_monitor)

    def update_tick_monitor(self, tick_monitor):
        self.tick_monitor.update(tick_monitor)

    def update_mock_tick_monitor(self, mock_tick_monitor):
        self.mock_tick_monitor.update(mock_tick_monitor)

    @staticmethod
    def __dict2df(monitor_dict):
        enum2value_dict = {}
        for date, monitor in monitor_dict.items():
            enum2value_dict[date] = monitor.value
        df = pd.Series(enum2value_dict).to_frame()
        df.columns = ["FlagValue"]
        df["FlagDate"] = df.index
        ### REINDEX COLUMNS
        df = df.reindex(columns=FLAG_COLUMNS)
        return df

    def save_monitor(self, flag_df, hbase_columns):
        SUFFIX = hbase_columns[0].split("_")[0]
        try:
            old_flag_df = self.get_old_flag_df(hbase_columns)
            date_list = list(set(old_flag_df["FlagDate"].to_list()))
        except:
            date_list = []
        date_list = list(map(str, date_list))

        if len(date_list) != 0:  # 原有数据库有数据
            trading_day_list = sorted(flag_df["FlagDate"].drop_duplicates().to_list())
            # 找出不在更新日期范围内的原有数据
            sub_old_flag_df = old_flag_df[~old_flag_df["FlagDate"].isin(trading_day_list)]
            # 合并两部分数据
            new_flag_df = sub_old_flag_df.append(flag_df).sort_values(by=['FlagDate'])
            new_flag_df.columns = hbase_columns
            self.fa.update_factor_value(self.lib_name, new_flag_df, "{0}_{1}".format(self.code, SUFFIX), "20200102")
        else: # 原数据库没有数据
            flag_df.columns = hbase_columns
            self.fa.update_factor_value(self.lib_name, flag_df, "{0}_{1}".format(self.code, SUFFIX), "20200102")

    def save_tick_monitor(self, flag_df, hbase_columns):
        ### TICK Monitor数据直接更新
        update_day_list = sorted(flag_df["FlagDate"].drop_duplicates().to_list())
        SUFFIX = hbase_columns[0].split("_")[0]
        flag_df.columns = hbase_columns
        for update_date in update_day_list:
            sub_flag_df = flag_df[flag_df["{}_FlagDate".format(SUFFIX)]==update_date]
            if not sub_flag_df.empty:
                self.fa.update_factor_value(self.lib_name, sub_flag_df, "{0}_{1}".format(self.code, SUFFIX), update_date)

    def get_old_flag_df(self, hbase_columns):
        SUFFIX = hbase_columns[0].split("_")[0]
        try:
            flag_df = self.fa.get_factor_value(self.lib_name, "{0}_{1}".format(self.code, SUFFIX), "20200102", hbase_columns)
        except:
            flag_df = pd.DataFrame(columns=hbase_columns)
        flag_df.columns = list( map(lambda x: x.replace("{0}_".format(SUFFIX), ""), flag_df.columns.to_list()))
        return flag_df



