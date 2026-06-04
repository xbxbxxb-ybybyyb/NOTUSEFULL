from DataInterface.Config import DAILY_STOCK_HBASE_COLUMNS, MINUTE_STOCK_HBASE_COLUMNS, TICK_STOCK_HBASE_COLUMNS, TRANSACTION_STOCK_HBASE_COLUMNS, ORDER_STOCK_HBASE_COLUMNS
from DataInterface.Config import DAILY_INDEX_HBASE_COLUMNS, MINUTE_INDEX_HBASE_COLUMNS, TICK_INDEX_HBASE_COLUMNS
from DataInterface.Config import DAILY_CBOND_HBASE_COLUMNS, MINUTE_CBOND_HBASE_COLUMNS, TICK_CBOND_HBASE_COLUMNS, TRANSACTION_CBOND_HBASE_COLUMNS, ORDER_CBOND_HBASE_COLUMNS
from DataInterface.Config import DAILY_FUND_HBASE_COLUMNS, MINUTE_FUND_HBASE_COLUMNS, TICK_FUND_HBASE_COLUMNS, TRANSACTION_FUND_HBASE_COLUMNS, ORDER_FUND_HBASE_COLUMNS
from DataInterface.Config import DAILY_SUFFIX, MINUTE_SUFFIX, TICK_SUFFIX, TRANSACTION_SUFFIX, ORDER_SUFFIX
from DataInterface.Config import DAILY_FUTURE_HBASE_COLUMNS, MINUTE_FUTURE_HBASE_COLUMNS, TICK_FUTURE_HBASE_COLUMNS
from IndexNonFactor.Config import INF_PREFIX, INF_NONFACTOR_COLUMNS
from Constants.INDEX_LIST import INDEX_LIST
from FactorDataTool.Config import SW_I_CODE, SW_II_CODE, CITICS_I_CODE, CITICS_II_CODE

import os
import gc
import datetime as dt
import numpy as np
import pandas as pd
from Utils.HelpFunc import get_code_type, get_industry_type, get_trading_day
from xquant.factordata import FactorData
from xquant.compute.sparkmr import remote_print


