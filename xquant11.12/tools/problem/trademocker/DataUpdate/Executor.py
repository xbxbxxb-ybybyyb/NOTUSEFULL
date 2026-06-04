from DataInterface.Config import DAILY_STOCK_HBASE_COLUMNS, MINUTE_STOCK_HBASE_COLUMNS, TICK_STOCK_HBASE_COLUMNS, TRANSACTION_STOCK_HBASE_COLUMNS, ORDER_STOCK_HBASE_COLUMNS
from DataInterface.Config import DAILY_INDEX_HBASE_COLUMNS, MINUTE_INDEX_HBASE_COLUMNS, TICK_INDEX_HBASE_COLUMNS
from DataInterface.Config import DAILY_CBOND_HBASE_COLUMNS, MINUTE_CBOND_HBASE_COLUMNS, TICK_CBOND_HBASE_COLUMNS, TRANSACTION_CBOND_HBASE_COLUMNS, ORDER_CBOND_HBASE_COLUMNS
from DataInterface.Config import DAILY_FUND_HBASE_COLUMNS, MINUTE_FUND_HBASE_COLUMNS, TICK_FUND_HBASE_COLUMNS, TRANSACTION_FUND_HBASE_COLUMNS, ORDER_FUND_HBASE_COLUMNS
from DataInterface.Config import DAILY_FUTURE_HBASE_COLUMNS, MINUTE_FUTURE_HBASE_COLUMNS, TICK_FUTURE_HBASE_COLUMNS
from DataInterface.Config import STOCK_TARGET_DAILY_COLUMNS, STOCK_TARGET_MINUTE_COLUMNS, ALIGN_STOCK_TICK_COLUMNS, ALIGN_STOCK_TRANSACTION_COLUMNS, ALIGN_STOCK_ORDER_COLUMNS
from DataInterface.Config import INDEX_TARGET_DAILY_COLUMNS, INDEX_TARGET_MINUTE_COLUMNS, ALIGN_INDEX_TICK_COLUMNS
from DataInterface.Config import CBOND_TARGET_DAILY_COLUMNS, CBOND_TARGET_MINUTE_COLUMNS, ALIGN_CBOND_TICK_COLUMNS, ALIGN_CBOND_TRANSACTION_COLUMNS, ALIGN_CBOND_ORDER_COLUMNS
from DataInterface.Config import FUND_TARGET_DAILY_COLUMNS, FUND_TARGET_MINUTE_COLUMNS, ALIGN_FUND_TICK_COLUMNS, ALIGN_FUND_TRANSACTION_COLUMNS, ALIGN_FUND_ORDER_COLUMNS
from DataInterface.Config import FUTURE_TARGET_DAILY_COLUMNS, FUTURE_TARGET_MINUTE_COLUMNS, ALIGN_FUTURE_TICK_COLUMNS
from DataInterface.Config import DAILY_SUFFIX, MINUTE_SUFFIX, TICK_SUFFIX, TRANSACTION_SUFFIX, ORDER_SUFFIX
from DataInterface.Config import USER_ID, CELL_SIZE
from DataLoader.MasterDataLoader import MasterDataLoader
from DataInterface.HFData import HFData
from DataMonitor.DataMonitor import DataMonitor
from Utils.HelpFunc import my_print, get_code_type, get_index_type, get_industry_type, get_trading_day

import os
import datetime as dt
import pandas as pd
import pickle
from xquant.factordata import FactorData
from xquant.xqutils.xqfile import HDFSFile


