from DataInterface.Config import THIRD_MAX_FRAME_LENGTH
from DataInterface.Config import CBOND_RAW_DAILY_COLUMNS, CBOND_RAW_MINUTE_COLUMNS, CBOND_RAW_TICK_COLUMNS, CBOND_RAW_TRANSACTION_COLUMNS, CBOND_RAW_ORDER_COLUMNS
from DataInterface.Config import CBOND_CLEAN_DAILY_COLUMNS, CBOND_CLEAN_MINUTE_COLUMNS, CBOND_CLEAN_TICK_COLUMNS, CBOND_CLEAN_TRANSACTION_COLUMNS, CBOND_CLEAN_ORDER_COLUMNS
from DataInterface.Config import CBOND_TARGET_DAILY_COLUMNS, CBOND_TARGET_MINUTE_COLUMNS , CBOND_TARGET_TICK_COLUMNS, CBOND_TARGET_TRANSACTION_COLUMNS, CBOND_TARGET_ORDER_COLUMNS
from DataInterface.Config import CBOND_SH_VOLUME_MULTIPLE, CBOND_SH_MINUTE_ADJUST_COLUMNS, CBOND_SH_TICK_ADJUST_COLUMNS, CBOND_SH_TRANSACTION_ADJUST_COLUMNS, CBOND_SH_ORDER_ADJUST_COLUMNS
from DataMonitor.Monitor import DailyMonitor, MinuteMonitor, TickMonitor, TransactionMonitor, OrderMonitor
from DataLoader.DataCleanUtil import tick_data_zero_price_filter, tick_data_circuit_filter, minute_data_transform
from Utils.HelpFunc import get_trading_day, split_calc_date_into_group

import numpy as np
import pandas as pd
import datetime as dt
from xquant.factordata import FactorData
from xquant.thirdpartydata.marketdata import MarketData as ThirdMarketData
from xquant.bonddata import BondData