class HFData(object):
    def __init__(self, library, code, tickLibrary=None, tranOrderLibrary=None, inf_library=None, use_l2p=False, cbond=None, verbose=True):
        self.library = library
        self.code = code
        self.tickLibrary = tickLibrary if tickLibrary is not None else self.library
        self.tranOrderLibrary = tranOrderLibrary if tranOrderLibrary is not None else self.library
        self.inf_library = inf_library
        self.use_l2p = use_l2p
        self.cbond = cbond
        self.verbose = verbose
        self.code_type = get_code_type(self.code)

        self.indus_type = get_industry_type(self.code) if self.code_type == "INDUSTRY" else None

        self.fa = FactorData()

        self.is_executor = "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ

    def get_daily_data(self, start_date, end_date):
        """获取HBase中某个股票、指数、可转债、基金或期货一段时间的日频数据"""
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
        """获取HBase中某个股票、指数、可转债、基金或期货一段时间的分钟频数据"""
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
        """获取HBase中股票、指数、可转债、基金或期货一段时间的Tick数据"""
        trading_day_list = get_trading_day(start_date, end_date)
        sub_tick_list = []
        for trading_day in trading_day_list:
            sub_tick_df = self.get_old_tick_data(trading_day, map_col=True)
            sub_tick_list.append(sub_tick_df)
        tick_df = pd.concat(sub_tick_list, axis=0)
        del sub_tick_list
        gc.collect()
        return tick_df

    def get_transaction_data(self, start_date, end_date):
        """获取HBase中股票、可转债、基金一段时间的Transaction数据"""
        trading_day_list = get_trading_day(start_date, end_date)
        sub_transaction_list = []
        for trading_day in trading_day_list:
            sub_transaction_df = self.get_old_transaction_data(trading_day, map_col=True)
            sub_transaction_list.append(sub_transaction_df)
        transaction_df = pd.concat(sub_transaction_list, axis=0)
        del sub_transaction_list
        gc.collect()
        return transaction_df

    def get_order_data(self, start_date, end_date):
        """获取HBase中股票、可转债、基金一段时间的Order数据"""
        trading_day_list = get_trading_day(start_date, end_date)
        sub_order_list = []
        for trading_day in trading_day_list:
            sub_order_df = self.get_old_order_data(trading_day, map_col=True)
            sub_order_list.append(sub_order_df)
        order_df = pd.concat(sub_order_list, axis=0)
        del sub_order_list
        gc.collect()
        return order_df

    def get_inf_tick_data(self, start_date, end_date, column_names=[]):
        """获取HBase中合成的中间因子一段时间的Tick数据"""
        trading_day_list = get_trading_day(start_date, end_date)
        sub_tick_list = []
        for trading_day in trading_day_list:
            sub_tick_df = self.get_old_inf_tick_data(trading_day, column_names, map_col=True)
            sub_tick_list.append(sub_tick_df)
        tick_df = pd.concat(sub_tick_list, axis=0)
        del sub_tick_list
        gc.collect()
        return tick_df

    def get_old_daily_data_clean(self):
        """获取HBase中某个股票、指数、可转债、基金或期货的历史日频数据"""
        if self.code_type == "STOCK":
            HBASE_COLUMNS = DAILY_STOCK_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            HBASE_COLUMNS = DAILY_CBOND_HBASE_COLUMNS
        elif self.code_type in ["ETF", "LOF"]:
            HBASE_COLUMNS = DAILY_FUND_HBASE_COLUMNS
        elif self.code_type == "FUTURE":
            HBASE_COLUMNS = DAILY_FUTURE_HBASE_COLUMNS
        elif self.code_type == "INDEX":
            HBASE_COLUMNS = DAILY_INDEX_HBASE_COLUMNS
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                HBASE_COLUMNS = DAILY_INDEX_HBASE_COLUMNS
            else:
                raise Exception(" Not Supported Daily Data For Industry Type: {} ".format(self.indus_type))
        else:
            raise Exception(" Not Supported Daily Data For Code Type: {} ".format(self.code_type))

        startTime = dt.datetime.now()
        try:
            df = self.fa.get_factor_value(self.library, self.code, "20200102", HBASE_COLUMNS)
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print(" WARN: Reading daily data from HBASE costs {} sec for {} ".format(round(timeCost, 2), self.code))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print(" WARN: Reading daily data from HBASE costs {} sec for {} ".format(round(timeCost, 2), self.code))

            df = pd.DataFrame(columns=HBASE_COLUMNS)

        df.columns = list(map(lambda x: x.replace("{0}_".format(DAILY_SUFFIX), ""), df.columns.to_list()))
        if self.code_type in ["STOCK", "ETF", "LOF", "FUTURE"]:
            df["TradeStatus"] = ((~df["TradeStatus"].isnull())
                                  & (df["TradeStatus"] != "待核查")
                                  & (df["TradeStatus"] != "停牌")
                                  & (df["Volume"] != 0))

        elif self.code_type == "CBOND":
            df["TradeStatus"] = ((~df["TradeStatus"].isnull())
                                  & (df["TradeStatus"] != "待核查")
                                  & (df["TradeStatus"] != "停牌")
                                  & (df["TradeStatus"] != "0")
                                  & (df["Volume"] != 0))

        if not df.empty:
            df.index = df["Date"].astype(np.int64)

        return df

    def get_old_daily_data(self):
        """获取HBase中某个股票、指数、可转债、基金或期货的历史日频数据"""
        if self.code_type == "STOCK":
            HBASE_COLUMNS = DAILY_STOCK_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            HBASE_COLUMNS = DAILY_CBOND_HBASE_COLUMNS
        elif self.code_type in ["ETF", "LOF"]:
            HBASE_COLUMNS = DAILY_FUND_HBASE_COLUMNS
        elif self.code_type == "FUTURE":
            HBASE_COLUMNS = DAILY_FUTURE_HBASE_COLUMNS
        elif self.code_type == "INDEX":
            HBASE_COLUMNS = DAILY_INDEX_HBASE_COLUMNS
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                HBASE_COLUMNS = DAILY_INDEX_HBASE_COLUMNS
            else:
                raise Exception(" Not Supported Daily Data For Industry Type: {} ".format(self.indus_type))
        else:
            raise Exception(" Not Supported Daily Data For Code Type: {} ".format(self.code_type))

        startTime = dt.datetime.now()
        try:
            df = self.fa.get_factor_value(self.library, self.code, "20200102", HBASE_COLUMNS)
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and  timeCost >= 1:
                self.my_print(" WARN: Reading daily data from HBASE costs {} sec for {} ".format(round(timeCost, 2), self.code))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print(" WARN: Reading daily data from HBASE costs {} sec for {} ".format(round(timeCost, 2), self.code))

            df = pd.DataFrame(columns=HBASE_COLUMNS)

        df.columns = list(map(lambda x: x.replace("{0}_".format(DAILY_SUFFIX), ""), df.columns.to_list()))
        if not df.empty:
            df.index = df["Date"].astype(np.int64)

        return df

    def get_old_minute_data(self):
        """获取HBase中某个股票、指数、可转债、基金或期货的历史分钟频数据"""
        if self.code_type == "STOCK":
            HBASE_COLUMNS = MINUTE_STOCK_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            HBASE_COLUMNS = MINUTE_CBOND_HBASE_COLUMNS
        elif self.code_type in ["ETF", "LOF"]:
            HBASE_COLUMNS = MINUTE_FUND_HBASE_COLUMNS
        elif self.code_type == "FUTURE":
            HBASE_COLUMNS = MINUTE_FUTURE_HBASE_COLUMNS
        elif self.code_type == "INDEX":
            HBASE_COLUMNS = MINUTE_INDEX_HBASE_COLUMNS
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                HBASE_COLUMNS = MINUTE_INDEX_HBASE_COLUMNS
            else:
                raise Exception(" Not Supported Minute Data For Industry Type: {} ".format(self.indus_type))
        else:
            raise Exception(" Not Supported Minute Data For Code Type: {} ".format(self.code_type))

        startTime = dt.datetime.now()
        try:
            df = self.fa.get_factor_value(self.library, self.code, "20200102", HBASE_COLUMNS)
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 5:
                self.my_print(" WARN: Reading minute data from HBASE costs {} sec for {} ".format(round(timeCost, 2), self.code))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 5:
                self.my_print(" WARN: Reading minute data from HBASE costs {} sec for {} ".format(round(timeCost, 2), self.code))

            df = pd.DataFrame(columns=HBASE_COLUMNS)

        df.columns = list(map(lambda x: x.replace("{0}_".format(MINUTE_SUFFIX), ""), df.columns.to_list()))
        if not df.empty:
            df.index = df["Date"].astype(np.int64)

        return df

    def get_old_tick_data(self, date, map_col=True):
        """获取HBase中某个股票、指数、可转债、基金或期货的历史某交易日的Tick频数据"""
        if self.code_type == "STOCK":
            HBASE_COLUMNS = TICK_STOCK_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            HBASE_COLUMNS = TICK_CBOND_HBASE_COLUMNS
        elif self.code_type in ["ETF", "LOF"]:
            HBASE_COLUMNS = TICK_FUND_HBASE_COLUMNS
        elif self.code_type == "FUTURE":
            HBASE_COLUMNS = TICK_FUTURE_HBASE_COLUMNS
        elif self.code_type == "INDEX":
            HBASE_COLUMNS = TICK_INDEX_HBASE_COLUMNS
        elif self.code_type == "INDUSTRY":
            HBASE_COLUMNS = TICK_INDEX_HBASE_COLUMNS
        else:
            raise Exception(" Not Supported Tick Data For Code Type : {} ".format(self.code_type))

        startTime = dt.datetime.now()
        try:
            df = self.fa.get_factor_value(self.tickLibrary, self.code, date, HBASE_COLUMNS)
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print(" WARN: Reading tick data from HBASE costs {} sec for {} on {} ".format(round(timeCost, 2), self.code, date))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print(" WARN: Reading tick data from HBASE costs {} sec for {} on {} ".format(round(timeCost, 2), self.code, date))

            df = pd.DataFrame(columns=HBASE_COLUMNS)

        if map_col:
            df.columns = list(map(lambda x: x.replace("{0}_".format(TICK_SUFFIX), ""), df.columns.to_list()))
        if not df.empty:
            df.index = df["Date"].astype(np.int64)

        return df

    def get_old_transaction_data(self, date, map_col=True):
        """获取HBase中某个股票、可转债、基金的历史某交易日的Transaction频数据"""
        if self.code_type == "STOCK":
            HBASE_COLUMNS = TRANSACTION_STOCK_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            HBASE_COLUMNS = TRANSACTION_CBOND_HBASE_COLUMNS
        elif self.code_type in ["ETF", "LOF"]:
            HBASE_COLUMNS = TRANSACTION_FUND_HBASE_COLUMNS
        else:
            raise Exception(" Not Supported Transaction Data For Code Type : {} ".format(self.code_type))

        startTime = dt.datetime.now()
        try:
            df = self.fa.get_factor_value(self.tranOrderLibrary, self.code, date, HBASE_COLUMNS)
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print(" WARN: Reading transaction data from HBASE costs {} sec for {} on {} ".format(round(timeCost, 2), self.code, date))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print(" WARN: Reading transaction data from HBASE costs {} sec for {} on {} ".format(round(timeCost, 2), self.code, date))

            df = pd.DataFrame(columns=HBASE_COLUMNS)

        if map_col:
            df.columns = list(map(lambda x: x.replace("{0}_".format(TRANSACTION_SUFFIX), ""), df.columns.to_list()))

        if not df.empty:
            df.index = df["Date"].astype(np.int64)

        return df

    def get_old_order_data(self, date, map_col=True):
        """获取HBase中某个股票、可转债、基金的历史某交易日的Transaction频数据"""
        if self.code.endswith(".SZ"):
            if self.code_type == "STOCK":
                HBASE_COLUMNS = ORDER_STOCK_HBASE_COLUMNS
            elif self.code_type == "CBOND":
                HBASE_COLUMNS = ORDER_CBOND_HBASE_COLUMNS
            elif self.code_type in ["ETF", "LOF"]:
                HBASE_COLUMNS = ORDER_FUND_HBASE_COLUMNS
            else:
                raise Exception(" Not Supported Order Data For Code Type : {} ".format(self.code_type))
        else:
            raise Exception(" Not Supported Order Data For Code Type : {} ".format(self.code_type))

        startTime = dt.datetime.now()
        try:
            df = self.fa.get_factor_value(self.tranOrderLibrary, self.code, date, HBASE_COLUMNS)
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print(" WARN: Reading order data from HBASE costs {} sec for {} on {} ".format(round(timeCost, 2), self.code, date))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print(" WARN: Reading order data from HBASE costs {} sec for {} on {} ".format(round(timeCost, 2), self.code, date))

            df = pd.DataFrame(columns=HBASE_COLUMNS)

        if map_col:
            df.columns = list(map(lambda x: x.replace("{0}_".format(ORDER_SUFFIX), ""), df.columns.to_list()))

        if not df.empty:
            df.index = df["Date"].astype(np.int64)

        return df

    def get_old_inf_tick_data(self, date, column_names, map_col=True):
        """获取HBase中合成大盘/行业指数某交易日的Tick频数据, column_names为查询列名列表，默认为空List时取所有列名"""

        assert self.code in INDEX_LIST + SW_I_CODE + SW_II_CODE + CITICS_I_CODE + CITICS_II_CODE, " ONLY SUPPORT INDEX OR INDUSTRY "

        if self.inf_library is None:
            self.my_print(" WARN: USE DEFAULT INFactor LIBRARY ")
            self.inf_library = "INFactor"

        if len(column_names) == 0:
            column_names = INF_NONFACTOR_COLUMNS
        extraColumns = list(set(column_names).difference(INF_NONFACTOR_COLUMNS))
        assert len(set(extraColumns).difference(["Date", "Time", "Timestamp", "IsMock", "Symbols"])) == 0, " EXTRA INF COLUMNS NOT EXIST: {}".format(extraColumns)
        validColumns = [col for col in column_names if col in INF_NONFACTOR_COLUMNS]

        HBASE_COLUMNS = ["timestamp", "symbols"] + ["{0}{1}".format(INF_PREFIX, col) for col in validColumns]
        INF_RENAME_COLUMNS = ["{0}{1}".format(INF_PREFIX, col) for col in ["Timestamp", "Symbols"] + validColumns]
        INF_FULL_COLUMNS = ["Code", "Timestamp", "Date", "Time", "Symbols"] + validColumns + ["IsMock"]
        INF_FULL_HBASE_COLUMNS = ["{0}{1}".format(INF_PREFIX, col) for col in INF_FULL_COLUMNS]

        startTime = dt.datetime.now()
        try:
            df = self.fa.get_factor_value(self.inf_library, self.code, date, HBASE_COLUMNS)
            df = df.reindex(columns=HBASE_COLUMNS)
            df.columns = INF_RENAME_COLUMNS
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print(" WARN: Reading tick data from HBASE costs {} sec for {} on {} ".format(round(timeCost, 2), self.code, date))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.my_print(" WARN: Reading tick data from HBASE costs {} sec for {} on {} ".format(round(timeCost, 2), self.code, date))

            df = pd.DataFrame(columns=INF_FULL_HBASE_COLUMNS)

        if map_col:
            df.columns = list(map(lambda x: x.replace("{}".format(INF_PREFIX), ""), df.columns.to_list()))

        if not df.empty:
            df["Code"] = self.code
            df["Date"] = df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(x).strftime("%Y%m%d"))
            df["Time"] = df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(x).strftime("%Y%m%d %H%M%S%f").split(" ")[1][:-3])
            df["IsMock"] = 0
            df.index = df["Date"].astype(np.int64)
            df = df.reindex(columns=INF_FULL_COLUMNS)

        return df

    def get_l2p_tick_time_dict(self, date):
        """ 加载Level2Plus Tick与该Tick对应最后一笔逐笔时间映射关系
        :param date:
        :param cbond: 如果取正股Level2Plus Tick时间映射， 需要传入对应转债代码
        :return: {tick time: real tick time}
        """
        HBASE_COLUMNS = ["{}_{}".format(TICK_SUFFIX, x) for x in ["Timestamp", "RealTimestamp"]]
        if self.code_type == "CBOND":
            code_save = "{0}_{1}".format(self.code, TICK_SUFFIX)
        elif self.code_type == "STOCK":
            code_save = "{}{}".format(self.code[:6], self.cbond[:6])
        else:
            raise Exception(" Level2Plus Tick Timestamp Mapping Only Support CBond & Its Stock in SZ")

        try:
            time_df = self.fa.get_factor_value(self.tickLibrary, code_save, date, HBASE_COLUMNS)
        except:
            time_df = pd.DataFrame(columns=HBASE_COLUMNS)
        time_df.columns = list(map(lambda x: x.replace("{0}_".format(TICK_SUFFIX), ""), time_df.columns.to_list()))

        tick_timestamp_dict = dict()
        if not time_df.empty:
            tick_timestamp_dict = time_df.set_index("Timestamp")["RealTimestamp"].to_dict()

        return tick_timestamp_dict

    def my_print(self, x_str):
        return remote_print(x_str) if self.is_executor else print(x_str)



