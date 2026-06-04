from DataInterface.Config import MAX_FRAME_LENGTH, MAX_MINUTE_KLINE, MAX_DAILY_KLINE, THIRD_MAX_FRAME_LENGTH
from DataInterface.Config import INDEX_RAW_DAILY_COLUMNS, INDEX_RAW_MINUTE_COLUMNS, INDEX_RAW_TICK_COLUMNS
from DataInterface.Config import SHENWAN_RAW_DAILY_COLUMNS, SHENWAN_CLEAN_DAILY_COLUMNS, SHENWAN_TARGET_DAILY_COLUMNS
from DataInterface.Config import INDEX_CLEAN_DAILY_COLUMNS, INDEX_CLEAN_MINUTE_COLUMNS, INDEX_CLEAN_TICK_COLUMNS
from DataInterface.Config import INDEX_TARGET_DAILY_COLUMNS, INDEX_TARGET_MINUTE_COLUMNS, INDEX_TARGET_TICK_COLUMNS
from DataMonitor.Monitor import DailyMonitor, MinuteMonitor, TickMonitor
from DataLoader.DataCleanUtil import tick_data_zero_price_filter, minute_data_transform
from Utils.HelpFunc import get_code_type, get_industry_type, get_index_type, get_trading_day, split_calc_date_into_group

import numpy as np
import pandas as pd
import datetime as dt
from xquant.factordata import FactorData
from xquant.marketdata import MarketData
from xquant.thirdpartydata.marketdata import MarketData as ThirdMarketData


