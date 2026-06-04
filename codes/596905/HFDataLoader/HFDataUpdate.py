from HFDataLoader.Config import DAILY_STOCK_HBASE_COLUMNS, MINUTE_STOCK_HBASE_COLUMNS, TICK_STOCK_HBASE_COLUMNS
from HFDataLoader.Config import MOCK_TICK_STOCK_HBASE_COLUMNS
from HFDataLoader.Config import DAILY_INDEX_HBASE_COLUMNS, MINUTE_INDEX_HBASE_COLUMNS, TICK_INDEX_HBASE_COLUMNS
from HFDataLoader.Config import DAILY_CBOND_HBASE_COLUMNS, MINUTE_CBOND_HBASE_COLUMNS, TICK_CBOND_HBASE_COLUMNS
from HFDataLoader.Config import DAILY_FUND_HBASE_COLUMNS, MINUTE_FUND_HBASE_COLUMNS, TICK_FUND_HBASE_COLUMNS
from HFDataLoader.Config import DAILY_FUTURE_HBASE_COLUMNS, MINUTE_FUTURE_HBASE_COLUMNS, TICK_FUTURE_HBASE_COLUMNS
from HFDataLoader.Config import STOCK_TARGET_DAILY_COLUMNS, STOCK_TARGET_MINUTE_COLUMNS, ALIGN_STOCK_COLUMNS
from HFDataLoader.Config import INDEX_TARGET_DAILY_COLUMNS, INDEX_TARGET_MINUTE_COLUMNS, ALIGN_INDEX_COLUMNS
from HFDataLoader.Config import CBOND_TARGET_DAILY_COLUMNS, CBOND_TARGET_MINUTE_COLUMNS, ALIGN_CBOND_COLUMNS
from HFDataLoader.Config import FUND_TARGET_DAILY_COLUMNS, FUND_TARGET_MINUTE_COLUMNS, ALIGN_FUND_COLUMNS
from HFDataLoader.Config import FUTURE_TARGET_DAILY_COLUMNS, FUTURE_TARGET_MINUTE_COLUMNS, ALIGN_FUTURE_COLUMNS
from HFDataLoader.Config import DAILY_SUFFIX, MINUTE_SUFFIX, TICK_SUFFIX, MOCK_TICK_SUFFIX
from HFDataLoader.Config import USER_ID, CELL_SIZE
from HFDataLoader.DataLoader import DataLoader
from HFDataLoader.HFData import HFData
from HFDataLoader.DataMonitor import DataMonitor
from ExchangeHouse.MockTickData import MockTickData
import Utils.HelpFunc as Util

import os
import datetime as dt
import pandas as pd
import pickle
from xquant.factordata import FactorData
from xquant.xqutils.xqfile import HDFSFile
from xquant.compute.sparkmr import remote_print


class HFDataUpdate(object):
    def __init__(self, 
                 lib_name, 
                 code,
                 start_date, end_date, 
                 daily=False, minute=False, tick=False, ### 更新数据与否
                 mock_tick=False, mock_freq=1,          ### SZ股票还原盘口
                 overwrite=False,                       ### 更新数据时覆盖原有与否，默认增量更新
                 monitor=True,                          ### 数据质量监控
                 hbase=False,                           ### 设置HBASE CELL_SIZE
                 save_file=None,                        ### 数据保存为文件，None, "HDFS", "NFS"
                 save_path=None,                        ### 如果保存，存储文件夹
                 env="Docker"):                         ### 运行环境, "Docker", "Spark"

        self.lib_name = lib_name
        self.code = code
        self.code_type = Util.get_code_type(self.code)
        self.sz_code = False
        if self.code_type == "STOCK":
            self.sz_code = Util.is_sz_code(self.code)

        self.indus_type = None
        if self.code_type == "INDUSTRY":
            self.indus_type = Util.get_industry_type(self.code)

        self.start_date = start_date
        self.end_date = end_date
        self.trading_day_list = Util.get_trading_day(self.start_date, self.end_date)
        assert len(self.trading_day_list) > 0, "no trading days!"
        self.start_date = self.trading_day_list[0]
        self.end_date = self.trading_day_list[-1]

        self.daily = daily
        self.minute = minute
        self.tick = tick
        self.overwrite = overwrite
        self.monitor = monitor

        self.mock_tick = mock_tick
        self.mock_freq = mock_freq
        if not self.sz_code:
            self.mock_tick = False
        if self.sz_code and self.mock_tick:
            if self.mock_freq is None:
                self.mock_freq = 1
        if self.mock_tick:
            self.mtd = MockTickData(self.code, self.mock_freq, self.monitor)

        if self.monitor:
            self.dmr = DataMonitor(self.lib_name, self.code)

        if self.daily or self.minute or self.tick:
            self.dlr = DataLoader(self.code, self.monitor)

        self.fa = FactorData()
        self.hbase = hbase

        self.hfd = HFData(self.lib_name, self.code)

        self.save_file = save_file
        self.save_path = save_path
        self.env = env
        if self.save_file is not None:
            if self.env == "Spark":
                self.save_file = "HDFS"
            if self.save_file == "HDFS":
                self.hf = HDFSFile()

        self.is_executor = "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ

    def run_update(self):
        if self.daily:
            daily_df = self.prepare_daily_data()
            self.update_daily_data(daily_df)
        if self.minute:
            minute_df = self.prepare_minute_data()
            self.update_minute_data(minute_df)
        if self.tick:
            tick_df = self.prepare_tick_data()
            self.update_tick_data(tick_df)
        if self.mock_tick:
            mock_tick_df = self.prepare_mock_tick_data()
            self.update_mock_tick_data(mock_tick_df)

        if self.monitor:
            self.dmr.run_monitor()

