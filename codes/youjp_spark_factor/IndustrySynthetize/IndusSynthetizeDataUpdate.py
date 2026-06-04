#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/3/2 17:13
from FactorDataTool.Config import INDUSTRY_TYPE
from HFDataLoader.Config import USER_ID, CELL_SIZE, TICK_SUFFIX, ALIGN_INDEX_COLUMNS, TICK_INDEX_HBASE_COLUMNS
from IndustrySynthetize.IndusSynthetizeData import IndusSynthetizeData

import os
import pickle
import pandas as pd
from xquant.factordata import FactorData
from xquant.xqutils.xqfile import HDFSFile
from xquant.compute.sparkmr import remote_print


class IndusSynthetizeDataUpdate:
    def __init__(self, lib_name, indus_code, start_date, end_date, daily, minute, tick, overwrite,
                       hbase, save_file, save_path, env):
        self.lib_name = lib_name
        self.indus_code = indus_code
        self.indus_type, self.indus = self.indus_code.split(".")
        assert self.indus_type in INDUSTRY_TYPE, "ONLY SUPPORT CITICS OR SW"
        self.start_date = start_date
        self.end_date = end_date

        self.daily = daily
        self.minute = minute
        self.tick = tick
        if self.daily or self.minute or self.tick:
            self.isd = IndusSynthetizeData(self.lib_name, self.indus_code)

        self.overwrite = overwrite

        self.hbase = hbase
        self.save_file = save_file
        self.save_path = save_path
        self.env = env

        if self.save_file is not None:
            if self.env == "Spark":
                self.save_file = "HDFS"
            if self.save_file == "HDFS":
                self.hf = HDFSFile()

        self.fa = FactorData()
        self.trading_day_list = self.fa.tradingday(self.start_date, self.end_date)
        self.start_date = self.trading_day_list[0]
        self.end_date = self.trading_day_list[-1]

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

    def update_daily_data(self, daily_df):
        pass

    def update_minute_data(self, minute_df):
        pass

    def update_tick_data(self, tick_df):
        if tick_df.empty:
            return None

        tick_df = tick_df.reindex(columns=ALIGN_INDEX_COLUMNS)
        tick_df.columns = TICK_INDEX_HBASE_COLUMNS

        update_day_list = sorted(tick_df["{}_Date".format(TICK_SUFFIX)].drop_duplicates().to_list())
        for update_date in update_day_list:
            sub_tick_df = tick_df[tick_df["{}_Date".format(TICK_SUFFIX)] == update_date]
            if not sub_tick_df.empty:
                try:
                    flag = self.fa_update_factor_value(self.lib_name, sub_tick_df,
                                                       "{}_{}".format(self.indus, TICK_SUFFIX), update_date)
                    if not flag:
                        self.my_print("Update Tick Data Fail: {}-{}".format(self.indus, update_date))
                except:
                    if self.save_file is not None:
                        self.dump_to_file(sub_tick_df, TICK_SUFFIX, self.indus, update_date, update_date,
                                          self.save_file, self.save_path, self.env)
                    else:
                        raise Exception("Dump Tick Data HBASE Error But No File Saved")

    def fa_update_factor_value(self, lib_name, df, stock, date):
        if self.hbase:
            return self.fa.update_factor_value(lib_name, df, stock, date, cell_size=CELL_SIZE)
        else:
            return self.fa.update_factor_value(lib_name, df, stock, date)

#######################################################################################################################
    def prepare_daily_data(self):
        pass

    def prepare_minute_data(self):
        pass

    def prepare_tick_data(self):
        '''增量更新Tick频数据'''
        ### 直接覆盖，不考虑存量数据
        if self.overwrite:
            self.my_print("Start Overwrite {} Tick Data {}-{} ".format(self.indus_code, self.start_date, self.end_date))
            tick_df = self.isd.synthetize_industry_tick_data(self.start_date, self.end_date)

        ### 读取存量数据，只更新数据库中不存在的数据
        else:
            # 获取历史数据已经存在的交易日列表
            fake_date_list = self.fa.search_by_stock(self.lib_name, "{}_{}".format(self.indus, TICK_SUFFIX),
                                                    self.trading_day_list)
            # 对每个交易日是否有值确认，获得真实已存在交易日列表
            existing_date_list = []
            for existing_date in fake_date_list:
                tick_num = len(self.fa.search_by_stock_date(self.lib_name, "{}_{}".format(self.indus, TICK_SUFFIX),
                                                               existing_date, TICK_INDEX_HBASE_COLUMNS))
                if tick_num != 0:  # 长度不为0的加入列表
                    existing_date_list.append(existing_date)
            # 获取还未更新的交易日列表
            tick_date_list = sorted(list(set(self.trading_day_list) - set(existing_date_list)))
            # 将新数据写入HBase
            if len(tick_date_list) != 0:
                update_start_date, update_end_date = tick_date_list[0], tick_date_list[-1]
                self.my_print("New Update {} Tick Data {}-{}".format(self.indus_code, update_start_date, update_end_date))
                # 计算该股票这一段时间Tick频数据
                tick_df = self.isd.synthetize_industry_tick_data(update_start_date, update_end_date)
            else:
                tick_df = pd.DataFrame(columns=ALIGN_INDEX_COLUMNS)

        return tick_df

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

    def dump_to_file(self, df, freq, stock, start_date, end_date, save_file, save_path, env):
        if save_path is None:
            save_path = "HFDataDump"
        root = self.get_save_root_path(USER_ID, save_file, save_path, env)
        path = os.path.join(root, freq)
        file_name = os.path.join(path, "{}_{}_{}.pkl".format(stock, start_date, end_date))

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