class IndexDataLoader:
    """加载宽基指数或行业指数数据"""
    def __init__(self, code: str, data_source: str="mdp", monitor=False):
        self.code = code
        self.data_source = data_source
        self.monitor = monitor

        self.code_type = get_code_type(self.code)
        self.index_type = get_index_type(self.code) if self.code_type == "INDEX" else None
        self.indus_type = get_industry_type(self.code) if self.code_type == "INDUSTRY" else None

        self.fa = FactorData()
        self.mdp = MarketData()
        self.tma = ThirdMarketData()

    def load_daily_data(self, start_date, end_date):
        if self.code_type == "INDEX":
            if self.index_type == "ZZ":
                daily_df, daily_monitor = self.load_index_daily_data(start_date, end_date)
            elif self.index_type == "SHENWAN":
                daily_df, daily_monitor = self.load_industry_daily_data(start_date, end_date)
            elif self.index_type == "THIRD":
                daily_df, daily_monitor = self.load_third_daily_data(start_date, end_date)
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                daily_df, daily_monitor = self.load_industry_daily_data(start_date, end_date)
            else:
                raise Exception(" Not Supported Daily Data Yet For Industry Type: {} ".format(self.code))
        else:
            raise Exception(" Not Supported Daily Data: {} ".format(self.code))

        return daily_df, daily_monitor

    def load_minute_data(self, start_date, end_date):
        if self.code_type == "INDEX":
            if self.index_type == "ZZ":
                minute_df, minute_monitor = self.load_index_minute_data(start_date, end_date)
            elif self.index_type == "SHENWAN":
                minute_df, minute_monitor = self.load_industry_minute_data(start_date, end_date)
            elif self.index_type == "THIRD":
                minute_df, minute_monitor = self.load_third_minute_data(start_date, end_date)
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                minute_df, minute_monitor = self.load_industry_minute_data(start_date, end_date)
            else:
                raise Exception(" Not Supported Minute Data Yet For Industry Type: {} ".format(self.code))
        else:
            raise Exception(" Not Supported Minute Data: {} ".format(self.code))

        return minute_df, minute_monitor

    def load_tick_data(self, start_date, end_date):
        if self.code_type == "INDEX":
            if self.index_type == "ZZ":
                tick_df, tick_monitor = self.load_index_tick_data(start_date, end_date)
            elif self.index_type == "SHENWAN":
                tick_df, tick_monitor = self.load_industry_tick_data(start_date, end_date)
            elif self.index_type == "THIRD":
                tick_df, tick_monitor = self.load_index_tick_data(start_date, end_date)
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                tick_df, tick_monitor = self.load_industry_tick_data(start_date, end_date)
            else:
                raise Exception(" Not Supported Tick Data Yet For Industry Type: {} ".format(self.code))
        else:
            raise Exception(" Not Supported Tick Data: {} ".format(self.code))

        return tick_df, tick_monitor

    def load_index_daily_data(self, start_date, end_date):
        """ 载入指数的一段交易日中的所有日频数据，并根据列进行筛选、清洗、清洗
        """
        daily_monitor = dict()

        trading_day_list = get_trading_day(start_date, end_date)

        daily_df = self.fa.get_factor_value("Basic_factor", stock=[self.code], mddate=trading_day_list,
                                       factor_names=INDEX_RAW_DAILY_COLUMNS)
        if daily_df.empty:
            daily_df = pd.DataFrame(columns=INDEX_TARGET_DAILY_COLUMNS)
            if self.monitor:
                daily_monitor.update({trading_day: DailyMonitor.EMPTY for trading_day in trading_day_list})
        else:
            daily_df = daily_df.droplevel(1)
            daily_df["volume"] = daily_df["volume"] * 100
            daily_df["amt"] = daily_df["amt"] * 1000

            daily_df["date"] = list(map(str, list(daily_df.index)))
            daily_df = daily_df.reindex(columns=INDEX_CLEAN_DAILY_COLUMNS)
            daily_df.columns = INDEX_TARGET_DAILY_COLUMNS

            if self.monitor:
                for trading_day in trading_day_list:
                    daily_daily_df = daily_df[daily_df["Date"] == trading_day]
                    if daily_daily_df.empty:
                        daily_monitor.update({trading_day: DailyMonitor.EMPTY})
                    else:
                        daily_monitor.update({trading_day: DailyMonitor.NORMAL})

        return daily_df, daily_monitor

    def load_index_minute_data(self, start_date, end_date):
        """ 载入指数的一段交易日中的所有分钟数据，并根据列进行筛选、清洗、清洗
        """
        minute_monitor = dict()

        trading_day_list = get_trading_day(start_date, end_date)

        sub_minutes_list = []

        for trading_day in trading_day_list:
            sub_minute_df = self.mdp.get_data_by_date("Kline1M4ZT", self.code, trading_day)
            if not sub_minute_df.empty:
                sub_minute_df = sub_minute_df[INDEX_RAW_MINUTE_COLUMNS]
                sub_minutes_list.append(sub_minute_df)

        if len(sub_minutes_list) == 0:
            minute_df = pd.DataFrame()
        else:
            minute_df = pd.concat(sub_minutes_list, axis=0)

        if minute_df.empty:
            minute_df = pd.DataFrame(columns=INDEX_TARGET_MINUTE_COLUMNS)
            if self.monitor:
                minute_monitor.update({trading_day: MinuteMonitor.EMPTY for trading_day in trading_day_list})
        else:
            minute_df["Timestamp"] = (minute_df["MDDate"] + minute_df["MDTime"]).apply(
                                                 lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            minute_df = minute_df.reindex(columns=INDEX_CLEAN_MINUTE_COLUMNS)
            minute_df.columns = INDEX_TARGET_MINUTE_COLUMNS
            price_columns = ["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]
            minute_df[["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]] = minute_df[price_columns].fillna(method='ffill')
            minute_df[["Volume", "Amount"]] = minute_df[["Volume", "Amount"]].fillna(0.)
            # 分钟数据处理，剔除开盘集合竞价092500和收盘集合竞价150000数据
            minute_df.index = minute_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(int(x)))
            minute_df = minute_data_transform(minute_df, ["drop", "drop"])
            minute_df = minute_df.reindex(columns=INDEX_TARGET_MINUTE_COLUMNS).reset_index(drop=True)

            if self.monitor:
                for trading_day in trading_day_list:
                    daily_minute_df = minute_df[minute_df["Date"] == trading_day]
                    if daily_minute_df.empty:
                        minute_monitor.update({trading_day: MinuteMonitor.EMPTY})
                    else:
                        minute_monitor.update({trading_day: MinuteMonitor.NORMAL})

        return minute_df, minute_monitor

    def load_index_tick_data(self, start_date, end_date):
        """ 载入指数一段交易日中所有Tick数据，并根据列进行筛选
        """
        tick_monitor = dict()

        trading_day_list = get_trading_day(start_date, end_date)

        calc_time_groups = split_calc_date_into_group(trading_day_list, MAX_FRAME_LENGTH)

        sub_ticks_list = []

        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "000001000")
            end_date_time = "{0} {1}".format(sub_end_date, "235959000")
            sub_tick_df = self.mdp.get_data_by_time_frame("INDEX", self.code, start_date_time, end_date_time, ["1", "2", "3", "4", "5"])
            if not sub_tick_df.empty:
                sub_tick_df = sub_tick_df[INDEX_RAW_TICK_COLUMNS]
                sub_tick_df = sub_tick_df.replace({"PreClosePx": 0.0}, np.nan)  # 如遇PreClose为0的，以前值填充之
                sub_tick_df = sub_tick_df.fillna(method="ffill")
                # 将连续竞价期间OpenPrice, HighPrice和LowPrice为0的条目删掉
                sub_tick_df = tick_data_zero_price_filter(sub_tick_df)
                sub_ticks_list.append(sub_tick_df)

        if len(sub_ticks_list) == 0:
            tick_df = pd.DataFrame()
        else:
            tick_df = pd.concat(sub_ticks_list, axis=0)

        if tick_df.empty:
            tick_df = pd.DataFrame(columns=INDEX_TARGET_TICK_COLUMNS)
            if self.monitor:
                tick_monitor.update({trading_day: TickMonitor.EMPTY for trading_day in trading_day_list})
        else:
            tick_df["Timestamp"] = (tick_df["MDDate"] + tick_df["MDTime"]).apply(
                                               lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            daily_tick_df_list = []

            for trading_day in trading_day_list:
                daily_tick_df = tick_df[tick_df["MDDate"] == trading_day]
                if daily_tick_df.empty:
                    if self.monitor:
                        tick_monitor.update({trading_day: TickMonitor.EMPTY})
                else:
                    if self.monitor:
                        tick_monitor.update({trading_day: TickMonitor.NORMAL})

                    daily_tick_df = daily_tick_df.reset_index(drop=True)
                    daily_tick_df["VolumeTrade"] = daily_tick_df["TotalVolumeTrade"].diff()
                    daily_tick_df["ValueTrade"] = daily_tick_df["TotalValueTrade"].diff()
                    # 每日第1行的成交额、成交量等于累计成交额、累计成交量
                    daily_tick_df.loc[0, "VolumeTrade"] = daily_tick_df.loc[0, "TotalVolumeTrade"]
                    daily_tick_df.loc[0, "ValueTrade"] = daily_tick_df.loc[0, "TotalValueTrade"]
                    daily_tick_df["VolumeTrade"] = daily_tick_df["VolumeTrade"].clip_lower(0)
                    daily_tick_df["ValueTrade"] = daily_tick_df["ValueTrade"].clip_lower(0)

                    daily_tick_df_list.append(daily_tick_df)

            tick_df = pd.concat(daily_tick_df_list, axis=0)

            tick_df = tick_df.reindex(columns=INDEX_CLEAN_TICK_COLUMNS)
            tick_df.columns = INDEX_TARGET_TICK_COLUMNS

        return tick_df, tick_monitor

    def load_industry_daily_data(self, start_date, end_date):
        """ 载入FUND一段交易日中的所有日频数据，并根据列进行筛选、清洗
        """
        daily_monitor = dict()

        trading_day_list = get_trading_day(start_date, end_date)

        calc_time_groups = split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)

        sub_dailys_list = []

        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "090000000")
            end_date_time = "{0} {1}".format(sub_end_date, "200000000")
            sub_daily_df = self.mdp.get_index_data(self.code, start_date_time, end_date_time, "K_DAY")

            if not sub_daily_df.empty:
                sub_daily_df = sub_daily_df[SHENWAN_RAW_DAILY_COLUMNS]
                sub_dailys_list.append(sub_daily_df)

        if len(sub_dailys_list) == 0:
            daily_df = pd.DataFrame()
        else:
            daily_df = pd.concat(sub_dailys_list, axis=0)

        if daily_df.empty:
            daily_df = pd.DataFrame(columns=SHENWAN_TARGET_DAILY_COLUMNS)
            if self.monitor:
                daily_monitor.update({trading_day: DailyMonitor.EMPTY for trading_day in trading_day_list})
        else:
            daily_df = daily_df.reindex(columns=SHENWAN_CLEAN_DAILY_COLUMNS).reset_index(drop=True)
            daily_df.columns = SHENWAN_TARGET_DAILY_COLUMNS

            if self.monitor:
                for trading_day in trading_day_list:
                    daily_daily_df = daily_df[daily_df["Date"] == trading_day]
                    if daily_daily_df.empty:
                        daily_monitor.update({trading_day: DailyMonitor.EMPTY})
                    else:
                        daily_monitor.update({trading_day: DailyMonitor.NORMAL})

        return daily_df, daily_monitor

    def load_industry_minute_data(self, start_date, end_date):
        """ 载入FUND一段交易日中的所有分钟数据，并根据列进行筛选、清洗、清洗
        """
        minute_monitor = dict()

        trading_day_list = get_trading_day(start_date, end_date)

        calc_time_groups = split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)

        sub_minutes_list = []

        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "090000000")
            end_date_time = "{0} {1}".format(sub_end_date, "200000000")
            sub_minute_df = self.mdp.get_index_data(self.code, start_date_time, end_date_time, "K_1MIN")

            if not sub_minute_df.empty:
                sub_minute_df = sub_minute_df[INDEX_RAW_MINUTE_COLUMNS]
                sub_minutes_list.append(sub_minute_df)

        if len(sub_minutes_list) == 0:
            minute_df = pd.DataFrame()
        else:
            minute_df = pd.concat(sub_minutes_list, axis=0)

        if minute_df.empty:
            minute_df = pd.DataFrame(columns=INDEX_TARGET_MINUTE_COLUMNS)
            minute_monitor.update({trading_day: MinuteMonitor.EMPTY for trading_day in trading_day_list})
        else:
            minute_df["Timestamp"] = (minute_df["MDDate"] + minute_df["MDTime"]).apply(
                                                lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            minute_df = minute_df.reindex(columns=INDEX_CLEAN_MINUTE_COLUMNS)
            minute_df.columns = INDEX_TARGET_MINUTE_COLUMNS
            price_columns = ["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]
            minute_df[price_columns] = minute_df[price_columns].fillna(method="ffill")
            minute_df[["Volume", "Amount"]] = minute_df[["Volume", "Amount"]].fillna(0.)
            # 分钟数据处理，剔除开盘集合竞价092500和收盘集合竞价150000数据
            minute_df.index = minute_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(int(x)))
            minute_df = minute_data_transform(minute_df, ["drop", "drop"])
            minute_df = minute_df.reindex(columns=INDEX_TARGET_MINUTE_COLUMNS).reset_index(drop=True)

            if self.monitor:
                for trading_day in trading_day_list:
                    daily_minute_df = minute_df[minute_df["Date"] == trading_day]
                    if daily_minute_df.empty:
                        minute_monitor.update({trading_day: MinuteMonitor.EMPTY})
                    else:
                        minute_monitor.update({trading_day: MinuteMonitor.NORMAL})

        return minute_df, minute_monitor

    def load_industry_tick_data(self, start_date, end_date):
        """ 载入FUND一段交易日中的所有Tick数据，并根据列进行筛选
        """
        tick_monitor = dict()

        trading_day_list = get_trading_day(start_date, end_date)

        calc_time_groups = split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)

        sub_ticks_list = []

        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "092500000")
            end_date_time = "{0} {1}".format(sub_end_date, "150000000")
            sub_tick_df = self.mdp.get_index_data(self.code, start_date_time, end_date_time, "TICK")

            if not sub_tick_df.empty:
                sub_tick_df = sub_tick_df[INDEX_RAW_TICK_COLUMNS]
                sub_tick_df = sub_tick_df.replace({"PreClosePx": 0.0}, np.nan)  # 如遇PreClose为0的，以前值填充之
                sub_tick_df = sub_tick_df.fillna(method="ffill")
                # 将连续竞价期间OpenPrice, HighPrice和LowPrice为0的条目删掉
                sub_tick_df = tick_data_zero_price_filter(sub_tick_df)
                sub_ticks_list.append(sub_tick_df)

        if len(sub_ticks_list) == 0:
            tick_df = pd.DataFrame()
        else:
            tick_df = pd.concat(sub_ticks_list, axis=0)

        if tick_df.empty:
            tick_df = pd.DataFrame(columns=INDEX_TARGET_TICK_COLUMNS)
            if self.monitor:
                tick_monitor.update({trading_day: TickMonitor.EMPTY for trading_day in trading_day_list})
        else:
            tick_df["Timestamp"] = (tick_df["MDDate"] + tick_df["MDTime"]).apply(
                                               lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            daily_tick_df_list = []

            for trading_day in trading_day_list:
                daily_tick_df = tick_df[tick_df["MDDate"] == trading_day]
                if daily_tick_df.empty:
                    if self.monitor:
                        tick_monitor.update({trading_day: TickMonitor.EMPTY})
                else:
                    if self.monitor:
                        tick_monitor.update({trading_day: TickMonitor.NORMAL})

                    daily_tick_df = daily_tick_df.reset_index(drop=True)
                    daily_tick_df["VolumeTrade"] = daily_tick_df["TotalVolumeTrade"].diff()
                    daily_tick_df["ValueTrade"] = daily_tick_df["TotalValueTrade"].diff()
                    daily_tick_df.loc[0, "VolumeTrade"] = daily_tick_df.loc[0, "TotalVolumeTrade"]
                    daily_tick_df.loc[0, "ValueTrade"] = daily_tick_df.loc[0, "TotalValueTrade"]
                    daily_tick_df["VolumeTrade"] = daily_tick_df["VolumeTrade"].clip_lower(0)
                    daily_tick_df["ValueTrade"] = daily_tick_df["ValueTrade"].clip_lower(0)

                    daily_tick_df_list.append(daily_tick_df)

            tick_df = pd.concat(daily_tick_df_list, axis=0)

            tick_df = tick_df.reindex(columns=INDEX_CLEAN_TICK_COLUMNS)
            tick_df.columns = INDEX_TARGET_TICK_COLUMNS

        return tick_df, tick_monitor

    def load_third_daily_data(self, start_date, end_date):
        """从ThirdParty接口载入标的一段交易日中的所有日频数据，并根据列进行筛选、清洗
        """
        daily_monitor = dict()

        trading_day_list = get_trading_day(start_date, end_date)

        calc_time_groups = split_calc_date_into_group(trading_day_list, MAX_DAILY_KLINE)  ### 日K线最长查询为365天

        sub_dailys_list = []

        for group in calc_time_groups:
            start_date_time = "{0}{1}".format(group[0], "090000000")
            end_date_time = "{0}{1}".format(group[-1], "200000000")
            sub_daily_data = self.tma.getMDSecurityKLineDataFrame(self.code, start_date_time, end_date_time, 10, 25)

            if not sub_daily_data.empty:
                sub_daily_data = sub_daily_data[SHENWAN_RAW_DAILY_COLUMNS]
                sub_dailys_list.append(sub_daily_data)

        if len(sub_dailys_list) == 0:
            daily_df = pd.DataFrame()
        else:
            daily_df = pd.concat(sub_dailys_list, axis=0)

        if daily_df.empty:
            daily_df = pd.DataFrame(columns=SHENWAN_TARGET_DAILY_COLUMNS)
            if self.monitor:
                daily_monitor.update({trading_day: DailyMonitor.EMPTY for trading_day in trading_day_list})
        else:
            daily_df = daily_df.reindex(columns=SHENWAN_CLEAN_DAILY_COLUMNS).reset_index(drop=True)
            daily_df.columns = SHENWAN_TARGET_DAILY_COLUMNS

            if self.monitor:
                for trading_day in trading_day_list:
                    daily_daily_df = daily_df[daily_df["Date"] == trading_day]
                    if daily_daily_df.empty:
                        daily_monitor.update({trading_day: DailyMonitor.EMPTY})
                    else:
                        daily_monitor.update({trading_day: DailyMonitor.NORMAL})

        return daily_df, daily_monitor

    def load_third_minute_data(self, start_date, end_date):
        """
         从ThirdParty接口载入标的一段交易日中的所有分钟数据，并根据列进行筛选、清洗、清洗
        """
        minute_monitor = dict()

        trading_day_list = get_trading_day(start_date, end_date)

        calc_time_groups = split_calc_date_into_group(trading_day_list, MAX_MINUTE_KLINE)  ## 分钟K线最长查询为7天

        sub_minutes_list = []

        for group in calc_time_groups:
            start_date_time = "{0}{1}".format(group[0], "090000000")
            end_date_time = "{0}{1}".format(group[-1], "153000000")
            sub_minute_data = self.tma.getKLine4ZTDataFrame(self.code, start_date_time, end_date_time, 10, 20)

            if not sub_minute_data.empty:
                sub_minute_data = sub_minute_data[INDEX_RAW_MINUTE_COLUMNS]
                sub_minutes_list.append(sub_minute_data)

        if len(sub_minutes_list) == 0:
            minute_df = pd.DataFrame()
        else:
            minute_df = pd.concat(sub_minutes_list, axis=0)

        if minute_df.empty:
            minute_df = pd.DataFrame(columns=INDEX_TARGET_MINUTE_COLUMNS)
            minute_monitor.update({trading_day: MinuteMonitor.EMPTY for trading_day in trading_day_list})
        else:
            minute_df["Timestamp"] = (minute_df["MDDate"] + minute_df["MDTime"]).apply(
                                               lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            minute_df = minute_df.reindex(columns=INDEX_CLEAN_MINUTE_COLUMNS)
            minute_df.columns = INDEX_TARGET_MINUTE_COLUMNS
            price_columns = ["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]
            minute_df[price_columns] = minute_df[price_columns].fillna(method="ffill")
            minute_df[["Volume", "Amount"]] = minute_df[["Volume", "Amount"]].fillna(0.)
            # 分钟数据处理，剔除开盘集合竞价092500和收盘集合竞价150000数据
            minute_df.index = minute_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(int(x)))
            minute_df = minute_data_transform(minute_df, ["drop", "drop"])
            minute_df = minute_df.reindex(columns=INDEX_TARGET_MINUTE_COLUMNS).reset_index(drop=True)

            if self.monitor:
                for trading_day in trading_day_list:
                    daily_minute_df = minute_df[minute_df["Date"] == trading_day]
                    if daily_minute_df.empty:
                        minute_monitor.update({trading_day: TickMonitor.EMPTY})
                    else:
                        minute_monitor.update({trading_day: TickMonitor.NORMAL})

        return minute_df, minute_monitor