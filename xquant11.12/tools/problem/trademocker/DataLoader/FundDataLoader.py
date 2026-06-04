from DataInterface.Config import THIRD_MAX_FRAME_LENGTH
from DataInterface.Config import FUND_RAW_DAILY_COLUMNS, FUND_RAW_MINUTE_COLUMNS, FUND_RAW_TICK_COLUMNS, FUND_RAW_TRANSACTION_COLUMNS, FUND_RAW_ORDER_COLUMNS
from DataInterface.Config import FUND_CLEAN_DAILY_COLUMNS, FUND_CLEAN_MINUTE_COLUMNS, FUND_CLEAN_TICK_COLUMNS, FUND_CLEAN_TRANSACTION_COLUMNS, FUND_CLEAN_ORDER_COLUMNS
from DataInterface.Config import FUND_TARGET_DAILY_COLUMNS, FUND_TARGET_MINUTE_COLUMNS, FUND_TARGET_TICK_COLUMNS, FUND_TARGET_TRANSACTION_COLUMNS, FUND_TARGET_ORDER_COLUMNS
from DataMonitor.Monitor import DailyMonitor, MinuteMonitor, TickMonitor, TransactionMonitor, OrderMonitor
from DataLoader.DataCleanUtil import tick_data_zero_price_filter, tick_data_circuit_filter, minute_data_transform
from Utils.HelpFunc import get_trading_day, split_calc_date_into_group

import numpy as np
import pandas as pd
import datetime as dt
from xquant.factordata import FactorData
from xquant.thirdpartydata.marketdata import MarketData as ThirdMarketData
from xquant.funddata import FundData


