from HFDataLoader.Config import DAILY_STOCK_HBASE_COLUMNS, MINUTE_STOCK_HBASE_COLUMNS, TICK_STOCK_HBASE_COLUMNS
from HFDataLoader.Config import MOCK_TICK_STOCK_HBASE_COLUMNS
from HFDataLoader.Config import DAILY_INDEX_HBASE_COLUMNS, MINUTE_INDEX_HBASE_COLUMNS, TICK_INDEX_HBASE_COLUMNS
from HFDataLoader.Config import DAILY_CBOND_HBASE_COLUMNS, MINUTE_CBOND_HBASE_COLUMNS, TICK_CBOND_HBASE_COLUMNS
from HFDataLoader.Config import DAILY_FUND_HBASE_COLUMNS, MINUTE_FUND_HBASE_COLUMNS, TICK_FUND_HBASE_COLUMNS
from HFDataLoader.Config import DAILY_SUFFIX, MINUTE_SUFFIX, TICK_SUFFIX, MOCK_TICK_SUFFIX
from HFDataLoader.Config import DAILY_FUTURE_HBASE_COLUMNS, MINUTE_FUTURE_HBASE_COLUMNS, TICK_FUTURE_HBASE_COLUMNS

import os
import gc
import datetime as dt
import numpy as np
import pandas as pd
import Utils.HelpFunc as Util
from xquant.factordata import FactorData
from xquant.compute.sparkmr import remote_print


