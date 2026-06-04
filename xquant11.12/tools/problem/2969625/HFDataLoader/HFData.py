import os
import gc
import datetime as dt
import numpy as np
import pandas as pd
from xquant.factordata import FactorData
from xquant.compute.sparkmr import remote_print
from CommonUtils.HelpFunc import get_code_type, get_industry_type, get_trading_day, generate_timestamp, get_start_end_not_fill_tick
from HFDataLoader.Config import DAILY_STOCK_HBASE_COLUMNS, MINUTE_STOCK_HBASE_COLUMNS, TICK_STOCK_HBASE_COLUMNS, TRANSACTION_STOCK_HBASE_COLUMNS, ORDER_STOCK_HBASE_COLUMNS
from HFDataLoader.Config import DAILY_INDEX_HBASE_COLUMNS, MINUTE_INDEX_HBASE_COLUMNS, TICK_INDEX_HBASE_COLUMNS
from HFDataLoader.Config import DAILY_CBOND_HBASE_COLUMNS, MINUTE_CBOND_HBASE_COLUMNS, TICK_CBOND_HBASE_COLUMNS, TRANSACTION_CBOND_HBASE_COLUMNS, ORDER_CBOND_HBASE_COLUMNS
from HFDataLoader.Config import DAILY_FUND_HBASE_COLUMNS, MINUTE_FUND_HBASE_COLUMNS, TICK_FUND_HBASE_COLUMNS, TRANSACTION_FUND_HBASE_COLUMNS, ORDER_FUND_HBASE_COLUMNS
from HFDataLoader.Config import DAILY_SUFFIX, MINUTE_SUFFIX, TICK_SUFFIX, TRANSACTION_SUFFIX, ORDER_SUFFIX
from HFDataLoader.Config import DAILY_FUTURE_HBASE_COLUMNS, MINUTE_FUTURE_HBASE_COLUMNS, TICK_FUTURE_HBASE_COLUMNS
from HFDataLoader.Config import TICK_CLEAN_OPEN_TIME, TICK_CLEAN_MORNING_START_TIME, TICK_CLEAN_MORNING_END_TIME, TICK_CLEAN_AFTERNOON_START_TIME, TICK_CLEAN_AFTERNOON_END_TIME
from IndexNonFactor.Config import INF_PREFIX, INF_NONFACTOR_COLUMNS
from Constants.INDEX_LIST import INDEX_LIST
from FactorDataTool.Config import SW_I_CODE, SW_II_CODE, CITICS_I_CODE, CITICS_II_CODE
from HFDataLoader.Config import TICK_ARRAY_FORMAT_COLUMNS
from HFDataLoader.DecimalUtil import myRound


