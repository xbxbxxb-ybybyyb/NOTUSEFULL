from DataInterface.Config import THIRD_MAX_FRAME_LENGTH
from DataInterface.Config import FUTURE_RAW_DAILY_COLUMNS, FUTURE_RAW_MINUTE_COLUMNS, FUTURE_RAW_TICK_COLUMNS
from DataInterface.Config import FUTURE_CLEAN_DAILY_COLUMNS, FUTURE_CLEAN_MINUTE_COLUMNS, FUTURE_CLEAN_TICK_COLUMNS
from DataInterface.Config import FUTURE_TARGET_DAILY_COLUMNS, FUTURE_TARGET_MINUTE_COLUMNS, FUTURE_TARGET_TICK_COLUMNS
from DataMonitor.Monitor import DailyMonitor, MinuteMonitor, TickMonitor
from DataLoader.DataCleanUtil import tick_data_zero_price_filter, tick_data_circuit_filter, minute_data_transform
from Utils.HelpFunc import get_trading_day, get_future_contract_type, split_calc_date_into_group

import numpy as np
import pandas as pd
import datetime as dt
from xquant.factordata import FactorData
from xquant.futuredata import FutureData


class FutureDataLoader:
    def __init__(self, code: str, data_source: str="mdp", monitor=False):
        self.code = code
        self.data_source = data_source
        self.monitor = monitor

        self.future_contract_type = get_future_contract_type(self.code)

        self.fa = FactorData()
        self.fd = FutureData()

    def load_daily_data(self, start_date, end_date):
        """ 载入Future一段交易日中的所有日频数据，并根据列进行筛选、清洗
        """
        daily_monitor = dict()

        trading_day_list = get_trading_day(start_date, end_date)

        calc_time_groups = split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)

        sub_dailys_list = []

        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "000001000")
            end_date_time = "{0} {1}".format(sub_end_date, "235959000")
            if self.future_contract_type is not None:
                sub_daily_df = self.fd.get_future_data(self.code[:-2], start_date_time, end_date_time, "K_DAY",
                                                        contract_type=self.future_contract_type)
            else:
                sub_daily_df = self.fd.get_future_data(self.code, start_date_time, end_date_time, "K_DAY")

            if not sub_daily_df.empty:
                sub_daily_df = sub_daily_df[FUTURE_RAW_DAILY_COLUMNS]
                sub_dailys_list.append(sub_daily_df)

        if len(sub_dailys_list) == 0:
            daily_df = pd.DataFrame()
        else:
            daily_df = pd.concat(sub_dailys_list, axis=0)

        if daily_df.empty:
            daily_df = pd.DataFrame(columns=FUTURE_TARGET_DAILY_COLUMNS)
            if self.monitor:
                daily_monitor.update({trading_day: DailyMonitor.EMPTY for trading_day in trading_day_list})
        else:
            daily_df["AdjFactor"] = 1
            daily_df["TradeStatus"] = "交易"
            daily_df = daily_df.reindex(columns=FUTURE_CLEAN_DAILY_COLUMNS).reset_index(drop=True)
            daily_df.columns = FUTURE_TARGET_DAILY_COLUMNS

            if self.monitor:
                for trading_day in trading_day_list:
                    daily_daily_df = daily_df[daily_df["Date"] == trading_day]
                    if daily_daily_df.empty:
                        daily_monitor.update({trading_day: DailyMonitor.EMPTY})
                    else:
                        daily_monitor.update({trading_day: DailyMonitor.NORMAL})

        return daily_df, daily_monitor

    def load_minute_data(self, start_date, end_date):
        """ 载入Future一段交易日中的所有分钟数据，并根据列进行筛选、清洗、清洗
        """
        minute_monitor = dict()

        trading_day_list = get_trading_day(start_date, end_date)

        calc_time_groups = split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)

        sub_minutes_list = []

        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "000001000")
            end_date_time = "{0} {1}".format(sub_end_date, "235959000")
            if self.future_contract_type is not None:
                sub_minute_df = self.fd.get_future_data(self.code[:-2], start_date_time, end_date_time, "K_1MIN",
                                                         contract_type=self.future_contract_type)
            else:
                sub_minute_df = self.fd.get_future_data(self.code, start_date_time, end_date_time, "K_1MIN")

            if not sub_minute_df.empty:
                sub_minute_df = sub_minute_df[FUTURE_RAW_MINUTE_COLUMNS]
                sub_minutes_list.append(sub_minute_df)

        if len(sub_minutes_list) == 0:
            minute_df = pd.DataFrame()
        else:
            minute_df = pd.concat(sub_minutes_list, axis=0)

        if minute_df.empty:
            minute_df = pd.DataFrame(columns=FUTURE_TARGET_MINUTE_COLUMNS)
            if self.monitor:
                minute_monitor.update({trading_day: MinuteMonitor.EMPTY for trading_day in trading_day_list})
        else:
            minute_df["Timestamp"] = (minute_df["MDDate"] + minute_df["MDTime"]).apply(
                                                lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            minute_df = minute_df.reindex(columns=FUTURE_CLEAN_MINUTE_COLUMNS)
            minute_df.columns = FUTURE_TARGET_MINUTE_COLUMNS
            price_columns = ["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]
            minute_df[price_columns] = minute_df[price_columns].fillna(method="ffill")
            minute_df[["Volume", "Amount"]] = minute_df[["Volume", "Amount"]].fillna(0.)
            # 分钟数据处理，剔除开盘集合竞价092500和收盘集合竞价150000数据
            minute_df.index = minute_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(int(x)))
            minute_df = minute_data_transform(minute_df, ["drop", "drop"])
            minute_df = minute_df.reindex(columns=FUTURE_TARGET_MINUTE_COLUMNS).reset_index(drop=True)

            if self.monitor:
                for trading_day in trading_day_list:
                    daily_minute_df = minute_df[minute_df["Date"] == trading_day]
                    if daily_minute_df.empty:
                        minute_monitor.update({trading_day: MinuteMonitor.EMPTY})
                    else:
                        minute_monitor.update({trading_day: MinuteMonitor.NORMAL})

        return minute_df, minute_monitor

    def load_future_tick_by_frame(self, start_date, end_date):
        """ 载入Future一段交易日中的所有Tick数据，并根据列进行筛选
        """
        tick_monitor = dict()

        trading_day_list = get_trading_day(start_date, end_date)

        calc_time_groups = split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)

        sub_ticks_list = []

        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "000001000")
            end_date_time = "{0} {1}".format(sub_end_date, "235959000")
            if self.future_contract_type is not None:
                sub_tick_df = self.fd.get_future_data(self.code[:-2], start_date_time, end_date_time, "TICK",
                                                       contract_type=self.future_contract_type)
            else:
                sub_tick_df = self.fd.get_future_data(self.code, start_date_time, end_date_time, "TICK")

            if not sub_tick_df.empty:
                sub_tick_df = sub_tick_df[FUTURE_RAW_TICK_COLUMNS]
                if self.future_contract_type is not None:
                    sub_tick_df["HTSCSecurityID"] = self.code
                sub_tick_df = sub_tick_df.replace({"PreClosePx": 0.0}, np.nan)  # 如遇PreClose为0的，以前值填充之
                sub_tick_df = sub_tick_df.fillna(method="ffill")
                # 将连续竞价期间OpenPrice, HighPrice和LowPrice为0的条目删掉
                sub_tick_df = tick_data_zero_price_filter(sub_tick_df)
                sub_tick_df = tick_data_circuit_filter(sub_tick_df)
                sub_ticks_list.append(sub_tick_df)

        if len(sub_ticks_list) == 0:
            tick_df = pd.DataFrame()
        else:
            tick_df = pd.concat(sub_ticks_list, axis=0)

        if tick_df.empty:
            tick_df = pd.DataFrame(columns=FUTURE_TARGET_TICK_COLUMNS)
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
                    first_tick_volume = daily_tick_df.TotalVolumeTrade.iloc[0]
                    first_tick_amount = daily_tick_df.TotalValueTrade.iloc[0]
                    daily_tick_df["VolumeTrade"] = daily_tick_df["TotalVolumeTrade"].diff()
                    daily_tick_df["ValueTrade"] = daily_tick_df["TotalValueTrade"].diff()
                    # 每日第1行的成交额、成交量等于累计成交额、累计成交量
                    daily_tick_df.loc[0, "VolumeTrade"] = first_tick_volume
                    daily_tick_df.loc[0, "ValueTrade"] = first_tick_amount
                    daily_tick_df["VolumeTrade"] = daily_tick_df["VolumeTrade"].clip_lower(0)
                    daily_tick_df["ValueTrade"] = daily_tick_df["ValueTrade"].clip_lower(0)

                    daily_tick_df_list.append(daily_tick_df)

            tick_df = pd.concat(daily_tick_df_list, axis=0)

            tick_df = tick_df.reindex(columns=FUTURE_CLEAN_TICK_COLUMNS)
            tick_df.columns = FUTURE_TARGET_TICK_COLUMNS

        return tick_df, tick_monitor