#################################################################################################################
    def update_daily_data(self, daily_df):
        # 更改列名与因子库的因子名对应
        if self.code_type == "STOCK":
            daily_df = daily_df.reindex(columns=STOCK_TARGET_DAILY_COLUMNS)
            daily_df.columns = DAILY_STOCK_HBASE_COLUMNS
        elif self.code_type == "INDEX":
            daily_df = daily_df.reindex(columns=INDEX_TARGET_DAILY_COLUMNS)
            daily_df.columns = DAILY_INDEX_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            daily_df = daily_df.reindex(columns=CBOND_TARGET_DAILY_COLUMNS)
            daily_df.columns = DAILY_CBOND_HBASE_COLUMNS
        elif self.code_type == "ETF" or self.code_type == "LOF":
            daily_df = daily_df.reindex(columns=FUND_TARGET_DAILY_COLUMNS)
            daily_df.columns = DAILY_FUND_HBASE_COLUMNS
        elif self.code_type == "FUTURE":
            daily_df = daily_df.reindex(columns=FUTURE_TARGET_DAILY_COLUMNS)
            daily_df.columns = DAILY_FUTURE_HBASE_COLUMNS
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                daily_df = daily_df.reindex(columns=INDEX_TARGET_DAILY_COLUMNS)
                daily_df.columns = DAILY_INDEX_HBASE_COLUMNS
            else:
                raise Exception("Not Supported Daily Data For Industry Type: {}".format(self.indus_type))
        else:
            raise Exception("Not Supported Daily Data For Code Type Yet: {}".format(self.code_type))

        if not daily_df.empty:
            daily_df = daily_df.reset_index(drop=True)
            try:
                self.fa_update_factor_value(self.lib_name, daily_df, "{}_{}".format(self.code, DAILY_SUFFIX), "20200102")
            except:
                if self.save_file is not None:
                    available_date_list = sorted(list(set(daily_df["{}_Date".format(DAILY_SUFFIX)].tolist())))
                    available_date_list = list(map(str, available_date_list))
                    start_date = available_date_list[0]
                    end_date = available_date_list[-1]
                    self.dump_to_file(daily_df, DAILY_SUFFIX ,self.code, start_date, end_date, self.save_file, self.save_path, self.env)
                else:
                    raise Exception("Dump Daily Data HBASE Error But No File Saved")

    def update_minute_data(self, minute_df):
        # 更改列名与因子库的因子名对应
        if self.code_type == "STOCK":
            minute_df = minute_df.reindex(columns=STOCK_TARGET_MINUTE_COLUMNS)
            minute_df.columns = MINUTE_STOCK_HBASE_COLUMNS
        elif self.code_type == "INDEX":
            minute_df = minute_df.reindex(columns=INDEX_TARGET_MINUTE_COLUMNS)
            minute_df.columns = MINUTE_INDEX_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            minute_df = minute_df.reindex(columns=CBOND_TARGET_MINUTE_COLUMNS)
            minute_df.columns = MINUTE_CBOND_HBASE_COLUMNS
        elif self.code_type == "ETF" or self.code_type == "LOF":
            minute_df = minute_df.reindex(columns=FUND_TARGET_MINUTE_COLUMNS)
            minute_df.columns = MINUTE_FUND_HBASE_COLUMNS
        elif self.code_type == "FUTURE":
            minute_df = minute_df.reindex(columns=FUTURE_TARGET_MINUTE_COLUMNS)
            minute_df.columns = MINUTE_FUTURE_HBASE_COLUMNS
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                minute_df = minute_df.reindex(columns=INDEX_TARGET_MINUTE_COLUMNS)
                minute_df.columns = MINUTE_INDEX_HBASE_COLUMNS
            else:
                raise Exception("Not Supported Minute Data For Industry Type: {}".format(self.indus_type))
        else:
            raise Exception("Not Supported Minute Data For Code Type Yet: {}".format(self.code_type))

        if not minute_df.empty:
            minute_df = minute_df.reset_index(drop=True)
            try:
                self.fa_update_factor_value(self.lib_name, minute_df, "{}_{}".format(self.code, MINUTE_SUFFIX), "20200102")
            except:
                if self.save_file is not None:
                    available_date_list = sorted(list(set(minute_df["{}_Date".format(MINUTE_SUFFIX)].tolist())))
                    available_date_list = list(map(str, available_date_list))
                    start_date = available_date_list[0]
                    end_date = available_date_list[-1]
                    self.dump_to_file(minute_df, MINUTE_SUFFIX, self.code, start_date, end_date, self.save_file, self.save_path, self.env)
                else:
                    raise Exception("Dump Minute Data HBASE Error But No File Saved")

    def update_tick_data(self, tick_df):
        # 更改列名与因子库的因子名对应
        if tick_df.empty:
            return None

        if self.code_type == "STOCK":
            tick_df = tick_df.reindex(columns=ALIGN_STOCK_COLUMNS)
            tick_df.columns = TICK_STOCK_HBASE_COLUMNS
        elif self.code_type == "INDEX":
            tick_df = tick_df.reindex(columns=ALIGN_INDEX_COLUMNS)
            tick_df.columns = TICK_INDEX_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            tick_df = tick_df.reindex(columns=ALIGN_CBOND_COLUMNS)
            tick_df.columns = TICK_CBOND_HBASE_COLUMNS
        elif self.code_type == "ETF" or self.code_type == "LOF":
            tick_df = tick_df.reindex(columns=ALIGN_FUND_COLUMNS)
            tick_df.columns = TICK_FUND_HBASE_COLUMNS
        elif self.code_type == "FUTURE":
            tick_df = tick_df.reindex(columns=ALIGN_FUTURE_COLUMNS)
            tick_df.columns = TICK_FUTURE_HBASE_COLUMNS
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                tick_df = tick_df.reindex(columns=ALIGN_INDEX_COLUMNS)
                tick_df.columns = TICK_INDEX_HBASE_COLUMNS
            else:
                Exception("Not Supported Tick Data For Industry Type: {}".format(self.indus_type))
        else:
            raise Exception("Not Supported Tick Data For Code Type Yet: {}".format(self.code_type))

        # 将每一天的Tick频数据写入HBase
        update_day_list = sorted(tick_df["{}_Date".format(TICK_SUFFIX)].drop_duplicates().to_list())
        for update_date in update_day_list:
            sub_tick_df = tick_df[tick_df["{}_Date".format(TICK_SUFFIX)]==update_date]
            if not sub_tick_df.empty:
                try:
                    self.fa_update_factor_value(self.lib_name, sub_tick_df, "{}_{}".format(self.code, TICK_SUFFIX), update_date)
                except:
                    if self.save_file is not None:
                        self.dump_to_file(sub_tick_df, TICK_SUFFIX, self.code, update_date, update_date, self.save_file, self.save_path, self.env)
                    else:
                        raise Exception("Dump Tick Data HBASE Error But No File Saved")

    def update_mock_tick_data(self, mock_tick_df):
        # 更改列名与因子库的因子名对应
        if mock_tick_df.empty:
            return None

        if self.sz_code:
            mock_tick_df = mock_tick_df.reindex(columns=ALIGN_STOCK_COLUMNS)
            mock_tick_df.columns = MOCK_TICK_STOCK_HBASE_COLUMNS
        else:
            raise Exception("Not SZ Stock, Mock Tick Not Supported Yet")
        # 将每一天的Tick频数据写入HBase
        update_day_list = sorted(mock_tick_df["{}_Date".format(MOCK_TICK_SUFFIX)].drop_duplicates().to_list())
        for update_date in update_day_list:
            sub_mock_tick_df = mock_tick_df[mock_tick_df["{0}_Date".format(MOCK_TICK_SUFFIX)]==update_date]
            if not sub_mock_tick_df.empty:
                try:
                    self.fa_update_factor_value(self.lib_name, sub_mock_tick_df, "{}_{}".format(self.code, MOCK_TICK_SUFFIX), update_date)
                except:
                    if self.save_file is not None:
                        self.dump_to_file(sub_mock_tick_df, MOCK_TICK_SUFFIX, self.code, update_date, update_date, self.save_file, self.save_path, self.env)
                    else:
                        raise Exception("Dump Mock Tick Data HBASE Error But No File Saved")

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
            self.my_print("WARN: Writing to HBASE costs {} sec for {} on {}".format(round(time_cost, 2), code, date))