class HFData(object):
    def __init__(self, library, code, tick_library=None, tran_order_library=None, inf_library=None, is_tick_l2p=False,
                 tick_clean_mode="StartNotEnd", cbond=None, verbose=True):
        self.library = library
        self.code = code
        self.tick_library = tick_library if tick_library is not None else self.library
        self.tran_order_library = tran_order_library if tran_order_library is not None else self.library
        self.inf_library = inf_library
        self.is_tick_l2p = is_tick_l2p
        self.tick_clean_mode = tick_clean_mode
        assert tick_clean_mode in ["NotClean", "StartEnd", "StartNotEnd"], " Only Support NotClean/StartEnd/StartNotEnd Tick Clean Mode: {} ".format(self.tick_clean_mode)
        self.cbond = cbond
        self.verbose = verbose
        self.code_type = get_code_type(self.code)
        self.decimal_size = 3 if self.code_type in ["CBOND", "ETF"] else 2

        self.indus_type = get_industry_type(self.code) if self.code_type == "INDUSTRY" else None

        self.fa = FactorData()

        self.is_executor = "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ

    def get_daily_data(self, start_date, end_date):
        """获取HBase中某个股票、指数、可转债、基金或期货一段时间的日频数据"""
        daily_df = self.get_full_daily_data_clean()
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
        minute_df = self.get_full_minute_data()
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
            sub_tick_df = self.get_daily_tick_data(trading_day, map_col=True)
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
            sub_transaction_df = self.get_daily_transaction_data(trading_day, map_col=True)
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
            sub_order_df = self.get_daily_order_data(trading_day, map_col=True)
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
            sub_tick_df = self.get_daily_inf_tick_data(trading_day, column_names, map_col=True)
            sub_tick_list.append(sub_tick_df)
        tick_df = pd.concat(sub_tick_list, axis=0)
        del sub_tick_list
        gc.collect()
        return tick_df

    def get_full_daily_data_clean(self):
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
                self.MyPrint(" WARN: Reading daily data from HBASE costs {} sec for {} ".format(round(timeCost, 2), self.code))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.MyPrint(" WARN: Reading daily data from HBASE costs {} sec for {} ".format(round(timeCost, 2), self.code))

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

    def get_full_daily_data(self):
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
                self.MyPrint(" WARN: Reading daily data from HBASE costs {} sec for {} ".format(round(timeCost, 2), self.code))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.MyPrint(" WARN: Reading daily data from HBASE costs {} sec for {} ".format(round(timeCost, 2), self.code))

            df = pd.DataFrame(columns=HBASE_COLUMNS)

        df.columns = list(map(lambda x: x.replace("{0}_".format(DAILY_SUFFIX), ""), df.columns.to_list()))
        if not df.empty:
            df.index = df["Date"].astype(np.int64)

        return df

    def get_full_minute_data(self):
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
                self.MyPrint(" WARN: Reading minute data from HBASE costs {} sec for {} ".format(round(timeCost, 2), self.code))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 5:
                self.MyPrint(" WARN: Reading minute data from HBASE costs {} sec for {} ".format(round(timeCost, 2), self.code))

            df = pd.DataFrame(columns=HBASE_COLUMNS)

        df.columns = list(map(lambda x: x.replace("{0}_".format(MINUTE_SUFFIX), ""), df.columns.to_list()))
        if not df.empty:
            df.index = df["Date"].astype(np.int64)

        return df
    def PK_Adjust(self,originalData):
        AskNName = ["T_AskN0", "T_AskN1", "T_AskN2", "T_AskN3", "T_AskN4", "T_AskN5", "T_AskN6", "T_AskN7", "T_AskN8", "T_AskN9"]
        BidNName = ["T_BidN0", "T_BidN1", "T_BidN2", "T_BidN3", "T_BidN4", "T_BidN5", "T_BidN6", "T_BidN7", "T_BidN8", "T_BidN9"]
        AskPName = ["T_AskP0", "T_AskP1", "T_AskP2", "T_AskP3", "T_AskP4", "T_AskP5", "T_AskP6", "T_AskP7", "T_AskP8", "T_AskP9"]
        BidPName = ["T_BidP0", "T_BidP1", "T_BidP2", "T_BidP3", "T_BidP4", "T_BidP5", "T_BidP6", "T_BidP7", "T_BidP8", "T_BidP9"]
        AskVName = ["T_AskV0", "T_AskV1", "T_AskV2", "T_AskV3", "T_AskV4", "T_AskV5", "T_AskV6", "T_AskV7", "T_AskV8", "T_AskV9"]
        BidVName = ["T_BidV0", "T_BidV1", "T_BidV2", "T_BidV3", "T_BidV4", "T_BidV5", "T_BidV6", "T_BidV7", "T_BidV8", "T_BidV9"]
        originalData['T_AskNum'] = originalData[AskNName].apply(lambda x: x.tolist(), axis=1)
        originalData['T_BidNum'] = originalData[BidNName].apply(lambda x: x.tolist(), axis=1)
        originalData['T_AskPrice'] = originalData[AskPName].apply(lambda x: x.tolist(), axis=1)
        originalData['T_BidPrice'] = originalData[BidPName].apply(lambda x: x.tolist(), axis=1)
        originalData['T_AskVolume'] = originalData[AskVName].apply(lambda x: x.tolist(), axis=1)
        originalData['T_BidVolume'] = originalData[BidVName].apply(lambda x: x.tolist(), axis=1)
        originalData = originalData[["T_Timestamp", "T_Date", "T_Time", "T_PreviousClose", "T_OpenPrice", "T_HighPrice", "T_LowPrice", "T_MaxPrice", "T_MinPrice", "T_LastPrice", "T_Volume", "T_Amount", "T_TotalVolume", "T_TotalAmount", "T_NumTrades",
                            "T_BidQty", "T_OfferQty", "T_AvgBidPrice", "T_AvgOfferPrice",
                            "T_BidPrice", "T_AskPrice", "T_BidVolume", "T_AskVolume", "T_BidNum", "T_AskNum", "T_TSIndex", "T_TEIndex", "T_OSIndex", "T_OEIndex", "T_IsMock"]]
        return originalData

    def get_daily_tick_data(self, date, map_col=True):
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

        if self.is_tick_l2p:
            HBASE_COLUMNS = HBASE_COLUMNS + ["T_TargetTimestamp"]

        startTime = dt.datetime.now()
        try:
            if self.code.split('.')[-1] == 'SZ':
                tick_library = self.tick_library + 'SZ2023'
            else:
                tick_library = self.tick_library + 'SH2023'
            df = self.fa.get_factor_value(tick_library, self.code, date, HBASE_COLUMNS,compress = True)
            df = self.PK_Adjust(df)
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.MyPrint(" WARN: Reading tick data from HBASE costs {} sec for {} on {} ".format(round(timeCost, 2), self.code, date))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.MyPrint(" WARN: Reading tick data from HBASE costs {} sec for {} on {} ".format(round(timeCost, 2), self.code, date))

            df = pd.DataFrame(columns=HBASE_COLUMNS)

        if map_col:
            df.columns = list(map(lambda x: x.replace("{0}_".format(TICK_SUFFIX), ""), df.columns.to_list()))

        if not df.empty:
            # Tick数据特定时间区间截断处理
            if self.tick_clean_mode in ["NotClean", "StartEnd", "StartNotEnd"]:
                df = self.cleanTickData(date, df, self.tick_clean_mode)
                round_columns = sorted(set(TICK_ARRAY_FORMAT_COLUMNS).intersection(df.columns.tolist()))
                for col in round_columns:
                    df[col] = df[col].apply(lambda x: np.array([myRound(i, self.decimal_size) for i in x],
                                                               dtype=np.float64) if x is not None else None)
            df.index = df["Date"].astype(np.int64)

        return df

    def get_daily_transaction_data(self, date, map_col=True):
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
            if self.code.split('.')[-1] == 'SZ':
                tran_order_library = self.tran_order_library + 'SZ2023IT'
            else:
                tran_order_library = self.tran_order_library + 'SH2023IT'
            df = self.fa.get_factor_value(tran_order_library, self.code, date, HBASE_COLUMNS,compress= True)
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.MyPrint(" WARN: Reading transaction data from HBASE costs {} sec for {} on {} ".format(round(timeCost, 2), self.code, date))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.MyPrint(" WARN: Reading transaction data from HBASE costs {} sec for {} on {} ".format(round(timeCost, 2), self.code, date))

            df = pd.DataFrame(columns=HBASE_COLUMNS)

        if map_col:
            df.columns = list(map(lambda x: x.replace("{0}_".format(TRANSACTION_SUFFIX), ""), df.columns.to_list()))

        if not df.empty:
            df.index = df["Date"].astype(np.int64)

        return df

    def get_daily_order_data(self, date, map_col=True):
        """获取HBase中某个股票、可转债、基金的历史某交易日的Transaction频数据"""
        if self.code_type == "STOCK":
            HBASE_COLUMNS = ORDER_STOCK_HBASE_COLUMNS
        elif self.code_type == "CBOND":
            HBASE_COLUMNS = ORDER_CBOND_HBASE_COLUMNS
        elif self.code_type in ["ETF", "LOF"]:
            HBASE_COLUMNS = ORDER_FUND_HBASE_COLUMNS
        else:
            raise Exception(" Not Supported Order Data For Code Type : {} ".format(self.code_type))

        startTime = dt.datetime.now()
        try:
            if self.code.split('.')[-1] == 'SZ':
                tran_order_library = self.tran_order_library + 'SZ2023IT'
            else:
                tran_order_library = self.tran_order_library + 'SH2023IT'
            df = self.fa.get_factor_value(tran_order_library, self.code, date, HBASE_COLUMNS, compress = True)
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.MyPrint(" WARN: Reading order data from HBASE costs {} sec for {} on {} ".format(round(timeCost, 2), self.code, date))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.MyPrint(" WARN: Reading order data from HBASE costs {} sec for {} on {} ".format(round(timeCost, 2), self.code, date))

            df = pd.DataFrame(columns=HBASE_COLUMNS)

        if map_col:
            df.columns = list(map(lambda x: x.replace("{0}_".format(ORDER_SUFFIX), ""), df.columns.to_list()))

        if not df.empty:
            df.index = df["Date"].astype(np.int64)

        return df

    def get_daily_inf_tick_data(self, date, column_names, map_col=True):
        """获取HBase中合成大盘/行业指数某交易日的Tick频数据, column_names为查询列名列表，默认为空List时取所有列名"""

        assert self.code in INDEX_LIST + SW_I_CODE + SW_II_CODE + CITICS_I_CODE + CITICS_II_CODE, " ONLY SUPPORT INDEX OR INDUSTRY "

        if self.inf_library is None:
            self.MyPrint(" WARN: USE DEFAULT INFactor LIBRARY ")
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
                self.MyPrint(" WARN: Reading tick data from HBASE costs {} sec for {} on {} ".format(round(timeCost, 2), self.code, date))
        except:
            endTime = dt.datetime.now()
            timeCost = (endTime - startTime).total_seconds()
            if self.verbose and timeCost >= 1:
                self.MyPrint(" WARN: Reading tick data from HBASE costs {} sec for {} on {} ".format(round(timeCost, 2), self.code, date))

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
            time_df = self.fa.get_factor_value(self.tick_library, code_save, date, HBASE_COLUMNS)
        except:
            time_df = pd.DataFrame(columns=HBASE_COLUMNS)
        time_df.columns = list(map(lambda x: x.replace("{0}_".format(TICK_SUFFIX), ""), time_df.columns.to_list()))

        tick_timestamp_dict = dict()
        if not time_df.empty:
            tick_timestamp_dict = time_df.set_index("Timestamp")["RealTimestamp"].to_dict()

        return tick_timestamp_dict

    def MyPrint(self, x_str):
        return remote_print(x_str) if self.is_executor else print(x_str)

    def cleanTickData(self, date, tick, tick_clean_mode="StartEnd"):
        if tick_clean_mode in ["StartEnd", "StartNotEnd"]:
            am_start_time, am_end_time, pm_start_time, pm_end_time = self.get_key_tick_timestamp(date)
            am_tick = tick[(tick["Timestamp"] >= am_start_time) & (tick["Timestamp"] <= am_end_time)]
            pm_tick = tick[(tick["Timestamp"] >= pm_start_time) & (tick["Timestamp"] <= pm_end_time)]
            align_am_tick = self.get_clean_tick_data(am_tick, am_start_time, am_end_time, tick_clean_mode)
            align_pm_tick = self.get_clean_tick_data(pm_tick, pm_start_time, pm_end_time, tick_clean_mode)
            align_tick = pd.concat([align_am_tick, align_pm_tick], axis=0).reset_index(drop=True)
        # tick_clean_mode == "NotClean"
        else:
            am_start_time = generate_timestamp(date, TICK_CLEAN_OPEN_TIME)
            pm_end_time = generate_timestamp(date, TICK_CLEAN_AFTERNOON_END_TIME)
            align_tick = tick[(tick["Timestamp"] >= am_start_time) & (tick["Timestamp"] <= pm_end_time)].reset_index(drop=True)
        return align_tick

    @staticmethod
    def get_clean_tick_data(tick, clean_start_timestamp, clean_end_timestamp, tick_clean_mode):
        tick_timestamp_list = tick["Timestamp"].values.tolist()
        fill_tick_timestamp_list = tick[tick["IsMock"] == 1]["Timestamp"].values.tolist()
        start_timestamp, end_timestamp = get_start_end_not_fill_tick(tick_timestamp_list, fill_tick_timestamp_list)
        if tick_clean_mode == "StartEnd":
            if start_timestamp is not None and end_timestamp is not None:
                start_timestamp = max(start_timestamp, clean_start_timestamp)
                end_timestamp = min(end_timestamp, clean_end_timestamp)
                tick = tick[(tick["Timestamp"] >= start_timestamp) & (tick["Timestamp"] <= end_timestamp)]
        elif tick_clean_mode == "StartNotEnd":
            if start_timestamp is not None:
                start_timestamp = max(start_timestamp, clean_start_timestamp)
                tick = tick[tick["Timestamp"] >= start_timestamp]
        else:
            raise Exception(" Not Supported Tick Data Clean Mode: {} ".format(tick_clean_mode))

        return tick

    @staticmethod
    def get_key_tick_timestamp(date):
        morning_start_timestamp = generate_timestamp(date, TICK_CLEAN_MORNING_START_TIME)
        morning_end_timestamp = generate_timestamp(date, TICK_CLEAN_MORNING_END_TIME)
        afternoon_start_timestamp = generate_timestamp(date, TICK_CLEAN_AFTERNOON_START_TIME)
        afternoon_end_timestamp = generate_timestamp(date, TICK_CLEAN_AFTERNOON_END_TIME)
        return morning_start_timestamp, morning_end_timestamp, afternoon_start_timestamp, afternoon_end_timestamp


if __name__ == "__main__":
    library = "Channel258STickDataLib"
    code = "300840.SZ"
    start_date = "20220125"
    instance = HFData(library, code)
    tick = instance.get_tick_data(start_date, start_date)
    print(tick.head())
