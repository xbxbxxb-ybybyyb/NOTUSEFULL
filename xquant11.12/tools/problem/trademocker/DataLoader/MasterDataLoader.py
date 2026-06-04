from DataInterface.Config import STOCK_TARGET_TICK_COLUMNS,  STOCK_TARGET_TRANSACTION_COLUMNS, STOCK_TARGET_ORDER_COLUMNS
from DataInterface.Config import ALIGN_STOCK_TICK_COLUMNS, ALIGN_INDEX_TICK_COLUMNS, ALIGN_CBOND_TICK_COLUMNS, ALIGN_FUND_TICK_COLUMNS, ALIGN_FUTURE_TICK_COLUMNS
from DataLoader.DataCleanUtil import daily_clean_GEM_stock, daily_align_tick_tran_order_data, daily_align_index_tick_data, daily_align_future_tick_data
from DataLoader.StockDataLoader import StockDataLoader
from DataLoader.CBondDataLoader import CBondDataLoader
from DataLoader.FundDataLoader import FundDataLoader
from DataLoader.FutureDataLoader import FutureDataLoader
from DataLoader.IndexDataLoader import IndexDataLoader
from Utils.HelpFunc import my_print, get_code_type

import pandas as pd
import datetime as dt
from xquant.factordata import FactorData