class Executor(object):
    def __init__(self, library, code, data_source, start_date, end_date,
                       daily=False, minute=False, tick=False, tran=False, order=False,
                       overwrite=False, monitor=True, hbase=False, save_file=False, save_path=None):
        self.library = library
        self.code = code
        self.data_source = data_source
        self.start_date = start_date
        self.end_date = end_date
        self.daily = daily
        self.minute = minute
        self.tick = tick
        self.tran = tran
        self.order = order
        self.overwrite = overwrite
        self.monitor = monitor
        self.hbase = hbase
        self.save_file = save_file
        self.save_path = save_path

        self.code_type = get_code_type(self.code)
        if self.code_type == "INDEX":
            self.index_type = get_index_type(self.code)
        if self.code_type == "INDUSTRY":
            self.indus_type = get_industry_type(self.code)

        self.trading_day_list = get_trading_day(self.start_date, self.end_date)
        assert len(self.trading_day_list) > 0, " No Trading Days ! "
        self.start_date = self.trading_day_list[0]
        self.end_date = self.trading_day_list[-1]

        assert self.data_source in ["mdp", "third"], " Only Support Mdp/Third Data Source "

        if self.code_type not in ["STOCK", "CBOND", "ETF", "LOF"]:
            self.tran = False
        if not (self.code.endswith(".SZ") and self.code_type in ["STOCK", "CBOND", "ETF", "LOF"]):
            self.order = False

        if self.daily or self.minute or self.tick or self.tran or self.order:
            self.dlr = MasterDataLoader(self.code, self.data_source, self.monitor)

        if self.monitor:
            self.dmr = DataMonitor(self.library, self.code)

        self.fa = FactorData()
        self.hf = HDFSFile()
        self.hfd = HFData(self.library, self.code)

    def run(self):
        if self.daily:
            daily_df = self.prepare_daily_data()
            self.update_daily_data(daily_df)
        if self.minute:
            minute_df = self.prepare_minute_data()
            self.update_minute_data(minute_df)
        if self.tick:
            tick_df = self.prepare_tick_data()
            self.update_tick_data(tick_df)
        if self.tran:
            tran_df = self.prepare_transaction_data()
            self.update_transaction_data(tran_df)
        if self.order:
            order_df = self.prepare_order_data()
            self.update_order_data(order_df)

        if self.monitor:
            self.dmr.run_monitor()

    def update_daily_data(self, df):
        # 更改列名与因子库的因子名对应
        if self.code_type == "STOCK":
            df = df.reindex(columns=STOCK_TARGET_DAILY_COLUMNS)
            df.columns = DAILY_STOCK_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            df = df.reindex(columns=CBOND_TARGET_DAILY_COLUMNS)
            df.columns = DAILY_CBOND_HBASE_COLUMNS
        elif self.code_type in ["ETF", "LOF"]:
            df = df.reindex(columns=FUND_TARGET_DAILY_COLUMNS)
            df.columns = DAILY_FUND_HBASE_COLUMNS
        elif self.code_type == "FUTURE":
            df = df.reindex(columns=FUTURE_TARGET_DAILY_COLUMNS)
            df.columns = DAILY_FUTURE_HBASE_COLUMNS
        elif self.code_type == "INDEX":
            df = df.reindex(columns=INDEX_TARGET_DAILY_COLUMNS)
            df.columns = DAILY_INDEX_HBASE_COLUMNS
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                df = df.reindex(columns=INDEX_TARGET_DAILY_COLUMNS)
                df.columns = DAILY_INDEX_HBASE_COLUMNS
            else:
                raise Exception(" Not Supported Daily Data For Industry Type: {} ".format(self.indus_type))
        else:
            raise Exception(" Not Supported Daily Data For Code Type: {} ".format(self.code_type))

        if not df.empty:
            df = df.reset_index(drop=True)
            try:
                self.fa_update_factor_value(self.library, df, self.code, "20200102")
            except:
                if self.save_file:
                    available_date_list = sorted(list(set(df["{}_Date".format(DAILY_SUFFIX)].tolist())))
                    available_date_list = list(map(str, available_date_list))
                    start_date = available_date_list[0]
                    end_date = available_date_list[-1]
                    self.dump_to_file(df, DAILY_SUFFIX ,self.code, start_date, end_date, self.save_path)
                else:
                    raise Exception(" Dump Daily Data HBASE Error But No File Saved ")

    def update_minute_data(self, df):
        # 更改列名与因子库的因子名对应
        if self.code_type == "STOCK":
            df = df.reindex(columns=STOCK_TARGET_MINUTE_COLUMNS)
            df.columns = MINUTE_STOCK_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            df = df.reindex(columns=CBOND_TARGET_MINUTE_COLUMNS)
            df.columns = MINUTE_CBOND_HBASE_COLUMNS
        elif self.code_type in ["ETF", "LOF"]:
            df = df.reindex(columns=FUND_TARGET_MINUTE_COLUMNS)
            df.columns = MINUTE_FUND_HBASE_COLUMNS
        elif self.code_type == "FUTURE":
            df = df.reindex(columns=FUTURE_TARGET_MINUTE_COLUMNS)
            df.columns = MINUTE_FUTURE_HBASE_COLUMNS
        elif self.code_type == "INDEX":
            df = df.reindex(columns=INDEX_TARGET_MINUTE_COLUMNS)
            df.columns = MINUTE_INDEX_HBASE_COLUMNS
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                df = df.reindex(columns=INDEX_TARGET_MINUTE_COLUMNS)
                df.columns = MINUTE_INDEX_HBASE_COLUMNS
            else:
                raise Exception(" Not Supported Minute Data For Industry Type: {} ".format(self.indus_type))
        else:
            raise Exception(" Not Supported Minute Data For Code Type: {} ".format(self.code_type))

        if not df.empty:
            df = df.reset_index(drop=True)
            try:
                self.fa_update_factor_value(self.library, df, self.code, "20200102")
            except:
                if self.save_file :
                    available_date_list = sorted(list(set(df["{}_Date".format(MINUTE_SUFFIX)].tolist())))
                    available_date_list = list(map(str, available_date_list))
                    start_date = available_date_list[0]
                    end_date = available_date_list[-1]
                    self.dump_to_file(df, MINUTE_SUFFIX, self.code, start_date, end_date, self.save_path)
                else:
                    raise Exception(" Dump Minute Data HBASE Error But No File Saved ")

    def update_tick_data(self, df):
        if df.empty:
            return

        if self.code_type == "STOCK":
            df = df.reindex(columns=ALIGN_STOCK_TICK_COLUMNS)
            df.columns = TICK_STOCK_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            df = df.reindex(columns=ALIGN_CBOND_TICK_COLUMNS)
            df.columns = TICK_CBOND_HBASE_COLUMNS
        elif self.code_type == "ETF" or self.code_type == "LOF":
            df = df.reindex(columns=ALIGN_FUND_TICK_COLUMNS)
            df.columns = TICK_FUND_HBASE_COLUMNS
        elif self.code_type == "FUTURE":
            df = df.reindex(columns=ALIGN_FUTURE_TICK_COLUMNS)
            df.columns = TICK_FUTURE_HBASE_COLUMNS
        elif self.code_type == "INDEX":
            df = df.reindex(columns=ALIGN_INDEX_TICK_COLUMNS)
            df.columns = TICK_INDEX_HBASE_COLUMNS
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                df = df.reindex(columns=ALIGN_INDEX_TICK_COLUMNS)
                df.columns = TICK_INDEX_HBASE_COLUMNS
            else:
                Exception(" Not Supported Tick Data For Industry Type: {} ".format(self.indus_type))
        else:
            raise Exception(" Not Supported Tick Data For Code Type: {} ".format(self.code_type))

        # 将每一天的Tick频数据写入HBase
        update_day_list = sorted(df["{}_Date".format(TICK_SUFFIX)].drop_duplicates().to_list())
        for update_date in update_day_list:
            sub_df = df[df["{}_Date".format(TICK_SUFFIX)] == update_date]
            if not sub_df.empty:
                try:
                    self.fa_update_factor_value(self.library, sub_df, self.code, update_date)
                except:
                    if self.save_file:
                        self.dump_to_file(sub_df, TICK_SUFFIX, self.code, update_date, update_date, self.save_path)
                    else:
                        raise Exception(" Dump Tick Data HBASE Error But No File Saved ")

    def update_transaction_data(self, df):
        # 更改列名与因子库的因子名对应
        if df.empty:
            return

        if self.code_type == "STOCK":
            df = df.reindex(columns=ALIGN_STOCK_TRANSACTION_COLUMNS)
            df.columns = TRANSACTION_STOCK_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            df = df.reindex(columns=ALIGN_CBOND_TRANSACTION_COLUMNS)
            df.columns = TRANSACTION_CBOND_HBASE_COLUMNS
        elif self.code_type in ["ETF", "LOF"]:
            df = df.reindex(columns=ALIGN_FUND_TRANSACTION_COLUMNS)
            df.columns = TRANSACTION_FUND_HBASE_COLUMNS
        else:
            raise Exception(" Not Supported Transaction Data For Code Type: {} ".format(self.code_type))

        update_day_list = sorted(df["{}_Date".format(TRANSACTION_SUFFIX)].drop_duplicates().to_list())
        for update_date in update_day_list:
            sub_df = df[df["{}_Date".format(TRANSACTION_SUFFIX)] == update_date]
            if not sub_df.empty:
                try:
                    self.fa_update_factor_value(self.library, sub_df, self.code, update_date)
                except:
                    if self.save_file:
                        self.dump_to_file(sub_df, TRANSACTION_SUFFIX, self.code, update_date, update_date, self.save_path)
                    else:
                        raise Exception(" Dump Transaction Data HBASE Error But No File Saved ")

    def update_order_data(self, df):
        # 更改列名与因子库的因子名对应
        if df.empty:
            return

        if self.code_type == "STOCK":
            df = df.reindex(columns=ALIGN_STOCK_ORDER_COLUMNS)
            df.columns = ORDER_STOCK_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            df = df.reindex(columns=ALIGN_CBOND_ORDER_COLUMNS)
            df.columns = ORDER_CBOND_HBASE_COLUMNS
        elif self.code_type in ["ETF", "LOF"]:
            df = df.reindex(columns=ALIGN_FUND_ORDER_COLUMNS)
            df.columns = ORDER_FUND_HBASE_COLUMNS
        else:
            raise Exception(" Not Supported Order Data For Code Type: {} ".format(self.code_type))

        update_day_list = sorted(df["{}_Date".format(ORDER_SUFFIX)].drop_duplicates().to_list())
        for update_date in update_day_list:
            sub_df = df[df["{}_Date".format(ORDER_SUFFIX)] == update_date]
            if not sub_df.empty:
                try:
                    self.fa_update_factor_value(self.library, sub_df, self.code, update_date)
                except:
                    if self.save_file:
                        self.dump_to_file(sub_df, ORDER_SUFFIX, self.code, update_date, update_date, self.save_path)
                    else:
                        raise Exception(" Dump Order Data HBASE Error But No File Saved ")

    def fa_update_factor_value(self, lib_name, df, code, date):
        start_time = dt.datetime.now()
        if self.hbase:
            # space = sys.getsizeof(df) / 1024 / 1024
            # if space < 5:
            #     self.fa.update_factor_value(lib_name, df, code, date)
            self.fa.update_factor_value(lib_name, df, code, date, cell_size=CELL_SIZE)
        else:
            self.fa.update_factor_value(lib_name, df, code, date)
        end_time = dt.datetime.now()
        time_cost = (end_time - start_time).total_seconds()
        if time_cost >= 3:
            my_print(" WARN: Writing to HBASE costs {} sec for {} on {} ".format(round(time_cost, 2), code, date))

    def prepare_daily_data(self):
        """准备日频数据"""
        try:
            # 读取已存在的日频数据
            old_daily_df = self.hfd.get_old_daily_data()
            daily_date_list = list(set(old_daily_df["Date"].to_list()))
        except:
            daily_date_list = []
        daily_date_list = list(map(str, daily_date_list))

        if len(daily_date_list) != 0:  # 原有数据库有数据
            # 覆盖原有数据
            if self.overwrite:
                # 原有数据不在更新日期范围内的数据
                my_print(" Start Overwrite {} Daily Data {}-{} ".format(self.code, self.start_date, self.end_date))
                sub_old_daily_df = old_daily_df[~old_daily_df["Date"].isin(self.trading_day_list)]
                new_daily_df, daily_monitor = self.dlr.load_daily_data(self.start_date, self.end_date)
                ###合并两部分数据
                daily_df = sub_old_daily_df.append(new_daily_df)
                if not daily_df.empty:
                    daily_df = daily_df.sort_values(by=["Date"])
            else:
            # 增量更新日频数据
                extra_date_list = sorted(list(set(self.trading_day_list) - set(daily_date_list)))
                if len(extra_date_list) != 0:  # 要更新的数据，有一些原数据库中没有
                    new_start_date, new_end_date = extra_date_list[0], extra_date_list[-1]
                    # 更新原来没有的数据
                    my_print(" New Update {} Daily Data {}-{} ".format(self.code, new_start_date, new_end_date))
                    new_daily_df, daily_monitor = self.dlr.load_daily_data(new_start_date, new_end_date)
                    # 合并两部分数据
                    sub_old_daily_df = old_daily_df[~old_daily_df["Date"].isin(extra_date_list)]
                    daily_df = sub_old_daily_df.append(new_daily_df)
                    if not daily_df.empty:
                        daily_df = daily_df.sort_values(by=["Date"])
                else:  # 没有需要更新的数据，所有指定日期中数据都可以在原数据中找到
                    daily_df = old_daily_df
                    daily_monitor = dict()
        else:
            my_print(" New Update {} Daily Data {}-{}".format(self.code, self.start_date, self.end_date))
            daily_df, daily_monitor = self.dlr.load_daily_data(self.start_date, self.end_date)

        if self.monitor:
            self.dmr.update_daily_monitor(daily_monitor)

        return daily_df

    def prepare_minute_data(self):
        """准备分钟频数据"""
        try:
            ### 读取存量分钟数据
            old_minute_df = self.hfd.get_old_minute_data()
            minute_date_list = list(set(old_minute_df["Date"].to_list()))
        except:
            minute_date_list = []
        minute_date_list = list(map(str, minute_date_list))

        if len(minute_date_list) != 0:  # 原有数据库有数据
            if self.overwrite:
                # 原有数据不在更新日期范围内的数据
                my_print("Start Overwrite {} Minute Data {}-{}".format(self.code, self.start_date, self.end_date))
                sub_old_minute_df = old_minute_df[~old_minute_df["Date"].isin(self.trading_day_list)]
                new_minute_df, minute_monitor = self.dlr.load_minute_data(self.start_date, self.end_date)
                #合并两部分数据
                minute_df = sub_old_minute_df.append(new_minute_df)
                if not minute_df.empty:
                    minute_df = minute_df.sort_values(by=["Date", "Time"])
            else:
                # 增量更新分钟数据
                missing_date_list = sorted(list(set(self.trading_day_list) - set(minute_date_list)))
                if len(missing_date_list) != 0:  # 要更新的数据，有一些原数据库中没有
                    new_start_date, new_end_date = missing_date_list[0], missing_date_list[-1]
                    # 更新原来没有的数据
                    my_print(" New Update {} Minute Data {}-{} ".format(self.code, new_start_date, new_end_date))
                    new_minute_df, minute_monitor = self.dlr.load_minute_data(new_start_date, new_end_date)
                    # 合并两部分数据
                    sub_old_minute_df = old_minute_df[~old_minute_df["Date"].isin(missing_date_list)]
                    minute_df = sub_old_minute_df.append(new_minute_df)
                    if not minute_df.empty:
                        minute_df = minute_df.sort_values(by=["Date", "Time"])
                else:  # 没有需要更新的数据，所有指定日期中的数据都可以在原数据中找到
                    minute_df = old_minute_df
                    minute_monitor = {}
        else:  # 原数据库中没有数据，直接计算新数据并更新
            my_print(" New Update {} Minute Data {}-{} ".format(self.code, self.start_date, self.end_date))
            minute_df, minute_monitor = self.dlr.load_minute_data(self.start_date, self.end_date)

        if self.monitor:
            self.dmr.update_minute_monitor(minute_monitor)

        return minute_df

    def prepare_tick_data(self):
        """增量更新Tick频数据"""
        if self.overwrite:
            my_print(" Start Overwrite {} Tick Data {}-{} ".format(self.code, self.start_date, self.end_date))
            data, data_monitor = self.dlr.load_tick_data(self.start_date, self.end_date)

        else:
            TICK_HBASE_COLUMNS = ["{}_Timestamp".format(TICK_SUFFIX)]
            if self.code_type == "STOCK":
                ALIGN_COLUMNS = ALIGN_STOCK_TICK_COLUMNS
            elif self.code_type == "CBOND":
                ALIGN_COLUMNS = ALIGN_STOCK_TICK_COLUMNS
            elif self.code_type in ["ETF", "LOF"]:
                ALIGN_COLUMNS = ALIGN_FUND_TICK_COLUMNS
            elif self.code_type == "FUTURE":
                ALIGN_COLUMNS = ALIGN_FUTURE_TICK_COLUMNS
            elif self.code_type == "INDEX" or (self.code_type == "INDUSTRY" and self.indus_type == "SHENWAN"):
                ALIGN_COLUMNS = ALIGN_INDEX_TICK_COLUMNS
            else:
                raise Exception(" Not Supported Code Type: {} ".format(self.code_type))

            # 获取历史数据已经存在的交易日列表
            fake_date_list = self.fa.search_by_stock(self.library, self.code, self.trading_day_list)
            # 对每个交易日是否有值确认，获得真实已存在交易日列表
            existing_date_list = []
            for existing_date in fake_date_list:
                data_size = len(self.fa.search_by_stock_date(self.library, self.code, existing_date, TICK_HBASE_COLUMNS))
                if data_size != 0:
                    existing_date_list.append(existing_date)

            # 获取还未更新的交易日列表
            missing_date_list = sorted(list(set(self.trading_day_list) - set(existing_date_list)))
            if len(missing_date_list) != 0:
                update_start_date, update_end_date = missing_date_list[0], missing_date_list[-1]
                my_print(" New Update {} Tick Data {}-{} ".format(self.code, update_start_date, update_end_date))
                data, data_monitor = self.dlr.load_tick_data(update_start_date, update_end_date)
            else:
                data, data_monitor = pd.DataFrame(columns=ALIGN_COLUMNS), dict()

        if self.monitor:
            self.dmr.update_tick_monitor(data_monitor)

        return data

    def prepare_transaction_data(self):
        """增量更新逐笔成交数据"""
        if self.overwrite:
            my_print(" Start Overwrite {} Transaction Data {}-{} ".format(self.code, self.start_date, self.end_date))
            data, data_monitor = self.dlr.load_transaction_data(self.start_date, self.end_date)

        else:
            TRANSACTION_HBASE_COLUMNS = ["{}_Timestamp".format(TRANSACTION_SUFFIX)]
            if self.code_type == "STOCK":
                ALIGN_COLUMNS = ALIGN_STOCK_TRANSACTION_COLUMNS
            elif self.code_type == "CBOND":
                ALIGN_COLUMNS = ALIGN_STOCK_TRANSACTION_COLUMNS
            elif self.code_type in ["ETF", "LOF"]:
                ALIGN_COLUMNS = ALIGN_FUND_TRANSACTION_COLUMNS
            else:
                raise Exception(" Not Supported Code Type: {} ".format(self.code_type))

            # 获取历史数据已经存在的交易日列表
            fake_date_list = self.fa.search_by_stock(self.library, self.code, self.trading_day_list)
            # 对每个交易日是否有值确认，获得真实已存在交易日列表
            existing_date_list = []
            for existing_date in fake_date_list:
                data_size = len(
                    self.fa.search_by_stock_date(self.library, self.code, existing_date, TRANSACTION_HBASE_COLUMNS))
                if data_size != 0:
                    existing_date_list.append(existing_date)

            # 获取还未更新的交易日列表
            missing_date_list = sorted(list(set(self.trading_day_list) - set(existing_date_list)))
            if len(missing_date_list) != 0:
                update_start_date, update_end_date = missing_date_list[0], missing_date_list[-1]
                my_print(" New Update {} Transaction Data {}-{} ".format(self.code, update_start_date, update_end_date))
                data, data_monitor = self.dlr.load_transaction_data(update_start_date, update_end_date)
            else:
                data, data_monitor = pd.DataFrame(columns=ALIGN_COLUMNS), dict()

        if self.monitor:
            self.dmr.update_transaction_monitor(data_monitor)

        return data

    def prepare_order_data(self):
        """增量更新逐笔成交数据"""
        if self.overwrite:
            my_print(" Start Overwrite {} Order Data {}-{} ".format(self.code, self.start_date, self.end_date))
            data, data_monitor = self.dlr.load_order_data(self.start_date, self.end_date)

        else:
            ORDER_HBASE_COLUMNS = ["{}_Timestamp".format(ORDER_SUFFIX)]
            if self.code_type == "STOCK":
                ALIGN_COLUMNS = ALIGN_STOCK_ORDER_COLUMNS
            elif self.code_type == "CBOND":
                ALIGN_COLUMNS = ALIGN_STOCK_ORDER_COLUMNS
            elif self.code_type in ["ETF", "LOF"]:
                ALIGN_COLUMNS = ALIGN_FUND_ORDER_COLUMNS
            else:
                raise Exception(" Not Supported Code Type: {} ".format(self.code_type))

            # 获取历史数据已经存在的交易日列表
            fake_date_list = self.fa.search_by_stock(self.library, self.code, self.trading_day_list)
            # 对每个交易日是否有值确认，获得真实已存在交易日列表
            existing_date_list = []
            for existing_date in fake_date_list:
                data_size = len(
                    self.fa.search_by_stock_date(self.library, self.code, existing_date, ORDER_HBASE_COLUMNS))
                if data_size != 0:
                    existing_date_list.append(existing_date)

            # 获取还未更新的交易日列表
            missing_date_list = sorted(list(set(self.trading_day_list) - set(existing_date_list)))
            if len(missing_date_list) != 0:
                update_start_date, update_end_date = missing_date_list[0], missing_date_list[-1]
                my_print(" New Update {} Order Data {}-{} ".format(self.code, update_start_date, update_end_date))
                data, data_monitor = self.dlr.load_transaction_data(update_start_date, update_end_date)
            else:
                data, data_monitor = pd.DataFrame(columns=ALIGN_COLUMNS), dict()

        if self.monitor:
            self.dmr.update_order_monitor(data_monitor)

        return data

    def dump_to_file(self, df, freq, code, start_date, end_date, save_path):
        if "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ:
            root = os.path.join(USER_ID, save_path)
        else:
            root = save_path
        path = os.path.join(root, freq)
        file_name = os.path.join(path, "{}_{}_{}.pickle".format(code, start_date, end_date))

        if not self.hf.exists(path):
            self.hf.mkdir(path)

        with self.hf.open(file_name, "wb") as f:
            pickle.dump(df, f)