class FundDataLoader:
    def __init__(self, code: str, data_source: str="mdp", monitor: bool=False):
        self.code = code
        self.data_source = data_source
        self.monitor = monitor

        self.fa = FactorData()
        self.fd = FundData()
        self.tma = ThirdMarketData() if self.data_source == "third" else None

    def load_daily_data(self, start_date, end_date):
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
            sub_daily_df = self.fd.get_fund_data(self.code, start_date_time, end_date_time, "K_DAY")

            if not sub_daily_df.empty:
                sub_daily_df = sub_daily_df[FUND_RAW_DAILY_COLUMNS]
                sub_dailys_list.append(sub_daily_df)

        if len(sub_dailys_list) == 0:
            daily_df = pd.DataFrame(columns=FUND_RAW_DAILY_COLUMNS)
        else:
            daily_df = pd.concat(sub_dailys_list, axis=0)

        # 从WIND获取其他日频字段, Wind落地库限制了并发访问数量，大规模访问受限
        wind_df = self.fa.get_factor_value("WIND_ChinaClosedFundEODPrice", factors=["S_INFO_WINDCODE", "TRADE_DT", "S_DQ_PRECLOSE", "S_DQ_ADJFACTOR"],
                                           S_INFO_WINDCODE=self.code, TRADE_DT=[">={}".format(trading_day_list[0]),
                                                                                "<={}".format(trading_day_list[-1])])
        if not wind_df.empty:
            wind_df = wind_df.sort_values(by=["TRADE_DT"])
            wind_df = wind_df[["TRADE_DT", "S_DQ_PRECLOSE", "S_DQ_ADJFACTOR"]]
            wind_df.columns = ["MDDate", "PreviousClose", "AdjFactor"]
            wind_df["TradeStatus"] = "交易"
        else:
            wind_df = pd.DataFrame(columns=["MDDate", "PreviousClose", "AdjFactor"])
            wind_df["MDDate"] = daily_df["MDDate"]
            wind_df["PreviousClose"] = np.nan
            wind_df["AdjFactor"] = np.nan
            wind_df["TradeStatus"] = np.nan

        wind_df["MaxPrice"] = np.round((1. + 0.1) * wind_df["PreviousClose"].astype(float), decimals=3)
        wind_df["MinPrice"] = np.round((1. - 0.1) * wind_df["PreviousClose"].astype(float), decimals=3)

        # 将Wind落地库信息合并到日频数据里，Inner连接：取mdp接口数据与wind落地库数据交集
        daily_df = pd.merge(daily_df, wind_df, on="MDDate", how="inner")

        # 参考Basic_Factor，将没有日期记录的数据全部填充为NAN
        valid_date_set = set(daily_df["MDDate"].tolist())
        invalid_date_list = list(set(trading_day_list).difference(valid_date_set))
        if len(invalid_date_list) != 0:
            daily_fill_df = pd.DataFrame(columns=daily_df.columns.tolist())
            daily_fill_df["MDDate"] = invalid_date_list
            daily_df = daily_df.append(daily_fill_df).sort_values(by=["MDDate"])

        if daily_df.empty:
            daily_df = pd.DataFrame(columns=FUND_TARGET_DAILY_COLUMNS)
            if self.monitor:
                daily_monitor.update({trading_day: DailyMonitor.EMPTY for trading_day in trading_day_list})
        else:
            daily_df = daily_df.reindex(columns=FUND_CLEAN_DAILY_COLUMNS).reset_index(drop=True)
            daily_df.columns = FUND_TARGET_DAILY_COLUMNS

            if self.monitor:
                for trading_day in trading_day_list:
                    daily_daily_df = daily_df[daily_df["Date"] == trading_day]
                    if daily_daily_df.empty:
                        daily_monitor.update({trading_day: DailyMonitor.EMPTY})
                    else:
                        daily_monitor.update({trading_day: DailyMonitor.NORMAL})

        return daily_df, daily_monitor

    def load_minute_data(self, start_date, end_date):
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
            sub_minute_df = self.fd.get_fund_data(self.code, start_date_time, end_date_time, "K_1MIN")

            if not sub_minute_df.empty:
                sub_minute_df = sub_minute_df[FUND_RAW_MINUTE_COLUMNS]
                sub_minutes_list.append(sub_minute_df)

        if len(sub_minutes_list) == 0:
            minute_df = pd.DataFrame()
        else:
            minute_df = pd.concat(sub_minutes_list, axis=0)

        if minute_df.empty:
            minute_df = pd.DataFrame(columns=FUND_TARGET_MINUTE_COLUMNS)
            if self.monitor:
                minute_monitor.update({trading_day: MinuteMonitor.EMPTY for trading_day in trading_day_list})
        else:
            minute_df["Timestamp"] = (minute_df["MDDate"] + minute_df["MDTime"]).apply(lambda x: dt.datetime.strptime(x+"000", "%Y%m%d%H%M%S%f").timestamp())
            minute_df = minute_df.reindex(columns=FUND_CLEAN_MINUTE_COLUMNS)
            minute_df.columns = FUND_TARGET_MINUTE_COLUMNS
            price_columns = ["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]
            minute_df[price_columns] = minute_df[price_columns].fillna(method="ffill")
            minute_df[["Volume", "Amount"]] = minute_df[["Volume", "Amount"]].fillna(0.)
            # 分钟数据处理，剔除开盘集合竞价092500和收盘集合竞价150000数据
            minute_df.index = minute_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(int(x)))
            minute_df = minute_data_transform(minute_df, ["drop", "drop"])
            minute_df = minute_df.reindex(columns=FUND_TARGET_MINUTE_COLUMNS).reset_index(drop=True)

            if self.monitor:
                for trading_day in trading_day_list:
                    daily_minute_df = minute_df[minute_df["Date"] == trading_day]
                    if daily_minute_df.empty:
                        minute_monitor.update({trading_day: MinuteMonitor.EMPTY})
                    else:
                        minute_monitor.update({trading_day: MinuteMonitor.NORMAL})

        return minute_df, minute_monitor

    def load_tick_data(self, start_date, end_date):
        """ 载入FUND一段交易日中的所有Tick数据，并根据列进行筛选
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
            sub_tick_df = self.fd.get_fund_data(self.code, start_date_time, end_date_time, "TICK")

            if not sub_tick_df.empty:
                sub_tick_df = sub_tick_df[FUND_RAW_TICK_COLUMNS]
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
            tick_df = pd.DataFrame(columns=FUND_TARGET_TICK_COLUMNS)
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
                    first_tick_num_trades = daily_tick_df.NumTrades.iloc[0]
                    daily_tick_df["VolumeTrade"] = daily_tick_df["TotalVolumeTrade"].diff()
                    daily_tick_df["ValueTrade"] = daily_tick_df["TotalValueTrade"].diff()
                    daily_tick_df["NumTrades"] = daily_tick_df["NumTrades"].diff()
                    daily_tick_df["BidQty"] = daily_tick_df["TotalBidQty"]
                    daily_tick_df["OfferQty"] = daily_tick_df["TotalOfferQty"]
                    # 每日第1行的成交额、成交量等于累计成交额、累计成交量
                    daily_tick_df.loc[0, "VolumeTrade"] = first_tick_volume
                    daily_tick_df.loc[0, "ValueTrade"] = first_tick_amount
                    daily_tick_df.loc[0, "NumTrades"] = first_tick_num_trades
                    daily_tick_df["VolumeTrade"] = daily_tick_df["VolumeTrade"].clip_lower(0)
                    daily_tick_df["ValueTrade"] = daily_tick_df["ValueTrade"].clip_lower(0)
                    daily_tick_df["NumTrades"] = daily_tick_df["NumTrades"].clip_lower(0)

                    daily_tick_df_list.append(daily_tick_df)

            tick_df = pd.concat(daily_tick_df_list, axis=0)

            tick_df = tick_df.reindex(columns=FUND_CLEAN_TICK_COLUMNS)
            tick_df.columns = FUND_TARGET_TICK_COLUMNS

        return tick_df, tick_monitor

    def load_transaction_data(self, start_date, end_date):
        """ 载入FUND的一段交易日中的所有逐笔成交数据，并根据列进行筛选、清洗
        """
        transaction_monitor = dict()

        trading_day_list = get_trading_day(start_date, end_date)

        if self.data_source == "mdp":
            max_frame_length = THIRD_MAX_FRAME_LENGTH
        else:
            max_frame_length = 1

        calc_time_groups = split_calc_date_into_group(trading_day_list, max_frame_length)

        sub_transactions_list = []

        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            if self.data_source == "mdp":
                start_date_time = "{0} {1}".format(sub_start_date, "000001000")
                end_date_time = "{0} {1}".format(sub_end_date, "235959000")
                sub_transactions_df = self.fd.get_fund_data(self.code, start_date_time, end_date_time, "TRANSACTION")
            else:
                start_date_time = "{0}{1}".format(sub_start_date, "000001")
                end_date_time = "{0}{1}".format(sub_end_date, "235959")
                sub_transactions_df = self.tma.getMDTransactionDataFrame(self.code, start_date_time, end_date_time)

            if not sub_transactions_df.empty:
                sub_transactions_df = sub_transactions_df[FUND_RAW_TRANSACTION_COLUMNS]
                sub_transactions_list.append(sub_transactions_df)

        if len(sub_transactions_list) == 0:
            transactions_df = pd.DataFrame()
        else:
            transactions_df = pd.concat(sub_transactions_list, axis=0)

        if transactions_df.empty:
            transactions_df = pd.DataFrame(columns=FUND_TARGET_TRANSACTION_COLUMNS)
            if self.monitor:
                transaction_monitor.update({trading_day: TransactionMonitor.EMPTY for trading_day in trading_day_list})
        else:
            transactions_df["Timestamp"] = (transactions_df["MDDate"] + transactions_df["MDTime"]).apply(
                                             lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            transactions_df = transactions_df.reindex(columns=FUND_CLEAN_TRANSACTION_COLUMNS)
            transactions_df.columns = FUND_TARGET_TRANSACTION_COLUMNS

            if self.monitor:
                for trading_day in trading_day_list:
                    daily_transaction_df = transactions_df[transactions_df["Date"] == trading_day]
                    if daily_transaction_df.empty:
                        transaction_monitor.update({trading_day: TransactionMonitor.EMPTY})
                    else:
                        transaction_monitor.update({trading_day: TransactionMonitor.NORMAL})

        return transactions_df, transaction_monitor

    def load_order_data(self, start_date, end_date):
        """"""
        order_monitor = dict()

        trading_day_list = get_trading_day(start_date, end_date)

        if self.data_source == "mdp":
            max_frame_length = THIRD_MAX_FRAME_LENGTH
        else:
            max_frame_length = 1

        calc_time_groups = split_calc_date_into_group(trading_day_list, max_frame_length)

        sub_orders_list = []

        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            if self.data_source == "mdp":
                start_date_time = "{0} {1}".format(sub_start_date, "000001000")
                end_date_time = "{0} {1}".format(sub_end_date, "235959000")
                sub_orders_df = self.fd.get_fund_data(self.code, start_date_time, end_date_time, "ORDER")
            else:
                start_date_time = "{0}{1}".format(sub_start_date, "000001")
                end_date_time = "{0}{1}".format(sub_end_date, "235959")
                sub_orders_df = self.tma.getMDOrderDataFrame(self.code, start_date_time, end_date_time)

            if not sub_orders_df.empty:
                sub_orders_df = sub_orders_df[FUND_RAW_ORDER_COLUMNS]
                sub_orders_list.append(sub_orders_df)

        if len(sub_orders_list) == 0:
            orders_df = pd.DataFrame()
        else:
            orders_df = pd.concat(sub_orders_list, axis=0)

        if orders_df.empty:
            orders_df = pd.DataFrame(columns=FUND_TARGET_ORDER_COLUMNS)
            if self.monitor:
                order_monitor.update({trading_day: OrderMonitor.EMPTY for trading_day in trading_day_list})
        else:
            orders_df["Timestamp"] = (orders_df["MDDate"] + orders_df["MDTime"]).apply(
                                      lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            orders_df = orders_df.reindex(columns=FUND_CLEAN_ORDER_COLUMNS)
            orders_df.columns = FUND_TARGET_ORDER_COLUMNS

            if self.monitor:
                for trading_day in trading_day_list:
                    daily_order_df = orders_df[orders_df["Date"] == trading_day]
                    if daily_order_df.empty:
                        order_monitor.update({trading_day: OrderMonitor.EMPTY})
                    else:
                        order_monitor.update({trading_day: OrderMonitor.NORMAL})

        return orders_df, order_monitor