class HFData(object):
    def __init__(self, lib_name, code, verbose=True):
        self.lib_name = lib_name
        self.code = code
        self.code_type = Util.get_code_type(self.code)
        self.sz_code = False
        if self.code_type == "STOCK":
            self.sz_code = Util.is_sz_code(self.code)

        self.indus_type = None
        if self.code_type == "INDUSTRY":
            self.indus_type = Util.get_industry_type(self.code)

        self.verbose = verbose

        self.fa = FactorData()

        self.__isExecutor = "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ

    def get_daily_data(self, start_date, end_date):
        '''获取HBase中某个股票、指数、可转债、基金或期货一段时间的日频数据'''
        daily_df = self.get_old_daily_data_clean()
        if not isinstance(start_date, str):
            start_date = str(start_date)
        if not isinstance(end_date, str):
            end_date = str(end_date)
        sub_daily_df = daily_df.loc[start_date:end_date]
        del daily_df
        gc.collect()
        return sub_daily_df

    def get_minute_data(self, start_date, end_date):
        '''获取HBase中某个股票、指数、可转债、基金或期货一段时间的分钟频数据'''
        minute_df = self.get_old_minute_data()
        if not isinstance(start_date, str):
            start_date = str(start_date)
        if not isinstance(end_date, str):
            end_date = str(end_date)
        sub_minute_df = minute_df.loc[start_date:end_date]
        del minute_df
        gc.collect()
        return sub_minute_df

    def get_tick_data(self, start_date, end_date):
        '''获取HBase中股票、指数、可转债、基金或期货一段时间的Tick数据'''
        trading_day_list = Util.get_trading_day(start_date, end_date)
        sub_tick_list = []
        for trading_day in trading_day_list:
            sub_tick_df = self.get_old_tick_data(trading_day, map_col=True)
            sub_tick_list.append(sub_tick_df)
        tick_df = pd.concat(sub_tick_list, axis=0)
        del sub_tick_list
        gc.collect()
        return tick_df

    def get_mock_tick_data(self, start_date, end_date):
        '''获取HBase中股票、指数、可转债、基金或期货一段时间的Mock Tick数据'''
        trading_day_list = Util.get_trading_day(start_date, end_date)
        sub_tick_list = []
        for trading_day in trading_day_list:
            sub_tick_df = self.get_old_mock_tick_data(trading_day, map_col=True)
            sub_tick_list.append(sub_tick_df)
        tick_df = pd.concat(sub_tick_list, axis=0)
        ### release the cache
        del sub_tick_list
        gc.collect()
        return tick_df

    def get_old_daily_data_clean(self):
        '''获取HBase中某个股票、指数、可转债、基金或期货的历史日频数据'''
        if self.code_type == "STOCK":
            HBASE_COLUMNS = DAILY_STOCK_HBASE_COLUMNS
        elif self.code_type == "INDEX":
            HBASE_COLUMNS = DAILY_INDEX_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            HBASE_COLUMNS = DAILY_CBOND_HBASE_COLUMNS
        elif self.code_type == "ETF" or self.code_type == "LOF":
            HBASE_COLUMNS = DAILY_FUND_HBASE_COLUMNS
        elif self.code_type == "FUTURE":
            HBASE_COLUMNS = DAILY_FUTURE_HBASE_COLUMNS
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                HBASE_COLUMNS = DAILY_INDEX_HBASE_COLUMNS
            else:
                raise Exception("Not Supported Daily Data For Industry Type: {}".format(self.indus_type))
        else:
            raise Exception("Not Supported Daily Data For Code Type: {}".format(self.code_type))

        startTime = dt.datetime.now()
        try:
            daily_df = self.fa.get_factor_value(self.lib_name, "{0}_{1}".format(self.code, DAILY_SUFFIX), "20200102",
                                                HBASE_COLUMNS)
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print("WARN: Reading daily data from HBASE costs {} sec for {}"
                                 .format(round(timeCost, 2), self.code))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print("WARN: Reading daily data from HBASE costs {} sec for {}"
                                 .format(round(timeCost, 2), self.code))

            daily_df = pd.DataFrame(columns=HBASE_COLUMNS)

        daily_df.columns = list(map(lambda x: x.replace("{0}_".format(DAILY_SUFFIX), ""), daily_df.columns.to_list()))
        if self.code_type in ["STOCK", "ETF", "LOF", "FUTURE"]:
            daily_df["TradeStatus"] = ((~daily_df["TradeStatus"].isnull())
                                       & (daily_df["TradeStatus"] != "待核查")
                                       & (daily_df["TradeStatus"] != "停牌"))

        elif self.code_type == "CBOND":
            daily_df["TradeStatus"] = ((~daily_df["TradeStatus"].isnull())
                                       & (daily_df["TradeStatus"] != "待核查")
                                       & (daily_df["TradeStatus"] != "停牌")
                                       & (daily_df["TradeStatus"] != "0"))

        if not daily_df.empty:
            daily_df.index = daily_df['Date'].astype(np.int64)
        return daily_df

    def get_old_daily_data(self):
        '''获取HBase中某个股票、指数、可转债、基金或期货的历史日频数据'''
        if self.code_type == "STOCK":
            HBASE_COLUMNS = DAILY_STOCK_HBASE_COLUMNS
        elif self.code_type == "INDEX":
            HBASE_COLUMNS = DAILY_INDEX_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            HBASE_COLUMNS = DAILY_CBOND_HBASE_COLUMNS
        elif self.code_type == "ETF" or self.code_type == "LOF":
            HBASE_COLUMNS = DAILY_FUND_HBASE_COLUMNS
        elif self.code_type == "FUTURE":
            HBASE_COLUMNS = DAILY_FUTURE_HBASE_COLUMNS
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                HBASE_COLUMNS = DAILY_INDEX_HBASE_COLUMNS
            else:
                raise Exception("Not Supported Daily Data For Industry Type: {}".format(self.indus_type))
        else:
            raise Exception("Not Supported Daily Data For Code Type: {}".format(self.code_type))

        startTime = dt.datetime.now()
        try:
            daily_df = self.fa.get_factor_value(self.lib_name, "{0}_{1}".format(self.code, DAILY_SUFFIX), "20200102",
                                                HBASE_COLUMNS)
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and  timeCost >= 1:
                if self.__isExecutor:
                    remote_print("WARN: Reading daily data from HBASE costs {} sec for {}"
                                 .format(round(timeCost, 2), self.code))
                else:
                    print("WARN: Reading daily data from HBASE costs {} sec for {}"
                          .format(round(timeCost, 2), self.code))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print("WARN: Reading daily data from HBASE costs {} sec for {}"
                                 .format(round(timeCost, 2), self.code))

            daily_df = pd.DataFrame(columns=HBASE_COLUMNS)

        daily_df.columns = list(map(lambda x: x.replace("{0}_".format(DAILY_SUFFIX), ""), daily_df.columns.to_list()))
        if not daily_df.empty:
            daily_df.index = daily_df['Date'].astype(np.int64)
        return daily_df

    def get_old_minute_data(self):
        '''获取HBase中某个股票、指数、可转债、基金或期货的历史分钟频数据'''
        if self.code_type == "STOCK":
            HBASE_COLUMNS = MINUTE_STOCK_HBASE_COLUMNS
        elif self.code_type == "INDEX":
            HBASE_COLUMNS = MINUTE_INDEX_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            HBASE_COLUMNS = MINUTE_CBOND_HBASE_COLUMNS
        elif self.code_type == "ETF" or self.code_type == "LOF":
            HBASE_COLUMNS = MINUTE_FUND_HBASE_COLUMNS
        elif self.code_type == "FUTURE":
            HBASE_COLUMNS = MINUTE_FUTURE_HBASE_COLUMNS
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                HBASE_COLUMNS = MINUTE_INDEX_HBASE_COLUMNS
            else:
                raise Exception("Not Supported Minute Data For Industry Type: {}".format(self.indus_type))
        else:
            raise Exception("Not Supported Minute Data For Code Type: {}".format(self.code_type))

        startTime = dt.datetime.now()
        try:
            minute_df = self.fa.get_factor_value(self.lib_name, "{0}_{1}".format(self.code, MINUTE_SUFFIX), "20200102",
                                                 HBASE_COLUMNS)
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 5:
                self.my_print("WARN: Reading minute data from HBASE costs {} sec for {}"
                                 .format(round(timeCost, 2), self.code))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 5:
                self.my_print("WARN: Reading minute data from HBASE costs {} sec for {}"
                                 .format(round(timeCost, 2), self.code))

            minute_df = pd.DataFrame(columns=HBASE_COLUMNS)

        minute_df.columns = list(
            map(lambda x: x.replace("{0}_".format(MINUTE_SUFFIX), ""), minute_df.columns.to_list()))
        if not minute_df.empty:
            minute_df.index = minute_df['Date'].astype(np.int64)
        return minute_df

    def get_old_tick_data(self, mddate, map_col=True):
        '''获取HBase中某个股票、指数、可转债、基金或期货的历史某交易日的Tick频数据'''
        if self.code_type == "STOCK":
            HBASE_COLUMNS = TICK_STOCK_HBASE_COLUMNS
        elif self.code_type == "INDEX":
            HBASE_COLUMNS = TICK_INDEX_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            HBASE_COLUMNS = TICK_CBOND_HBASE_COLUMNS
        elif self.code_type == "ETF" or self.code_type == "LOF":
            HBASE_COLUMNS = TICK_FUND_HBASE_COLUMNS
        elif self.code_type == "FUTURE":
            HBASE_COLUMNS = TICK_FUTURE_HBASE_COLUMNS
        elif self.code_type == "INDUSTRY":
            HBASE_COLUMNS = TICK_INDEX_HBASE_COLUMNS
        else:
            raise Exception("Not Supported Tick Data For Code Type : {}".format(self.code_type))

        startTime = dt.datetime.now()
        try:
            tick_df = self.fa.get_factor_value(self.lib_name, "{0}_{1}".format(self.code, TICK_SUFFIX), mddate,
                                               HBASE_COLUMNS)
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print("WARN: Reading tick data from HBASE costs {} sec for {} on {}"
                                 .format(round(timeCost, 2), self.code, mddate))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print("WARN: Reading tick data from HBASE costs {} sec for {} on {}"
                                 .format(round(timeCost, 2), self.code, mddate))

            tick_df = pd.DataFrame(columns=HBASE_COLUMNS)

        if map_col:
            tick_df.columns = list(map(lambda x: x.replace("{0}_".format(TICK_SUFFIX), ""), tick_df.columns.to_list()))
        if not tick_df.empty:
            tick_df.index = tick_df['Date'].astype(np.int64)
        return tick_df

    def get_old_mock_tick_data(self, mddate, map_col=True):
        '''获取HBase中深交所股票某个交易日盘口还原Tick频数据'''
        if self.sz_code:
            HBASE_COLUMNS = MOCK_TICK_STOCK_HBASE_COLUMNS
        else:
            raise Exception("Not SZ Stock, Mock Tick Not Supported Yet")

        startTime = dt.datetime.now()
        try:
            mock_tick_df = self.fa.get_factor_value(self.lib_name, "{0}_{1}".format(self.code, MOCK_TICK_SUFFIX),
                                                    mddate, HBASE_COLUMNS)
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print("WARN: Reading mock tick data from HBASE costs {} sec for {} on {}"
                                 .format(round(timeCost, 2), self.code, mddate))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print("WARN: Reading mock tick data from HBASE costs {} sec for {} on {}"
                                 .format(round(timeCost, 2), self.code, mddate))

            mock_tick_df = pd.DataFrame(columns=HBASE_COLUMNS)

        if map_col:
            mock_tick_df.columns = list(
                map(lambda x: x.replace("{0}_".format(MOCK_TICK_SUFFIX), ""), mock_tick_df.columns.to_list()))
        if not mock_tick_df.empty:
            mock_tick_df.index = mock_tick_df['Date'].astype(np.int64)
        return mock_tick_df

    def my_print(self, x_str):
        if self.__isExecutor:
            remote_print(x_str)
        else:
            print(x_str)