class CBondDataLoader:
    def __init__(self, code: str, data_source: str="mdp", monitor: bool=False):
        self.code = code
        self.data_source = data_source
        self.monitor = monitor

        self.fa = FactorData()
        self.bd = BondData()
        self.tma = ThirdMarketData() if self.data_source == "third" else None

    def load_daily_data(self, start_date, end_date):
        """ 载入可转债一段交易日中的所有日频数据，并根据列进行筛选、清洗
        """
        daily_monitor = dict()

        trading_day_list = get_trading_day(start_date, end_date)

        try:
            daily_df = self.fa.get_factor_value("Basic_factor", stock=[self.code], mddate=trading_day_list,
                                       factor_names=CBOND_RAW_DAILY_COLUMNS, category="bond")
        except:
            daily_df = pd.DataFrame(columns=CBOND_RAW_DAILY_COLUMNS)

        if daily_df.empty:
            daily_df = pd.DataFrame(columns=CBOND_TARGET_DAILY_COLUMNS)
            if self.monitor:
                daily_monitor.update({trading_day: DailyMonitor.EMPTY for trading_day in trading_day_list})
        else:
            daily_df = daily_df.droplevel(1)

            # 转换数据单位
            daily_df["volume"] = daily_df["volume"] * 10
            daily_df["amount"] = daily_df["amount"] * 1000

            # 加入涨跌停价格
            daily_df['maxup'] = 10**9
            daily_df['maxdown'] = 0.01 if self.code.endswith(".SH") else 0.001
            daily_df["adjfactor"] = 1.

            daily_df["date"] = list(map(str, list(daily_df.index)))
            daily_df = daily_df.reindex(columns=CBOND_CLEAN_DAILY_COLUMNS).reset_index(drop=True)
            daily_df.columns = CBOND_TARGET_DAILY_COLUMNS

            if self.monitor:
                for trading_day in trading_day_list:
                    daily_daily_df = daily_df[daily_df["Date"] == trading_day]
                    if daily_daily_df.empty:
                        daily_monitor.update({trading_day: DailyMonitor.EMPTY})
                    else:
                        daily_monitor.update({trading_day: DailyMonitor.NORMAL})

        return daily_df, daily_monitor

    def load_minute_data(self, start_date, end_date):
        """ 载入可转债一段交易日中的所有分钟数据，并根据列进行筛选、清洗、清洗
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
            sub_minute_df = self.bd.get_bond_data(self.code, start_date_time, end_date_time, "K_1MIN")

            if not sub_minute_df.empty:
                sub_minute_df = sub_minute_df[CBOND_RAW_MINUTE_COLUMNS]
                sub_minutes_list.append(sub_minute_df)

        if len(sub_minutes_list) == 0:
            minute_df = pd.DataFrame()
        else:
            minute_df = pd.concat(sub_minutes_list, axis=0)

        if minute_df.empty:
            minute_df = pd.DataFrame(columns=CBOND_TARGET_MINUTE_COLUMNS)
            if self.monitor:
                minute_monitor.update({trading_day: MinuteMonitor.EMPTY for trading_day in trading_day_list})
        else:
            minute_df["Timestamp"] = (minute_df["MDDate"] + minute_df["MDTime"]).apply(
                                                lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            minute_df = minute_df.reindex(columns=CBOND_CLEAN_MINUTE_COLUMNS)
            minute_df.columns = CBOND_TARGET_MINUTE_COLUMNS
            price_columns = ["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]
            minute_df[price_columns] = minute_df[price_columns].fillna(method="ffill")
            minute_df[["Volume", "Amount"]] = minute_df[["Volume", "Amount"]].fillna(0.)
            if self.code.endswith(".SH"):
                minute_df[CBOND_SH_MINUTE_ADJUST_COLUMNS] = minute_df[CBOND_SH_MINUTE_ADJUST_COLUMNS] * CBOND_SH_VOLUME_MULTIPLE
            # 分钟数据处理，剔除开盘集合竞价092500和收盘集合竞价150000数据
            minute_df.index = minute_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(int(x)))
            minute_df = minute_data_transform(minute_df, ["drop", "drop"])
            minute_df = minute_df.reindex(columns=CBOND_TARGET_MINUTE_COLUMNS).reset_index(drop=True)

            if self.monitor:
                for trading_day in trading_day_list:
                    daily_minute_df = minute_df[minute_df["Date"] == trading_day]
                    if daily_minute_df.empty:
                        minute_monitor.update({trading_day: MinuteMonitor.EMPTY})
                    else:
                        minute_monitor.update({trading_day: MinuteMonitor.NORMAL})

        return minute_df, minute_monitor

    def load_tick_data(self, start_date, end_date):
        """ 载入可转债一段交易日中的所有Tick数据，并根据列进行筛选
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
            sub_tick_df = self.bd.get_bond_data(self.code, start_date_time, end_date_time, "TICK")

            if not sub_tick_df.empty:
                sub_tick_df = sub_tick_df[CBOND_RAW_TICK_COLUMNS]
                sub_tick_df = sub_tick_df.replace({"PreClosePx": 0.0}, np.nan)  # 如遇PreClose为0的，以前值填充之
                sub_tick_df = sub_tick_df.fillna(method="ffill")
                # 将连续竞价期间OpenPrice, HighPrice和LowPrice为0的条目删掉
                sub_tick_df = tick_data_zero_price_filter(sub_tick_df)
                # 剔除临停期间数据
                sub_tick_df = tick_data_circuit_filter(sub_tick_df)
                sub_ticks_list.append(sub_tick_df)

        if len(sub_ticks_list) == 0:
            tick_df = pd.DataFrame()
        else:
            tick_df = pd.concat(sub_ticks_list, axis=0)

        if tick_df.empty:
            tick_df = pd.DataFrame(columns=CBOND_TARGET_TICK_COLUMNS)
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

            tick_df = tick_df.reindex(columns=CBOND_CLEAN_TICK_COLUMNS)
            tick_df.columns = CBOND_TARGET_TICK_COLUMNS

            if self.code.endswith(".SH"):
                tick_df[CBOND_SH_TICK_ADJUST_COLUMNS] = tick_df[CBOND_SH_TICK_ADJUST_COLUMNS] * CBOND_SH_VOLUME_MULTIPLE

        return tick_df, tick_monitor

    def load_transaction_data(self, start_date, end_date):
        """ 载入可转债的一段交易日中的所有逐笔成交数据，并根据列进行筛选、清洗，目前上交所转债没有撤单数据
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
                sub_transactions_df = self.bd.get_bond_data(self.code, start_date_time, end_date_time, "TRANSACTION")
            else:
                start_date_time = "{0}{1}".format(sub_start_date, "000001")
                end_date_time = "{0}{1}".format(sub_end_date, "235959")
                sub_transactions_df = self.tma.getMDTransactionDataFrame(self.code, start_date_time, end_date_time)

            if not sub_transactions_df.empty:
                sub_transactions_df = sub_transactions_df[CBOND_RAW_TRANSACTION_COLUMNS]
                sub_transactions_list.append(sub_transactions_df)

        if len(sub_transactions_list) == 0:
            transactions_df = pd.DataFrame()
        else:
            transactions_df = pd.concat(sub_transactions_list, axis=0)

        if transactions_df.empty:
            transactions_df = pd.DataFrame(columns=CBOND_TARGET_TRANSACTION_COLUMNS)
            if self.monitor:
                transaction_monitor.update({trading_day: TransactionMonitor.EMPTY for trading_day in trading_day_list})
        else:
            transactions_df["Timestamp"] = (transactions_df["MDDate"] + transactions_df["MDTime"]).apply(
                                                 lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            transactions_df = transactions_df.reindex(columns=CBOND_CLEAN_TRANSACTION_COLUMNS)
            transactions_df.columns = CBOND_TARGET_TRANSACTION_COLUMNS

            if self.code.endswith(".SH"):
                transactions_df[CBOND_SH_TRANSACTION_ADJUST_COLUMNS] = transactions_df[CBOND_SH_TRANSACTION_ADJUST_COLUMNS] * CBOND_SH_VOLUME_MULTIPLE

            if self.monitor:
                for trading_day in trading_day_list:
                    daily_transaction_df = transactions_df[transactions_df["Date"] == trading_day]
                    if daily_transaction_df.empty:
                        transaction_monitor.update({trading_day: TransactionMonitor.EMPTY})
                    else:
                        transaction_monitor.update({trading_day: TransactionMonitor.NORMAL})

        return transactions_df, transaction_monitor

    def load_order_data(self, start_date, end_date):
        """加载逐笔委托数据，目前上交所转债没有逐笔委托数据"""
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
                sub_orders_df = self.bd.get_bond_data(self.code, start_date_time, end_date_time, "ORDER")
            else:
                start_date_time = "{0}{1}".format(sub_start_date, "000001")
                end_date_time = "{0}{1}".format(sub_end_date, "235959")
                sub_orders_df = self.tma.getMDOrderDataFrame(self.code, start_date_time, end_date_time)

            if not sub_orders_df.empty:
                sub_orders_df = sub_orders_df[CBOND_RAW_ORDER_COLUMNS]
                sub_orders_list.append(sub_orders_df)

        if len(sub_orders_list) == 0:
            orders_df = pd.DataFrame()
        else:
            orders_df = pd.concat(sub_orders_list, axis=0)

        if orders_df.empty:
            orders_df = pd.DataFrame(columns=CBOND_TARGET_ORDER_COLUMNS)
            if self.monitor:
                order_monitor.update({trading_day: OrderMonitor.EMPTY for trading_day in trading_day_list})
        else:
            orders_df["Timestamp"] = (orders_df["MDDate"] + orders_df["MDTime"]).apply(
                                      lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            orders_df = orders_df.reindex(columns=CBOND_CLEAN_ORDER_COLUMNS)
            orders_df.columns = CBOND_TARGET_ORDER_COLUMNS
            
            if self.code.endswith(".SH"):
                orders_df[CBOND_SH_ORDER_ADJUST_COLUMNS] = orders_df[CBOND_SH_ORDER_ADJUST_COLUMNS] * CBOND_SH_VOLUME_MULTIPLE

            if self.monitor:
                for trading_day in trading_day_list:
                    daily_order_df = orders_df[orders_df["Date"] == trading_day]
                    if daily_order_df.empty:
                        order_monitor.update({trading_day: OrderMonitor.EMPTY})
                    else:
                        order_monitor.update({trading_day: OrderMonitor.NORMAL})

        return orders_df, order_monitor