########################################################################################################################
    def prepare_daily_data(self):
        '''准备日频数据'''
        # 读取已存在的日频数据
        try:
            old_daily_df = self.hfd.get_old_daily_data()
            daily_date_list = list(set(old_daily_df["Date"].to_list()))
        except:
            daily_date_list = []
        daily_date_list = list(map(str, daily_date_list))

        if len(daily_date_list) != 0:  # 原有数据库有数据
            ### 覆盖原有数据
            if self.overwrite:
                ### 原有数据不在更新日期范围内的数据
                self.my_print("Start Overwrite {} Daily Data {}-{}".format(self.code, self.start_date,self.end_date))
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
                    self.my_print(" New Update {} Daily Data {}-{} ".format(self.code, new_start_date, new_end_date))
                    new_daily_df, daily_monitor = self.dlr.load_daily_data(new_start_date, new_end_date)
                    # 合并两部分数据
                    sub_old_daily_df = old_daily_df[~old_daily_df["Date"].isin(extra_date_list)]
                    daily_df = sub_old_daily_df.append(new_daily_df)
                    if not daily_df.empty:
                        daily_df = daily_df.sort_values(by=["Date"])
                else:  # 没有需要更新的数据，所有指定日期中数据都可以在原数据中找到
                    daily_df = old_daily_df
                    daily_monitor = {}
        else:  # 原数据库中没有数据，直接计算新数据并更新
            self.my_print("New Update {} Daily Data {}-{}".format(self.code, self.start_date, self.end_date))
            daily_df, daily_monitor = self.dlr.load_daily_data(self.start_date, self.end_date)

        if self.monitor:
            self.dmr.update_daily_monitor(daily_monitor)

        return daily_df

    def prepare_minute_data(self):
        '''准备分钟频数据'''
        ### 读取存量分钟数据
        try:
            old_minute_df = self.hfd.get_old_minute_data()
            minute_date_list = list(set(old_minute_df["Date"].to_list()))
        except:
            minute_date_list = []
        minute_date_list = list(map(str, minute_date_list))

        if len(minute_date_list) != 0:  # 原有数据库有数据
            if self.overwrite:
                ### 原有数据不在更新日期范围内的数据
                self.my_print("Start Overwrite {} Minute Data {}-{}".format(self.code, self.start_date, self.end_date))
                sub_old_minute_df = old_minute_df[~old_minute_df["Date"].isin(self.trading_day_list)]
                new_minute_df, minute_monitor = self.dlr.load_minute_data(self.start_date, self.end_date)
                ###合并两部分数据
                minute_df = sub_old_minute_df.append(new_minute_df)
                if not minute_df.empty:
                    minute_df = minute_df.sort_values(by=["Date","Time"])
            else:
                # 增量更新分钟数据
                extra_date_list = sorted(list(set(self.trading_day_list) - set(minute_date_list)))
                if len(extra_date_list) != 0:  # 要更新的数据，有一些原数据库中没有
                    new_start_date, new_end_date = extra_date_list[0], extra_date_list[-1]
                    # 更新原来没有的数据
                    self.my_print("New Update {} Minute Data {}-{}".format(self.code, new_start_date, new_end_date))
                    new_minute_df, minute_monitor = self.dlr.load_minute_data(new_start_date, new_end_date)
                    # 合并两部分数据
                    sub_old_minute_df = old_minute_df[~old_minute_df["Date"].isin(extra_date_list)]
                    minute_df = sub_old_minute_df.append(new_minute_df)
                    if not minute_df.empty:
                        minute_df = minute_df.sort_values(by=["Date", "Time"])
                else:  # 没有需要更新的数据，所有指定日期中的数据都可以在原数据中找到
                    minute_df = old_minute_df
                    minute_monitor = {}
        else:  # 原数据库中没有数据，直接计算新数据并更新
            self.my_print("New Update {} Minute Data {}-{}".format(self.code, self.start_date, self.end_date))
            minute_df, minute_monitor = self.dlr.load_minute_data(self.start_date, self.end_date)

        if self.monitor:
            self.dmr.update_minute_monitor(minute_monitor)

        return minute_df

    def prepare_tick_data(self):
        '''增量更新Tick频数据'''
        ### 直接覆盖，不考虑存量数据
        if self.overwrite:
            self.my_print("Start Overwrite {} Tick Data {}-{} ".format(self.code, self.start_date, self.end_date))
            tick_df, tick_monitor = self.dlr.load_tick_data(self.start_date, self.end_date)

        ### 读取存量数据，只更新数据库中不存在的数据     
        else:
            # 获取历史数据已经存在的交易日列表
            fake_date_list = self.fa.search_by_stock(self.lib_name, "{}_{}".format(self.code, TICK_SUFFIX),
                                                    self.trading_day_list)
            # 对每个交易日是否有值确认，获得真实已存在交易日列表
            existing_date_list = []
            for existing_date in fake_date_list:
                if self.code_type == "STOCK":
                    tick_num = len(self.fa.search_by_stock_date(self.lib_name, "{}_{}".format(self.code, TICK_SUFFIX),
                                                               existing_date, TICK_STOCK_HBASE_COLUMNS))
                elif self.code_type == "INDEX":
                    tick_num = len(self.fa.search_by_stock_date(self.lib_name, "{}_{}".format(self.code, TICK_SUFFIX),
                                                               existing_date, TICK_INDEX_HBASE_COLUMNS))
                elif self.code_type == "CBOND":
                    tick_num = len(self.fa.search_by_stock_date(self.lib_name, "{}_{}".format(self.code, TICK_SUFFIX),
                                                               existing_date, TICK_CBOND_HBASE_COLUMNS))
                elif self.code_type == "ETF" or self.code_type == "LOF":
                    tick_num = len(self.fa.search_by_stock_date(self.lib_name, "{}_{}".format(self.code, TICK_SUFFIX),
                                                               existing_date, TICK_FUND_HBASE_COLUMNS))
                elif self.code_type == "FUTURE":
                    tick_num = len(self.fa.search_by_stock_date(self.lib_name, "{}_{}".format(self.code, TICK_SUFFIX),
                                                               existing_date, TICK_FUTURE_HBASE_COLUMNS))
                elif self.code_type == "INDUSTRY":
                    if self.indus_type == "SHENWAN":
                        tick_num = len(self.fa.search_by_stock_date(self.lib_name, "{}_{}".format(self.code, TICK_SUFFIX),
                                                         existing_date, TICK_INDEX_HBASE_COLUMNS))
                    else:
                        raise Exception("Not Supported Industry Type Yet: {}".format(self.indus_type))
                else:
                    raise Exception("Not Supported Code Type Yet: {}".format(self.code_type))

                if tick_num != 0:  # 长度不为0的加入列表
                    existing_date_list.append(existing_date)
            # 获取还未更新的交易日列表
            tick_date_list = sorted(list(set(self.trading_day_list) - set(existing_date_list)))
            # 将新数据写入HBase
            if len(tick_date_list) != 0:
                update_start_date, update_end_date = tick_date_list[0], tick_date_list[-1]
                self.my_print("New Update {} Tick Data {}-{}".format(self.code, update_start_date, update_end_date))
                # 计算该股票这一段时间Tick频数据
                tick_df, tick_monitor = self.dlr.load_tick_data(update_start_date, update_end_date)
            else:
                if self.code_type == "STOCK":
                    ALIGN_COLUMNS = ALIGN_STOCK_COLUMNS
                elif self.code_type == "INDEX":
                    ALIGN_COLUMNS = ALIGN_INDEX_COLUMNS
                elif self.code_type == "CBOND":
                    ALIGN_COLUMNS = ALIGN_CBOND_COLUMNS
                elif self.code_type == "ETF" or self.code_type == "LOF":
                    ALIGN_COLUMNS = ALIGN_FUND_COLUMNS
                elif self.code_type == "FUTURE":
                    ALIGN_COLUMNS = ALIGN_FUTURE_COLUMNS
                elif self.code_type == "INDUSTRY":
                    if self.indus_type == "SHENWAN":
                        ALIGN_COLUMNS = ALIGN_INDEX_COLUMNS
                    else:
                        raise Exception("Not Supported Industry Type Yet: {}".format(self.indus_type))
                else:
                    raise Exception("Not Supported Code Type Yet: {}".format(self.code_type))

                tick_df, tick_monitor = pd.DataFrame(columns=ALIGN_COLUMNS), {}

        if self.monitor:
            self.dmr.update_tick_monitor(tick_monitor)

        return tick_df

    def prepare_mock_tick_data(self):
        '''增量更新Tick频数据'''
        ### 直接覆盖，不考虑存量数据
        if self.overwrite:
            self.my_print("Start Overwrite {} Mock Tick Data {}-{} ".format(self.code, self.start_date, self.end_date))
            mock_tick_df, mock_tick_monitor = self.mtd.load_mock_tick_data(self.start_date, self.end_date)

        ### 读取存量数据，只更新数据库中不存在的数据
        else:
            # 获取历史数据已经存在的交易日列表
            if self.sz_code:
                fake_date_list = self.fa.search_by_stock(self.lib_name, "{}_{}".format(self.code, MOCK_TICK_SUFFIX),
                                                    self.trading_day_list)
            else:
                raise Exception("Not SZ Stock, Not Mock Tick Supported Yet")
            # 对每个交易日是否有值确认，获得真实已存在交易日列表
            existing_date_list = []
            for existing_date in fake_date_list:
                tick_num = len(self.fa.search_by_stock_date(self.lib_name, "{}_{}".format(self.code, MOCK_TICK_SUFFIX),
                                                               existing_date, MOCK_TICK_STOCK_HBASE_COLUMNS))
                if tick_num != 0:  # 长度不为0的加入列表
                    existing_date_list.append(existing_date)
            # 获取还未更新的交易日列表
            tick_date_list = sorted(list(set(self.trading_day_list) - set(existing_date_list)))
            # 将新数据写入HBase
            if len(tick_date_list) != 0:
                update_start_date, update_end_date = tick_date_list[0], tick_date_list[-1]
                self.my_print("New Update {} Mock Tick Data {}-{}".format(self.code, update_start_date, update_end_date))
                # 计算该股票这一段时间Tick频数据
                mock_tick_df, mock_tick_monitor = self.mtd.load_mock_tick_data(update_start_date, update_end_date)
            else:
                mock_tick_df, mock_tick_monitor = pd.DataFrame(columns=ALIGN_STOCK_COLUMNS), {}

        if self.monitor:
            self.dmr.update_mock_tick_monitor(mock_tick_monitor)

        return mock_tick_df

    @staticmethod
    def get_save_root_path(user_id, save_file, save_path, env):
        if env == "Docker":
            if save_file=="NFS":
                root = os.path.join('/data/user', user_id, save_path)
            else:
                root = os.path.join("", save_path)
        else:  ### Spark, save_file=="HDFS"
            root = os.path.join(user_id, save_path)
        return root

    def dump_to_file(self, df, freq, code, start_date, end_date, save_file, save_path, env):
        if save_path is None:
            save_path = "HFDataDump"
        root = self.get_save_root_path(USER_ID, save_file, save_path, env)
        path = os.path.join(root, freq)
        file_name = os.path.join(path, "{}_{}_{}.pkl".format(code, start_date, end_date))

        if save_file=="NFS":
            if not os.path.exists(path):
                os.makedirs(path)
            with open(file_name, 'wb') as f:
                pickle.dump(df, f)

        else:  ### "HDFS"
            if not self.hf.exists(path):
                self.hf.mkdir(path)
            with self.hf.open(file_name, 'wb') as f:
                pickle.dump(df, f)

    def my_print(self, x_str):
        if self.is_executor:
            remote_print(x_str)
        else:
            print(x_str)