class MasterDataLoader:
    def __init__(self, code: str, data_source: str="mdp", monitor=False):
        self.code = code
        self.data_source = data_source
        self.monitor = monitor

        self.fa = FactorData()

        self.code_type = get_code_type(self.code)

        if self.code_type in ["INDEX", "INDUSTRY"]:
            self.dl = IndexDataLoader(self.code, self.data_source, self.monitor)
        elif self.code_type == "FUTURE":
            self.dl = FutureDataLoader(self.code, self.data_source, self.monitor)
        elif self.code_type in ["ETF", "LOF"]:
            self.dl = FundDataLoader(self.code, self.data_source, self.monitor)
        elif self.code_type == "CBOND":
            self.dl = CBondDataLoader(self.code, self.data_source, self.monitor)
        elif self.code_type == "STOCK":
            self.dl = StockDataLoader(self.code, self.data_source, self.monitor)
        else:
            raise Exception(" Not Supported Code Type: {}-{} ".format(self.code, self.code_type))

    def load_daily_data(self, start_date, end_date):
        """ 获取股票/指数/可转债/FUND/Future一段日期日频数据
        """
        t1 = dt.datetime.now()

        daily_df, daily_monitor = self.dl.load_daily_data(start_date, end_date)

        t2 = dt.datetime.now()

        my_print(" {}-{}-{} Load Daily Data Time Cost: {}, Data Size: {} ".format(
                            self.code, start_date, end_date,  round((t2 - t1).total_seconds(), 2), daily_df.shape))

        return daily_df, daily_monitor

    def load_minute_data(self, start_date, end_date):
        """  获取股票/指数/可转债/FUND/Future一段日期分钟频数据
        """
        t1 = dt.datetime.now()

        minute_df, minute_monitor = self.dl.load_minute_data(start_date, end_date)

        t2 = dt.datetime.now()

        my_print(" {}-{}-{} Load Minute Data Time Cost: {}, Data Size: {} ".format(
                            self.code, start_date, end_date, round((t2 - t1).total_seconds(), 2), minute_df.shape))

        return minute_df, minute_monitor

    def load_tick_data(self, start_date, end_date):
        """ 获取股票/指数/可转债/FUND/Future一段日期Tick数据
        """
        t1 = dt.datetime.now()

        tick_df, tick_monitor = self.dl.load_tick_data(start_date, end_date)

        if self.code_type in ["STOCK", "CBOND", "ETF", "LOF"]:
            transaction_df, transaction_monitor = self.dl.load_transaction_data(start_date, end_date)

            # 创业板股票，Tick时间戳直接移3S
            if self.code.startswith("3"):
                tick_df, status_dict = self.clean_GEM_stock(tick_df, transaction_df)
                tick_monitor.update(status_dict)

            order_df = None
            if self.code.endswith(".SZ"):
                order_df, order_monitor = self.dl.load_order_data(start_date, end_date)

            tick_df = self.align_tick_tran_order_data(self.code, tick_df, transaction_df, order_df)

        elif self.code_type == "FUTURE":
            tick_df = self.align_future_tick_data(tick_df)

        elif self.code_type in ["INDEX", "INDUSTRY"]:
            tick_df = self.align_index_tick_data(tick_df)

        t2 = dt.datetime.now()

        my_print( " {}-{}-{} Load Tick Data Time Cost: {}, Data Size: {} ".format(
                         self.code, start_date, end_date, round((t2 - t1).total_seconds(), 2), tick_df.shape))

        return tick_df, tick_monitor

    def load_transaction_data(self, start_date, end_date):
        """ 获取股票/可转债/FUND一段日期Transaction数据
        """
        t1 = dt.datetime.now()

        if self.code_type in ["STOCK", "CBOND", "ETF", "LOF"]:
            transaction_df, transaction_monitor = self.dl.load_transaction_data(start_date, end_date)
        else:
            my_print(" No Transaction Data For {} ".format(self.code))
            transaction_df, transaction_monitor = pd.DataFrame(columns=STOCK_TARGET_TRANSACTION_COLUMNS), dict()

        t2 = dt.datetime.now()

        my_print(" {}-{}-{} Load Transaction Data Time Cost: {}, Data Size: {} ".format(
                  self.code, start_date, end_date, round((t2 - t1).total_seconds(), 2), transaction_df.shape))

        return transaction_df, transaction_monitor

    def load_order_data(self, start_date, end_date):
        """ 获取深交所股票/可转债/FUND一段日期Order数据
        """
        t1 = dt.datetime.now()

        if self.code_type in ["STOCK", "CBOND", "ETF", "LOF"] and self.code.endswith(".SZ"):
            order_df, order_monitor = self.dl.load_order_data(start_date, end_date)
        else:
            my_print(" No Order Data For {} ".format(self.code))
            order_df, order_monitor = pd.DataFrame(columns=STOCK_TARGET_ORDER_COLUMNS), dict()

        t2 = dt.datetime.now()

        my_print(" {}-{}-{} Load Order Data Time Cost: {}, Data Size: {} ".format(
                 self.code, start_date, end_date, round((t2 - t1).total_seconds(), 2), order_df.shape))

        return order_df, order_monitor

    @staticmethod
    def clean_GEM_stock(tick, transaction):
        """ 清洗创业板股票，如果TICK和TRANSACTION成交额数据对不上，TICK数据延迟3S
        """
        status_dict = dict()

        trading_day_list = sorted(list(set(tick["Date"].tolist())))

        clean_tick_list = []

        for trading_day in trading_day_list:
            daily_tick = tick[tick["Date"] == trading_day]
            daily_transaction = transaction[transaction["Date"] == trading_day]
            daily_tick, status = daily_clean_GEM_stock(daily_tick, daily_transaction)
            clean_tick_list.append(daily_tick)
            status_dict.update({trading_day: status})

        if len(clean_tick_list) == 0:
            clean_tick = pd.DataFrame(columns=STOCK_TARGET_TICK_COLUMNS)
        else:
            clean_tick = pd.concat(clean_tick_list, axis=0)

        return clean_tick, status_dict

    def align_tick_tran_order_data(self, code, tick, transaction, order=None):
        """ 对齐股票/可转债/FUND Tick数据（整合逐笔成交数据，逐笔委托StartIndex & EndIndex）
        """
        trading_day_list = sorted(list(set(tick["Date"].tolist())))

        aligned_tick_list = []

        for trading_day in trading_day_list:
            daily_tick = tick[tick["Date"] == trading_day]
            daily_transaction = transaction[transaction["Date"] == trading_day]
            daily_order = order[order["Date"] == trading_day] if order is not None else None
            if code.endswith(".SH"):
                if daily_transaction.empty:
                    my_print(" {}-{} Transaction Empty ".format(code, trading_day))
                    continue
            else:
                if daily_transaction.empty or daily_order.empty:
                    my_print(" {}-{} Transaction Empty={}, Order Empty={} ".format(code, trading_day, daily_transaction.empty, daily_order.empty))
                    continue

            aligned_daily_tick = daily_align_tick_tran_order_data(code, trading_day, daily_tick, daily_transaction, daily_order)
            aligned_tick_list.append(aligned_daily_tick)

        if len(aligned_tick_list) != 0:
            aligned_tick = pd.concat(aligned_tick_list, axis=0)
        else:
            if self.code_type == "STOCK":
                ALIGN_COLUMNS = ALIGN_STOCK_TICK_COLUMNS
            elif self.code_type == "CBOND":
                ALIGN_COLUMNS = ALIGN_CBOND_TICK_COLUMNS
            elif self.code_type in ["ETF", "LOF"]:
                ALIGN_COLUMNS = ALIGN_FUND_TICK_COLUMNS
            else:
                raise Exception(" Not Supported For Align Tick & Transaction & Order: {}-{} ".format(self.code, self.code_type))

            aligned_tick = pd.DataFrame(columns=ALIGN_COLUMNS)

        return aligned_tick

    @staticmethod
    def align_index_tick_data(tick):
        """ 对齐指数/行业指数Tick数据
        """
        trading_day_list = sorted(list(set(tick["Date"].tolist())))

        aligned_tick_list = []

        for trading_day in trading_day_list:
            daily_tick = tick[tick["Date"] == trading_day]
            aligned_tick = daily_align_index_tick_data(trading_day, daily_tick)
            aligned_tick_list.append(aligned_tick)

        if len(aligned_tick_list) != 0:
            aligned_tick = pd.concat(aligned_tick_list, axis=0)
        else:
            aligned_tick = pd.DataFrame(columns=ALIGN_INDEX_TICK_COLUMNS)

        return aligned_tick

    @staticmethod
    def align_future_tick_data(tick):
        """ 对齐期货Tick数据
        """
        trading_day_list = sorted(list(set(tick["Date"].tolist())))

        aligned_tick_list = []

        for trading_day in trading_day_list:
            daily_tick = tick[tick["Date"] == trading_day]
            aligned_tick = daily_align_future_tick_data(trading_day, daily_tick)
            aligned_tick_list.append(aligned_tick)

        if len(aligned_tick_list) != 0:
            aligned_tick = pd.concat(aligned_tick_list, axis=0)
        else:
            aligned_tick = pd.DataFrame(columns=ALIGN_FUTURE_TICK_COLUMNS)

        return aligned_tick