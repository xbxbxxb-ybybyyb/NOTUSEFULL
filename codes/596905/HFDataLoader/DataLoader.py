from HFDataLoader.Config import MAX_FRAME_LENGTH, THIRD_MAX_FRAME_LENGTH, MAX_MINUTE_KLINE, MAX_DAILY_KLINE
from HFDataLoader.Config import STOCK_RAW_DAILY_COLUMNS, STOCK_RAW_MINUTE_COLUMNS, STOCK_RAW_TICK_COLUMNS, STOCK_RAW_TRANSACTIONS_COLUMNS
from HFDataLoader.Config import STOCK_CLEAN_DAILY_COLUMNS, STOCK_CLEAN_MINUTE_COLUMNS, STOCK_CLEAN_TICK_COLUMNS, STOCK_CLEAN_TRANSACTIONS_COLUMNS
from HFDataLoader.Config import STOCK_TARGET_DAILY_COLUMNS, STOCK_TARGET_MINUTE_COLUMNS, STOCK_TARGET_TICK_COLUMNS, STOCK_TARGET_TRANSACTIONS_COLUMNS
from HFDataLoader.Config import INDEX_RAW_DAILY_COLUMNS, INDEX_RAW_MINUTE_COLUMNS, INDEX_RAW_TICK_COLUMNS
from HFDataLoader.Config import INDEX_CLEAN_DAILY_COLUMNS, INDEX_CLEAN_MINUTE_COLUMNS, INDEX_CLEAN_TICK_COLUMNS
from HFDataLoader.Config import INDEX_TARGET_DAILY_COLUMNS, INDEX_TARGET_MINUTE_COLUMNS, INDEX_TARGET_TICK_COLUMNS
from HFDataLoader.Config import CBOND_RAW_DAILY_COLUMNS, CBOND_CLEAN_DAILY_COLUMNS, CBOND_TARGET_DAILY_COLUMNS
from HFDataLoader.Config import CBOND_RAW_MINUTE_COLUMNS, CBOND_CLEAN_MINUTE_COLUMNS, CBOND_TARGET_MINUTE_COLUMNS
from HFDataLoader.Config import CBOND_RAW_TICK_COLUMNS, CBOND_CLEAN_TICK_COLUMNS, CBOND_TARGET_TICK_COLUMNS
from HFDataLoader.Config import CBOND_RAW_TRANSACTIONS_COLUMNS, CBOND_CLEAN_TRANSACTIONS_COLUMNS, CBOND_TARGET_TRANSACTIONS_COLUMNS
from HFDataLoader.Config import CBOND_SH_MINUTE_ADJUST_COLUMNS, CBOND_SH_TICK_ADJUST_COLUMNS, CBOND_SH_TRANSACTIONS_ADJUST_COLUMNS
from HFDataLoader.Config import CBOND_SH_VOLUME_MULTIPLE
from HFDataLoader.Config import FUND_RAW_DAILY_COLUMNS, FUND_CLEAN_DAILY_COLUMNS, FUND_TARGET_DAILY_COLUMNS
from HFDataLoader.Config import FUND_RAW_MINUTE_COLUMNS, FUND_CLEAN_MINUTE_COLUMNS, FUND_TARGET_MINUTE_COLUMNS
from HFDataLoader.Config import FUND_RAW_TICK_COLUMNS, FUND_CLEAN_TICK_COLUMNS, FUND_TARGET_TICK_COLUMNS
from HFDataLoader.Config import FUND_RAW_TRANSACTIONS_COLUMNS, FUND_CLEAN_TRANSACTIONS_COLUMNS, FUND_TARGET_TRANSACTIONS_COLUMNS
from HFDataLoader.Config import FUTURE_RAW_DAILY_COLUMNS, FUTURE_RAW_MINUTE_COLUMNS, FUTURE_RAW_TICK_COLUMNS
from HFDataLoader.Config import FUTURE_CLEAN_DAILY_COLUMNS, FUTURE_CLEAN_MINUTE_COLUMNS, FUTURE_CLEAN_TICK_COLUMNS
from HFDataLoader.Config import FUTURE_TARGET_DAILY_COLUMNS, FUTURE_TARGET_MINUTE_COLUMNS, FUTURE_TARGET_TICK_COLUMNS
from HFDataLoader.Config import SHENWAN_RAW_DAILY_COLUMNS, SHENWAN_CLEAN_DAILY_COLUMNS, SHENWAN_TARGET_DAILY_COLUMNS
from HFDataLoader.Config import ALIGN_STOCK_COLUMNS, ALIGN_INDEX_COLUMNS, ALIGN_CBOND_COLUMNS, ALIGN_FUND_COLUMNS, ALIGN_FUTURE_COLUMNS
from HFDataLoader.Config import DailyMonitor, MinuteMonitor, TickMonitor
from HFDataLoader.DataUtil import tickdata_OHL_filter, tickdata_circuit_filter, daily_clean_GEMSecurities
from HFDataLoader.DataUtil import daily_tick_transaction_align, daily_index_align, daily_future_align, minute_data_transform
import Utils.HelpFunc as Util

import os
import numpy as np
import pandas as pd
import datetime as dt
from xquant.factordata import FactorData
from xquant.marketdata import MarketData
from xquant.thirdpartydata.marketdata import MarketData as ThirdMarketData
from xquant.bonddata import BondData
from xquant.funddata import FundData
from xquant.futuredata import FutureData
from xquant.compute.sparkmr import remote_print


class DataLoader:
    def __init__(self, code, monitor=False):
        '''
        :param stock: "000001.SZ"
        '''
        self.code = code
        self.code_type = Util.get_code_type(self.code)
        self.indus_type = None
        if self.code_type == "INDUSTRY":
            self.indus_type = Util.get_industry_type(self.code)
        self.index_type = None
        if self.code_type == "INDEX":
            self.index_type = Util.get_index_type(self.code)
        self.future_contract_type = None
        if self.code_type == "FUTURE":
            self.future_contract_type = Util.get_future_contract_type(self.code)
        self.monitor = monitor

        self.fa = FactorData()
        self.mdp = MarketData()
        self.tma = ThirdMarketData()
        self.bd = BondData()
        self.fd = FundData()
        self.ftd = FutureData()

        self.is_executor = "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ

    def load_stock_daily_by_frame(self, start_date, end_date):
        """ 载入股票一段交易日中的所有日频数据，并根据列进行筛选、清洗
        """
        daily_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        try:
            daily_df = self.fa.get_factor_value('Basic_factor', stock=[self.code], mddate=trading_day_list,
                                       factor_names=STOCK_RAW_DAILY_COLUMNS)
        except:
            daily_df = pd.DataFrame(columns=STOCK_RAW_DAILY_COLUMNS)

        if daily_df.empty:
            daily_df = pd.DataFrame(columns=STOCK_TARGET_DAILY_COLUMNS)
            if self.monitor:
                daily_monitor.update({trading_day: DailyMonitor.EMPTY for trading_day in trading_day_list})
        else:
            daily_df = daily_df.droplevel(1)   ### Convert MultiIndex Format to DataFrame

            # 转换数据单位
            daily_df["volume"] = daily_df["volume"] * 100
            daily_df["amt"] = daily_df["amt"] * 1000
            daily_df.loc[:, ["total_shares", "free_float_shares"]] = daily_df.loc[:, ["total_shares", "free_float_shares"]] * 10000
            daily_df["ev"] = daily_df["ev"] * 10000
            daily_df["mkt_cap_ard"] = daily_df["mkt_cap_ard"] * 10000

            # 加入涨跌停价格
            up_down_threshold = (daily_df['stpt']=='1') * 0.05 + (daily_df['stpt']=='0') * 0.1
            daily_df['maxup'] = np.around((daily_df['pre_close'] * (1. + up_down_threshold)).astype(float), decimals=2)
            daily_df['maxdown'] = np.around((daily_df['pre_close'] * (1. - up_down_threshold)).astype(float), decimals=2)
            daily_df["date"] = list(map(str, list(daily_df.index)))
            daily_df = daily_df.reindex(columns=STOCK_CLEAN_DAILY_COLUMNS).reset_index(drop=True)
            daily_df.columns = STOCK_TARGET_DAILY_COLUMNS
            if self.monitor:
                for trading_day in trading_day_list:
                    this_daily_df = daily_df[daily_df['Date']==trading_day]
                    if this_daily_df.empty:
                        daily_monitor.update({trading_day: DailyMonitor.EMPTY})
                    else:
                        daily_monitor.update({trading_day: DailyMonitor.NORMAL})
        return daily_df, daily_monitor

    def load_stock_minute_by_frame(self, start_date, end_date):
        """ 载入股票一段交易日中的所有分钟数据，并根据列进行筛选、清洗、清洗
        """
        minute_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        sub_minute_list = []
        for trading_day in trading_day_list:
            date_minute_data = self.mdp.get_data_by_date("Kline1M4ZT", self.code, trading_day)
            if date_minute_data.empty:
                date_minute_data = pd.DataFrame(columns=STOCK_RAW_MINUTE_COLUMNS)
                if self.monitor:
                    minute_monitor.update({trading_day: MinuteMonitor.EMPTY})
            else:
                date_minute_data = date_minute_data[STOCK_RAW_MINUTE_COLUMNS]
                if self.monitor:
                    minute_monitor.update({trading_day: MinuteMonitor.NORMAL})
            sub_minute_list.append(date_minute_data)
        minute_df = pd.concat(sub_minute_list, axis=0)
        if minute_df.empty:
            minute_df = pd.DataFrame(columns=STOCK_TARGET_MINUTE_COLUMNS)
        else:
            minute_df["Timestamp"] = (minute_df["MDDate"] + minute_df["MDTime"]).apply(lambda x: dt.datetime.strptime(x+"000", "%Y%m%d%H%M%S%f").timestamp())
            minute_df = minute_df.reindex(columns=STOCK_CLEAN_MINUTE_COLUMNS)
            minute_df.columns = STOCK_TARGET_MINUTE_COLUMNS
            minute_df[["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]] = minute_df[["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]].fillna(method='ffill')
            minute_df[["Volume", "Amount"]] = minute_df[["Volume", "Amount"]].fillna(0.)
            # minute_df = minute_df[~minute_df["Volume"].isnull()]
            ###### 分钟数据处理，开盘集合竞价和收盘集合竞价数据剔除 ######
            minute_df.index = minute_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(int(x)))
            minute_df = minute_data_transform(minute_df, ["drop", "drop"])
            minute_df = minute_df.reindex(columns=STOCK_TARGET_MINUTE_COLUMNS).reset_index(drop=True)
        return minute_df, minute_monitor

    def load_stock_tick_by_frame(self, start_date, end_date):
        """ 载入股票一段交易日中所有Tick数据，并根据列进行筛选
        """
        tick_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, MAX_FRAME_LENGTH)
        sub_tick_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            # 读取股票Tick数据
            start_date_time = "{0} {1}".format(sub_start_date, "000001000")
            end_date_time = "{0} {1}".format(sub_end_date, "235959000")
            sub_tick_df = self.mdp.get_data_by_time_frame("Stock", self.code, start_date_time, end_date_time, ['1','2','3','4','5'])
            if sub_tick_df.empty:
                sub_tick_df = pd.DataFrame(columns=STOCK_RAW_TICK_COLUMNS)
            else:
                sub_tick_df = sub_tick_df[STOCK_RAW_TICK_COLUMNS]
                sub_tick_df = sub_tick_df.replace({'PreClosePx': 0.0}, np.nan)  # 如遇PreClose为0的，以前值填充之
                sub_tick_df = sub_tick_df.fillna(method='ffill')
                # 将连续竞价期间OpenPrice, HighPrice和LowPrice为0的条目删掉
                sub_tick_df = tickdata_OHL_filter(sub_tick_df)
            sub_tick_list.append(sub_tick_df)
        tick_df = pd.concat(sub_tick_list, axis=0)

        if tick_df.empty:
            tick_df = pd.DataFrame(columns=STOCK_TARGET_TICK_COLUMNS)
            if self.monitor:
                tick_monitor.update({trading_day: TickMonitor.EMPTY for trading_day in trading_day_list})
        else:
            # 清洗，加入"Timestamp", "VolumeTrade", "ValueTrade"字段
            tick_df["Timestamp"] = (tick_df["MDDate"] + tick_df["MDTime"]).apply(lambda x: dt.datetime.strptime(x+"000", "%Y%m%d%H%M%S%f").timestamp())
            daily_tick_df_list = []
            for trading_day in trading_day_list:
                daily_tick_df = tick_df[tick_df["MDDate"]==trading_day]
                if daily_tick_df.empty:
                    if self.monitor:
                        tick_monitor.update({trading_day: TickMonitor.EMPTY})
                else:
                    if self.monitor:
                        tick_monitor.update({trading_day: TickMonitor.NORMAL})
                    daily_tick_df = daily_tick_df.reset_index(drop=True)
                    daily_tick_df["VolumeTrade"] = daily_tick_df["TotalVolumeTrade"].diff()
                    daily_tick_df["ValueTrade"] = daily_tick_df["TotalValueTrade"].diff()
                    ### 每日第1行的成交额、成交量直接用累计成交额、累计成交量代替
                    daily_tick_df.loc[0, "VolumeTrade"] = daily_tick_df.loc[0, "TotalVolumeTrade"]
                    daily_tick_df.loc[0, "ValueTrade"] = daily_tick_df.loc[0, "TotalValueTrade"]
                    daily_tick_df["VolumeTrade"] = daily_tick_df["VolumeTrade"].clip_lower(0)
                    daily_tick_df["ValueTrade"] = daily_tick_df["ValueTrade"].clip_lower(0)
                    daily_tick_df_list.append(daily_tick_df)
            tick_df = pd.concat(daily_tick_df_list, axis=0)
            tick_df = tick_df.reindex(columns=STOCK_CLEAN_TICK_COLUMNS)
            tick_df.columns = STOCK_TARGET_TICK_COLUMNS
        return tick_df, tick_monitor

    def load_stock_transactions_by_frame(self, start_date, end_date):
        """ 载入股票的一段交易日中的所有逐笔成交数据，并根据列进行筛选、清洗
        """
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, MAX_FRAME_LENGTH)
        sub_transactions_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            # 读取股票逐笔数据
            start_date_time = "{0} {1}".format(sub_start_date, "000001000")
            end_date_time = "{0} {1}".format(sub_end_date, "235959000")
            sub_transactions_df = self.mdp.get_data_by_time_frame("Transaction", self.code, start_date_time, end_date_time, ['1','2','3','4','5'])
            if sub_transactions_df.empty:
                sub_transactions_df = pd.DataFrame(columns=STOCK_RAW_TRANSACTIONS_COLUMNS)
            else:
                sub_transactions_df = sub_transactions_df[STOCK_RAW_TRANSACTIONS_COLUMNS]
            sub_transactions_list.append(sub_transactions_df)
        transactions_df = pd.concat(sub_transactions_list, axis=0)
        if transactions_df.empty:
            transactions_df = pd.DataFrame(columns=STOCK_TARGET_TRANSACTIONS_COLUMNS)
        else:
            ### Filter out cancelled transactions record
            transactions_df = transactions_df[transactions_df['TradeType'] == 0]
            transactions_df["Timestamp"] = (transactions_df["MDDate"] + transactions_df["MDTime"]).apply(lambda x: dt.datetime.strptime(x+"000", "%Y%m%d%H%M%S%f").timestamp())
            transactions_df = transactions_df.reindex(columns=STOCK_CLEAN_TRANSACTIONS_COLUMNS)
            transactions_df.columns = STOCK_TARGET_TRANSACTIONS_COLUMNS
        return transactions_df

    def load_index_daily_by_frame(self, start_date, end_date):
        """ 载入指数的一段交易日中的所有日频数据，并根据列进行筛选、清洗、清洗
        """
        daily_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        daily_df = self.fa.get_factor_value('Basic_factor', stock=[self.code], mddate=trading_day_list,
                                       factor_names=INDEX_RAW_DAILY_COLUMNS)
        if daily_df.empty:
            daily_df = pd.DataFrame(columns=INDEX_TARGET_DAILY_COLUMNS)
            if self.monitor:
                daily_monitor.update({trading_day: DailyMonitor.EMPTY for trading_day in trading_day_list})
        else:
            daily_df = daily_df.droplevel(1)
            ### 转换单位
            daily_df["volume"] = daily_df["volume"] * 100
            daily_df["amt"] = daily_df["amt"] * 1000

            daily_df["date"] = list(map(str, list(daily_df.index)))
            daily_df = daily_df.reindex(columns=INDEX_CLEAN_DAILY_COLUMNS)
            daily_df.columns = INDEX_TARGET_DAILY_COLUMNS
            if self.monitor:
                for trading_day in trading_day_list:
                    this_daily_df = daily_df[daily_df['Date']==trading_day]
                    if this_daily_df.empty:
                        daily_monitor.update({trading_day: DailyMonitor.EMPTY})
                    else:
                        daily_monitor.update({trading_day: DailyMonitor.NORMAL})
        return daily_df, daily_monitor

    def load_index_minute_by_frame(self, start_date, end_date):
        """ 载入指数的一段交易日中的所有分钟数据，并根据列进行筛选、清洗、清洗
        """
        minute_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        sub_minute_list = []
        for trading_day in trading_day_list:
            date_minute_data = self.mdp.get_data_by_date("Kline1M4ZT", self.code, trading_day)
            if date_minute_data.empty:
                date_minute_data = pd.DataFrame(columns=INDEX_RAW_MINUTE_COLUMNS)
                if self.monitor:
                    minute_monitor.update({trading_day: MinuteMonitor.EMPTY})
            else:
                date_minute_data = date_minute_data[INDEX_RAW_MINUTE_COLUMNS]
                if self.monitor:
                    minute_monitor.update({trading_day: MinuteMonitor.NORMAL})
            sub_minute_list.append(date_minute_data)
        minute_df = pd.concat(sub_minute_list, axis=0)

        if minute_df.empty:
            minute_df = pd.DataFrame(columns=INDEX_TARGET_MINUTE_COLUMNS)
        else:
            minute_df["Timestamp"] = (minute_df["MDDate"] + minute_df["MDTime"]).apply(
                                                 lambda x: dt.datetime.strptime(x+"000", "%Y%m%d%H%M%S%f").timestamp())
            minute_df = minute_df.reindex(columns=INDEX_CLEAN_MINUTE_COLUMNS)
            minute_df.columns = INDEX_TARGET_MINUTE_COLUMNS
            minute_df[["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]] = minute_df[["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]].fillna(method='ffill')
            minute_df[["Volume", "Amount"]] = minute_df[["Volume", "Amount"]].fillna(0.)
            ###### 分钟数据处理，开盘集合竞价和收盘集合竞价数据剔除 ######
            minute_df.index = minute_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(int(x)))
            minute_df = minute_data_transform(minute_df, ["drop", "drop"])
            minute_df = minute_df.reindex(columns=INDEX_TARGET_MINUTE_COLUMNS).reset_index(drop=True)
        return minute_df, minute_monitor

    def load_index_tick_by_frame(self, start_date, end_date):
        """ 载入指数一段交易日中所有Tick数据，并根据列进行筛选
        """
        tick_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, MAX_FRAME_LENGTH)
        sub_tick_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "000001000")
            end_date_time = "{0} {1}".format(sub_end_date, "235959000")
            sub_tick_df = self.mdp.get_data_by_time_frame("INDEX", self.code, start_date_time, end_date_time, ['1','2','3','4','5'])
            if sub_tick_df.empty:
                sub_tick_df = pd.DataFrame(columns=INDEX_RAW_TICK_COLUMNS)
            else:
                sub_tick_df = sub_tick_df[INDEX_RAW_TICK_COLUMNS]
                sub_tick_df = sub_tick_df.replace({'PreClosePx': 0.0}, np.nan)  # 如遇PreClose为0的，以前值填充之
                sub_tick_df = sub_tick_df.fillna(method='ffill')
                # 将连续竞价期间OpenPrice, HighPrice和LowPrice为0的条目删掉
                sub_tick_df = tickdata_OHL_filter(sub_tick_df)
            sub_tick_list.append(sub_tick_df)
        tick_df = pd.concat(sub_tick_list, axis=0)

        if tick_df.empty:
            tick_df = pd.DataFrame(columns=STOCK_TARGET_TICK_COLUMNS)
            if self.monitor:
                tick_monitor.update({trading_day: TickMonitor.EMPTY for trading_day in trading_day_list})
        else:
            tick_df["Timestamp"] = (tick_df["MDDate"] + tick_df["MDTime"]).apply(lambda x: dt.datetime.strptime(x+"000", "%Y%m%d%H%M%S%f").timestamp())
            daily_tick_df_list = []
            for trading_day in trading_day_list:
                daily_tick_df = tick_df[tick_df["MDDate"]==trading_day]
                if daily_tick_df.empty:
                    if self.monitor:
                        tick_monitor.update({trading_day: TickMonitor.EMPTY})
                else:
                    if self.monitor:
                        tick_monitor.update({trading_day: TickMonitor.NORMAL})
                    daily_tick_df = daily_tick_df.reset_index(drop=True)
                    daily_tick_df["VolumeTrade"] = daily_tick_df["TotalVolumeTrade"].diff().values
                    daily_tick_df["ValueTrade"] = daily_tick_df["TotalValueTrade"].diff().values
                    daily_tick_df.loc[0, "VolumeTrade"] = daily_tick_df.loc[0, "TotalVolumeTrade"]
                    daily_tick_df.loc[0, "ValueTrade"] = daily_tick_df.loc[0, "TotalValueTrade"]
                    daily_tick_df["VolumeTrade"] = daily_tick_df["VolumeTrade"].clip_lower(0)
                    daily_tick_df["ValueTrade"] = daily_tick_df["ValueTrade"].clip_lower(0)
                    daily_tick_df_list.append(daily_tick_df)
            tick_df = pd.concat(daily_tick_df_list, axis=0)
            tick_df = tick_df.reindex(columns=INDEX_CLEAN_TICK_COLUMNS)
            tick_df.columns = INDEX_TARGET_TICK_COLUMNS
        return tick_df, tick_monitor

    def load_cbond_daily_by_frame(self, start_date, end_date):
        """ 载入可转债一段交易日中的所有日频数据，并根据列进行筛选、清洗
        """
        daily_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        try:
            daily_df = self.fa.get_factor_value('Basic_factor', stock=[self.code], mddate=trading_day_list,
                                       factor_names=CBOND_RAW_DAILY_COLUMNS, category="bond")
        except:
            daily_df = pd.DataFrame(columns=CBOND_RAW_DAILY_COLUMNS)

        if daily_df.empty:
            daily_df = pd.DataFrame(columns=CBOND_TARGET_DAILY_COLUMNS)
            if self.monitor:
                daily_monitor.update({trading_day: DailyMonitor.EMPTY for trading_day in trading_day_list})
        else:
            daily_df = daily_df.droplevel(1)   ### Convert MultiIndex Format to DataFrame

            # 转换数据单位
            daily_df["volume"] = daily_df["volume"] * 10
            daily_df["amount"] = daily_df["amount"] * 1000

            # 加入涨跌停价格
            daily_df['maxup'] = 10**9
            if self.code.endswith(".SH"):
                daily_df['maxdown'] = 0.01
            elif self.code.endswith(".SZ"):
                daily_df["maxdown"] = 0.001
            daily_df["adjfactor"] = 1.

            daily_df["date"] = list(map(str, list(daily_df.index)))
            daily_df = daily_df.reindex(columns=CBOND_CLEAN_DAILY_COLUMNS).reset_index(drop=True)
            daily_df.columns = CBOND_TARGET_DAILY_COLUMNS
            if self.monitor:
                for trading_day in trading_day_list:
                    this_daily_df = daily_df[daily_df['Date']==trading_day]
                    if this_daily_df.empty:
                        daily_monitor.update({trading_day: DailyMonitor.EMPTY})
                    else:
                        daily_monitor.update({trading_day: DailyMonitor.NORMAL})
        return daily_df, daily_monitor

    def load_cbond_minute_by_frame(self, start_date, end_date):
        """ 载入可转债一段交易日中的所有分钟数据，并根据列进行筛选、清洗、清洗
        """
        minute_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)
        sub_minute_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "090000000")
            end_date_time = "{0} {1}".format(sub_end_date, "200000000")
            sub_minute_df = self.bd.get_bond_data(self.code, start_date_time, end_date_time, "K_1MIN")
            if sub_minute_df.empty:
                sub_minute_df = pd.DataFrame(columns=CBOND_RAW_MINUTE_COLUMNS)
            else:
                sub_minute_df = sub_minute_df[CBOND_RAW_MINUTE_COLUMNS]
            sub_minute_list.append(sub_minute_df)
        minute_df = pd.concat(sub_minute_list, axis=0)

        if minute_df.empty:
            minute_df = pd.DataFrame(columns=CBOND_TARGET_MINUTE_COLUMNS)
            minute_monitor.update({trading_day: MinuteMonitor.EMPTY for trading_day in trading_day_list})
        else:
            minute_df["Timestamp"] = (minute_df["MDDate"] + minute_df["MDTime"]).apply(lambda x: dt.datetime.strptime(x+"000", "%Y%m%d%H%M%S%f").timestamp())
            minute_df = minute_df.reindex(columns=CBOND_CLEAN_MINUTE_COLUMNS)
            minute_df.columns = CBOND_TARGET_MINUTE_COLUMNS
            minute_df[["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]] = minute_df[["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]].fillna(method='ffill')
            minute_df[["Volume", "Amount"]] = minute_df[["Volume", "Amount"]].fillna(0.)
            if self.code_type=="CBOND" and self.code.split(".")[1]=="SH":
                minute_df[CBOND_SH_MINUTE_ADJUST_COLUMNS] = minute_df[CBOND_SH_MINUTE_ADJUST_COLUMNS] * CBOND_SH_VOLUME_MULTIPLE
            ###### 分钟数据处理，开盘集合竞价和收盘集合竞价数据剔除 ######
            minute_df.index = minute_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(int(x)))
            minute_df = minute_data_transform(minute_df, ["drop", "drop"])
            minute_df = minute_df.reindex(columns=CBOND_TARGET_MINUTE_COLUMNS).reset_index(drop=True)
            for trading_day in trading_day_list:
                sub_minute_df = minute_df[minute_df['Date'] == trading_day]
                if sub_minute_df.empty:
                    if self.monitor:
                        minute_monitor.update({trading_day: MinuteMonitor.EMPTY})
                else:
                    if self.monitor:
                        minute_monitor.update({trading_day: MinuteMonitor.NORMAL})
        return minute_df, minute_monitor

    def load_cbond_tick_by_frame(self, start_date, end_date):
        """ 载入可转债一段交易日中的所有Tick数据，并根据列进行筛选
        """
        tick_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)
        sub_tick_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "092500000")
            end_date_time = "{0} {1}".format(sub_end_date, "150000000")
            sub_tick_df = self.bd.get_bond_data(self.code, start_date_time, end_date_time, "TICK")
            if sub_tick_df.empty:
                sub_tick_df = pd.DataFrame(columns=CBOND_RAW_TICK_COLUMNS)
            else:
                sub_tick_df = sub_tick_df[CBOND_RAW_TICK_COLUMNS]
                sub_tick_df = sub_tick_df.replace({'PreClosePx': 0.0}, np.nan)  # 如遇PreClose为0的，以前值填充之
                sub_tick_df = sub_tick_df.fillna(method='ffill')
                # 将连续竞价期间OpenPrice, HighPrice和LowPrice为0的条目删掉
                sub_tick_df = tickdata_OHL_filter(sub_tick_df)
                sub_tick_df = tickdata_circuit_filter(sub_tick_df)
            sub_tick_list.append(sub_tick_df)
        tick_df = pd.concat(sub_tick_list, axis=0)

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
                    daily_tick_df["VolumeTrade"] = daily_tick_df["TotalVolumeTrade"].diff()
                    daily_tick_df["ValueTrade"] = daily_tick_df["TotalValueTrade"].diff()
                    daily_tick_df.loc[0, "VolumeTrade"] = daily_tick_df.loc[0, "TotalVolumeTrade"]
                    daily_tick_df.loc[0, "ValueTrade"] = daily_tick_df.loc[0, "TotalValueTrade"]
                    daily_tick_df["VolumeTrade"] = daily_tick_df["VolumeTrade"].clip_lower(0)
                    daily_tick_df["ValueTrade"] = daily_tick_df["ValueTrade"].clip_lower(0)
                    daily_tick_df_list.append(daily_tick_df)
            tick_df = pd.concat(daily_tick_df_list, axis=0)
            tick_df = tick_df.reindex(columns=CBOND_CLEAN_TICK_COLUMNS)
            tick_df.columns = CBOND_TARGET_TICK_COLUMNS
            if self.code_type == "CBOND" and self.code.split(".")[1] == "SH":
                tick_df[CBOND_SH_TICK_ADJUST_COLUMNS] = tick_df[CBOND_SH_TICK_ADJUST_COLUMNS] * CBOND_SH_VOLUME_MULTIPLE
        return tick_df, tick_monitor

    def load_cbond_transactions_by_frame(self, start_date, end_date):
        """ 载入可转债的一段交易日中的所有逐笔成交数据，并根据列进行筛选、清洗
        """
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)
        sub_transactions_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "092500000")
            end_date_time = "{0} {1}".format(sub_end_date, "150000000")
            sub_transactions_df = self.bd.get_bond_data(self.code, start_date_time, end_date_time, "TRANSACTION")
            if sub_transactions_df.empty:
                sub_transactions_df = pd.DataFrame(columns=CBOND_RAW_TRANSACTIONS_COLUMNS)
            else:
                sub_transactions_df = sub_transactions_df[CBOND_RAW_TRANSACTIONS_COLUMNS]
            sub_transactions_list.append(sub_transactions_df)
        transactions_df = pd.concat(sub_transactions_list, axis=0)
        if transactions_df.empty:
            transactions_df = pd.DataFrame(columns=CBOND_TARGET_TRANSACTIONS_COLUMNS)
        else:
            ### Filter out cancelled transaction record
            transactions_df = transactions_df[transactions_df['TradeType'] == 0]
            transactions_df["Timestamp"] = (transactions_df["MDDate"] + transactions_df["MDTime"]).apply(
                                                 lambda x: dt.datetime.strptime(x+"000", "%Y%m%d%H%M%S%f").timestamp())
            transactions_df = transactions_df.reindex(columns=CBOND_CLEAN_TRANSACTIONS_COLUMNS)
            transactions_df.columns = CBOND_TARGET_TRANSACTIONS_COLUMNS
            if self.code_type=="CBOND" and self.code.split(".")[1]=="SH":
                transactions_df[CBOND_SH_TRANSACTIONS_ADJUST_COLUMNS] = transactions_df[CBOND_SH_TRANSACTIONS_ADJUST_COLUMNS] * CBOND_SH_VOLUME_MULTIPLE
        return transactions_df

    def load_fund_daily_by_frame(self, start_date, end_date):
        """ 载入FUND一段交易日中的所有日频数据，并根据列进行筛选、清洗
        """
        daily_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)
        sub_daily_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "090000000")
            end_date_time = "{0} {1}".format(sub_end_date, "200000000")
            sub_daily_df = self.fd.get_fund_data(self.code, start_date_time, end_date_time, "K_DAY")
            if sub_daily_df.empty:
                sub_daily_df = pd.DataFrame(columns=FUND_RAW_DAILY_COLUMNS)
            else:
                sub_daily_df = sub_daily_df[FUND_RAW_DAILY_COLUMNS]
            sub_daily_list.append(sub_daily_df)
        daily_df = pd.concat(sub_daily_list, axis=0)

        ### 从WIND获取其他日频字段, Wind落地库限制了并发访问数量，大规模访问受限
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

        ### 将Wind落地库信息合并到日频数据里，Inner连接：取mdp接口数据与wind落地库数据交集
        daily_df = pd.merge(daily_df, wind_df, on="MDDate", how="inner")

        ### 参考Basic_Factor，将没有日期记录的数据全部填充为NAN
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
                    this_daily_df = daily_df[daily_df['Date']==trading_day]
                    if this_daily_df.empty:
                        daily_monitor.update({trading_day: DailyMonitor.EMPTY})
                    else:
                        daily_monitor.update({trading_day: DailyMonitor.NORMAL})
        return daily_df, daily_monitor

    def load_fund_minute_by_frame(self, start_date, end_date):
        """ 载入FUND一段交易日中的所有分钟数据，并根据列进行筛选、清洗、清洗
        """
        minute_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)
        sub_minute_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "090000000")
            end_date_time = "{0} {1}".format(sub_end_date, "200000000")
            sub_minute_df = self.fd.get_fund_data(self.code, start_date_time, end_date_time, "K_1MIN")
            if sub_minute_df.empty:
                sub_minute_df = pd.DataFrame(columns=FUND_RAW_MINUTE_COLUMNS)
            else:
                sub_minute_df = sub_minute_df[FUND_RAW_MINUTE_COLUMNS]
            sub_minute_list.append(sub_minute_df)
        minute_df = pd.concat(sub_minute_list, axis=0)

        if minute_df.empty:
            minute_df = pd.DataFrame(columns=FUND_TARGET_MINUTE_COLUMNS)
            minute_monitor.update({trading_day: MinuteMonitor.EMPTY for trading_day in trading_day_list})
        else:
            minute_df["Timestamp"] = (minute_df["MDDate"] + minute_df["MDTime"]).apply(lambda x: dt.datetime.strptime(x+"000", "%Y%m%d%H%M%S%f").timestamp())
            minute_df = minute_df.reindex(columns=FUND_CLEAN_MINUTE_COLUMNS)
            minute_df.columns = FUND_TARGET_MINUTE_COLUMNS
            minute_df[["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]] = minute_df[["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]].fillna(method='ffill')
            minute_df[["Volume", "Amount"]] = minute_df[["Volume", "Amount"]].fillna(0.)
            ###### 分钟数据处理，开盘集合竞价和收盘集合竞价数据剔除 ######
            minute_df.index = minute_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(int(x)))
            minute_df = minute_data_transform(minute_df, ["drop", "drop"])
            minute_df = minute_df.reindex(columns=FUND_TARGET_MINUTE_COLUMNS).reset_index(drop=True)
            for trading_day in trading_day_list:
                sub_minute_df = minute_df[minute_df['Date'] == trading_day]
                if sub_minute_df.empty:
                    if self.monitor:
                        minute_monitor.update({trading_day: MinuteMonitor.EMPTY})
                else:
                    if self.monitor:
                        minute_monitor.update({trading_day: MinuteMonitor.NORMAL})
        return minute_df, minute_monitor

    def load_fund_tick_by_frame(self, start_date, end_date):
        """ 载入FUND一段交易日中的所有Tick数据，并根据列进行筛选
        """
        tick_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)
        sub_tick_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "092500000")
            end_date_time = "{0} {1}".format(sub_end_date, "150000000")
            sub_tick_df = self.fd.get_fund_data(self.code, start_date_time, end_date_time, "TICK")
            if sub_tick_df.empty:
                sub_tick_df = pd.DataFrame(columns=FUND_RAW_TICK_COLUMNS)
            else:
                sub_tick_df = sub_tick_df[FUND_RAW_TICK_COLUMNS]
                sub_tick_df = sub_tick_df.replace({'PreClosePx': 0.0}, np.nan)  # 如遇PreClose为0的，以前值填充之
                sub_tick_df = sub_tick_df.fillna(method='ffill')
                # 将连续竞价期间OpenPrice, HighPrice和LowPrice为0的条目删掉
                sub_tick_df = tickdata_OHL_filter(sub_tick_df)
            sub_tick_list.append(sub_tick_df)
        tick_df = pd.concat(sub_tick_list, axis=0)

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
                    daily_tick_df["VolumeTrade"] = daily_tick_df["TotalVolumeTrade"].diff()
                    daily_tick_df["ValueTrade"] = daily_tick_df["TotalValueTrade"].diff()
                    daily_tick_df.loc[0, "VolumeTrade"] = daily_tick_df.loc[0, "TotalVolumeTrade"]
                    daily_tick_df.loc[0, "ValueTrade"] = daily_tick_df.loc[0, "TotalValueTrade"]
                    daily_tick_df["VolumeTrade"] = daily_tick_df["VolumeTrade"].clip_lower(0)
                    daily_tick_df["ValueTrade"] = daily_tick_df["ValueTrade"].clip_lower(0)
                    daily_tick_df_list.append(daily_tick_df)
            tick_df = pd.concat(daily_tick_df_list, axis=0)
            tick_df = tick_df.reindex(columns=FUND_CLEAN_TICK_COLUMNS)
            tick_df.columns = FUND_TARGET_TICK_COLUMNS
        return tick_df, tick_monitor

    def load_fund_transactions_by_frame(self, start_date, end_date):
        """ 载入FUND的一段交易日中的所有逐笔成交数据，并根据列进行筛选、清洗
        """
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)
        sub_transactions_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "092500000")
            end_date_time = "{0} {1}".format(sub_end_date, "150000000")
            sub_transactions_df = self.fd.get_fund_data(self.code, start_date_time, end_date_time, "TRANSACTION")
            if sub_transactions_df.empty:
                sub_transactions_df = pd.DataFrame(columns=FUND_RAW_TRANSACTIONS_COLUMNS)
            else:
                sub_transactions_df = sub_transactions_df[FUND_RAW_TRANSACTIONS_COLUMNS]
            sub_transactions_list.append(sub_transactions_df)
        transactions_df = pd.concat(sub_transactions_list, axis=0)
        if transactions_df.empty:
            transactions_df = pd.DataFrame(columns=FUND_TARGET_TRANSACTIONS_COLUMNS)
        else:
            ### Filter out cancelled transaction record
            transactions_df = transactions_df[transactions_df['TradeType'] == 0]
            transactions_df["Timestamp"] = (transactions_df["MDDate"] + transactions_df["MDTime"]).apply(
                lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            transactions_df = transactions_df.reindex(columns=FUND_CLEAN_TRANSACTIONS_COLUMNS)
            transactions_df.columns = FUND_TARGET_TRANSACTIONS_COLUMNS
        return transactions_df

    def load_industry_daily_by_frame(self, start_date, end_date):
        """ 载入FUND一段交易日中的所有日频数据，并根据列进行筛选、清洗
        """
        daily_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)
        sub_daily_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "090000000")
            end_date_time = "{0} {1}".format(sub_end_date, "200000000")
            sub_daily_df = self.mdp.get_index_data(self.code, start_date_time, end_date_time, "K_DAY")
            if sub_daily_df.empty:
                sub_daily_df = pd.DataFrame(columns=SHENWAN_RAW_DAILY_COLUMNS)
            else:
                sub_daily_df = sub_daily_df[SHENWAN_RAW_DAILY_COLUMNS]
            sub_daily_list.append(sub_daily_df)
        daily_df = pd.concat(sub_daily_list, axis=0)

        if daily_df.empty:
            daily_df = pd.DataFrame(columns=SHENWAN_TARGET_DAILY_COLUMNS)
            if self.monitor:
                daily_monitor.update({trading_day: DailyMonitor.EMPTY for trading_day in trading_day_list})
        else:
            daily_df = daily_df.reindex(columns=SHENWAN_CLEAN_DAILY_COLUMNS).reset_index(drop=True)
            daily_df.columns = SHENWAN_TARGET_DAILY_COLUMNS
            if self.monitor:
                for trading_day in trading_day_list:
                    this_daily_df = daily_df[daily_df['Date']==trading_day]
                    if this_daily_df.empty:
                        daily_monitor.update({trading_day: DailyMonitor.EMPTY})
                    else:
                        daily_monitor.update({trading_day: DailyMonitor.NORMAL})
        return daily_df, daily_monitor

    def load_industry_minute_by_frame(self, start_date, end_date):
        """ 载入FUND一段交易日中的所有分钟数据，并根据列进行筛选、清洗、清洗
        """
        minute_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)
        sub_minute_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "090000000")
            end_date_time = "{0} {1}".format(sub_end_date, "200000000")
            sub_minute_df = self.mdp.get_index_data(self.code, start_date_time, end_date_time, "K_1MIN")
            if sub_minute_df.empty:
                sub_minute_df = pd.DataFrame(columns=INDEX_RAW_MINUTE_COLUMNS)
            else:
                sub_minute_df = sub_minute_df[INDEX_RAW_MINUTE_COLUMNS]
            sub_minute_list.append(sub_minute_df)
        minute_df = pd.concat(sub_minute_list, axis=0)

        if minute_df.empty:
            minute_df = pd.DataFrame(columns=INDEX_TARGET_MINUTE_COLUMNS)
            minute_monitor.update({trading_day: MinuteMonitor.EMPTY for trading_day in trading_day_list})
        else:
            minute_df["Timestamp"] = (minute_df["MDDate"] + minute_df["MDTime"]).apply(lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            minute_df = minute_df.reindex(columns=INDEX_CLEAN_MINUTE_COLUMNS)
            minute_df.columns = INDEX_TARGET_MINUTE_COLUMNS
            minute_df[["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]] = minute_df[["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]].fillna(method='ffill')
            minute_df[["Volume", "Amount"]] = minute_df[["Volume", "Amount"]].fillna(0.)
            ###### 分钟数据处理，开盘集合竞价和收盘集合竞价数据剔除 ######
            minute_df.index = minute_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(int(x)))
            minute_df = minute_data_transform(minute_df, ["drop", "drop"])
            minute_df = minute_df.reindex(columns=INDEX_TARGET_MINUTE_COLUMNS).reset_index(drop=True)
            for trading_day in trading_day_list:
                sub_minute_df = minute_df[minute_df['Date'] == trading_day]
                if sub_minute_df.empty:
                    if self.monitor:
                        minute_monitor.update({trading_day: MinuteMonitor.EMPTY})
                else:
                    if self.monitor:
                        minute_monitor.update({trading_day: MinuteMonitor.NORMAL})
        return minute_df, minute_monitor

    def load_industry_tick_by_frame(self, start_date, end_date):
        """ 载入FUND一段交易日中的所有Tick数据，并根据列进行筛选
        """
        tick_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)
        sub_tick_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "092500000")
            end_date_time = "{0} {1}".format(sub_end_date, "150000000")
            sub_tick_df = self.mdp.get_index_data(self.code, start_date_time, end_date_time, "TICK")
            if sub_tick_df.empty:
                sub_tick_df = pd.DataFrame(columns=INDEX_RAW_TICK_COLUMNS)
            else:
                sub_tick_df = sub_tick_df[INDEX_RAW_TICK_COLUMNS]
                sub_tick_df = sub_tick_df.replace({'PreClosePx': 0.0}, np.nan)  # 如遇PreClose为0的，以前值填充之
                sub_tick_df = sub_tick_df.fillna(method='ffill')
                # 将连续竞价期间OpenPrice, HighPrice和LowPrice为0的条目删掉
                sub_tick_df = tickdata_OHL_filter(sub_tick_df)
            sub_tick_list.append(sub_tick_df)
        tick_df = pd.concat(sub_tick_list, axis=0)

        if tick_df.empty:
            tick_df = pd.DataFrame(columns=INDEX_TARGET_TICK_COLUMNS)
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
                    daily_tick_df["VolumeTrade"] = daily_tick_df["TotalVolumeTrade"].diff()
                    daily_tick_df["ValueTrade"] = daily_tick_df["TotalValueTrade"].diff()
                    daily_tick_df.loc[0, "VolumeTrade"] = daily_tick_df.loc[0, "TotalVolumeTrade"]
                    daily_tick_df.loc[0, "ValueTrade"] = daily_tick_df.loc[0, "TotalValueTrade"]
                    daily_tick_df["VolumeTrade"] = daily_tick_df["VolumeTrade"].clip_lower(0)
                    daily_tick_df["ValueTrade"] = daily_tick_df["ValueTrade"].clip_lower(0)
                    daily_tick_df_list.append(daily_tick_df)
            tick_df = pd.concat(daily_tick_df_list, axis=0)
            tick_df = tick_df.reindex(columns=INDEX_CLEAN_TICK_COLUMNS)
            tick_df.columns = INDEX_TARGET_TICK_COLUMNS
        return tick_df, tick_monitor

    ### 行情中心ThirdParty接口，供研究使用，避免大规模并发访问
    def load_third_daily_by_frame(self, start_date, end_date):
        '''
        从ThirdParty接口载入标的一段交易日中的所有日频数据，并根据列进行筛选、清洗
        '''
        daily_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, MAX_DAILY_KLINE)  ### 日K线最长查询为365天
        sub_daily_list = []
        for group in calc_time_groups:
            start_date_time = "{0}{1}".format(group[0], "090000000")
            end_date_time = "{0}{1}".format(group[-1], "200000000")
            sub_daily_data = self.tma.getMDSecurityKLineDataFrame(self.code, start_date_time, end_date_time, 10, 25)
            sub_daily_data = sub_daily_data[SHENWAN_RAW_DAILY_COLUMNS]
            sub_daily_list.append(sub_daily_data)
        daily_df = pd.concat(sub_daily_list, axis=0)
        if daily_df.empty:
            daily_df = pd.DataFrame(columns=SHENWAN_TARGET_DAILY_COLUMNS)
            if self.monitor:
                daily_monitor.update({trading_day: DailyMonitor.EMPTY for trading_day in trading_day_list})
        else:
            daily_df = daily_df.reindex(columns=SHENWAN_CLEAN_DAILY_COLUMNS).reset_index(drop=True)
            daily_df.columns = SHENWAN_TARGET_DAILY_COLUMNS
            if self.monitor:
                for trading_day in trading_day_list:
                    this_daily_df = daily_df[daily_df['Date']==trading_day]
                    if this_daily_df.empty:
                        daily_monitor.update({trading_day: DailyMonitor.EMPTY})
                    else:
                        daily_monitor.update({trading_day: DailyMonitor.NORMAL})
        return daily_df, daily_monitor

    def load_third_minute_by_frame(self, start_date, end_date):
        '''
         从ThirdParty接口载入标的一段交易日中的所有分钟数据，并根据列进行筛选、清洗、清洗
         '''
        minute_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, MAX_MINUTE_KLINE)  ## 分钟K线最长查询为7天
        sub_minute_list = []
        for group in calc_time_groups:
            start_date_time = "{0}{1}".format(group[0], "090000000")
            end_date_time = "{0}{1}".format(group[-1], "150000000")
            sub_minute_data = self.tma.getKLine4ZTDataFrame(self.code, start_date_time, end_date_time, 10, 20)
            sub_minute_data = sub_minute_data[INDEX_RAW_MINUTE_COLUMNS]
            sub_minute_list.append(sub_minute_data)
        minute_df = pd.concat(sub_minute_list, axis=0)

        if minute_df.empty:
            minute_df = pd.DataFrame(columns=INDEX_TARGET_MINUTE_COLUMNS)
            minute_monitor.update({trading_day: MinuteMonitor.EMPTY for trading_day in trading_day_list})
        else:
            minute_df["Timestamp"] = (minute_df["MDDate"] + minute_df["MDTime"]).apply(
                lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            minute_df = minute_df.reindex(columns=INDEX_CLEAN_MINUTE_COLUMNS)
            minute_df.columns = INDEX_TARGET_MINUTE_COLUMNS
            minute_df[["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]] = minute_df[["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]].fillna(method='ffill')
            minute_df[["Volume", "Amount"]] = minute_df[["Volume", "Amount"]].fillna(0.)
            ###### 分钟数据处理，开盘集合竞价和收盘集合竞价数据剔除 ######
            minute_df.index = minute_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(int(x)))
            minute_df = minute_data_transform(minute_df, ["drop", "drop"])
            minute_df = minute_df.reindex(columns=INDEX_TARGET_MINUTE_COLUMNS).reset_index(drop=True)
            for trading_day in trading_day_list:
                daily_minute_df = minute_df[minute_df['Date'] == trading_day]
                if daily_minute_df.empty:
                    minute_monitor.update({trading_day: TickMonitor.EMPTY})
                else:
                    minute_monitor.update({trading_day: TickMonitor.NORMAL})
        return minute_df, minute_monitor

    def load_third_tick_by_frame(self, start_date, end_date):
        '''
         从ThirdParty接口载入一段交易日中的所有Tick数据，并根据列进行筛选
         '''
        tick_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        # 交易日循环，对于TICK数据，接口支持最长查询为1天
        sub_tick_list = []
        for trading_day in trading_day_list:
            sub_start_date = trading_day
            sub_end_date = trading_day
            start_date_time = "{0}{1}".format(sub_start_date, "092500000")
            end_date_time = "{0}{1}".format(sub_end_date, "150000000")
            sub_tick_df = self.tma.getMDSecurityTickDataFrame(self.code, start_date_time, end_date_time, QueryType=1)
            # 对关键字段进行抽取并重命名
            if sub_tick_df.empty:
                sub_tick_df = pd.DataFrame(columns=INDEX_RAW_TICK_COLUMNS)
            else:
                sub_tick_df = sub_tick_df[INDEX_RAW_TICK_COLUMNS]
            sub_tick_list.append(sub_tick_df)
        tick_df = pd.concat(sub_tick_list, axis=0)

        if tick_df.empty:
            tick_df = pd.DataFrame(columns=INDEX_TARGET_TICK_COLUMNS)
            if self.monitor:
                tick_monitor.update({trading_day: TickMonitor.EMPTY for trading_day in trading_day_list})
        else:
            # 清洗，加入"Timestamp", "VolumeTrade", "ValueTrade"字段
            # 把全体数据加入"Timestamp"字段
            tick_df["Timestamp"] = (tick_df["MDDate"] + tick_df["MDTime"]).apply(
                lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            # 对每一天的数据计算
            daily_tick_df_list = []
            for trading_day in trading_day_list:
                daily_tick_df = tick_df[tick_df["MDDate"] == trading_day]
                daily_tick_df["VolumeTrade"] = daily_tick_df["TotalVolumeTrade"].diff(1)
                daily_tick_df["ValueTrade"] = daily_tick_df["TotalValueTrade"].diff(1)
                daily_tick_df_list.append(daily_tick_df)
                if self.monitor:
                    if daily_tick_df.empty:
                        tick_monitor.update({trading_day: TickMonitor.EMPTY})
                    else:
                        tick_monitor.update({trading_day: TickMonitor.NORMAL})
            tick_df = pd.concat(daily_tick_df_list, axis=0)
            tick_df = tick_df.reindex(columns=INDEX_CLEAN_TICK_COLUMNS)
            tick_df.columns = INDEX_TARGET_TICK_COLUMNS
        return tick_df, tick_monitor

    def load_third_transactions_by_frame(self, start_date, end_date):
        '''
        从ThirdParty接口载入标的一段交易日中的所有逐笔成交数据，并根据列进行筛选、清洗
        '''
        trading_day_list = Util.get_trading_day(start_date, end_date)
        # 对各个分组分别取数据
        sub_transactions_list = []
        for trading_day in trading_day_list:
            sub_start_date = trading_day
            sub_end_date = trading_day
            # 读取原始股票的逐笔数据
            start_date_time = "{0}{1}".format(sub_start_date, "092500000")
            end_date_time = "{0}{1}".format(sub_end_date, "150000000")
            sub_transactions_df = self.tma.getMDTransactionDataFrame(self.code, start_date_time, end_date_time)
            # 对关键字段进行抽取并重命名
            if sub_transactions_df.empty:
                sub_transactions_df = pd.DataFrame(columns=STOCK_RAW_TRANSACTIONS_COLUMNS)
            else:
                sub_transactions_df = sub_transactions_df[STOCK_RAW_TRANSACTIONS_COLUMNS]
            sub_transactions_list.append(sub_transactions_df)
        transactions_df = pd.concat(sub_transactions_list, axis=0)
        if transactions_df.empty:
            transactions_df = pd.DataFrame(columns=STOCK_TARGET_TRANSACTIONS_COLUMNS)
        else:
            ### Filter out cancelled item
            transactions_df = transactions_df[transactions_df['TradeType'] == 0]
            # 清洗，加入"Timestamp"字段
            transactions_df["Timestamp"] = (transactions_df["MDDate"] + transactions_df["MDTime"]).apply(lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            transactions_df = transactions_df.reindex(columns=STOCK_CLEAN_TRANSACTIONS_COLUMNS)
            transactions_df.columns = STOCK_TARGET_TRANSACTIONS_COLUMNS
        return transactions_df

    def load_future_daily_by_frame(self, start_date, end_date):
        """ 载入FUND一段交易日中的所有日频数据，并根据列进行筛选、清洗
        """
        daily_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)
        sub_daily_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "000000000")
            end_date_time = "{0} {1}".format(sub_end_date, "235900000")
            if self.future_contract_type is not None:
                sub_daily_df = self.ftd.get_future_data(self.code[:-2], start_date_time, end_date_time, "K_DAY",
                                                        contract_type=self.future_contract_type)
            else:
                sub_daily_df = self.ftd.get_future_data(self.code, start_date_time, end_date_time, "K_DAY")
            if sub_daily_df.empty:
                sub_daily_df = pd.DataFrame(columns=FUTURE_RAW_DAILY_COLUMNS)
            else:
                sub_daily_df = sub_daily_df[FUTURE_RAW_DAILY_COLUMNS]
            sub_daily_list.append(sub_daily_df)
        daily_df = pd.concat(sub_daily_list, axis=0)

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
                    this_daily_df = daily_df[daily_df['Date']==trading_day]
                    if this_daily_df.empty:
                        daily_monitor.update({trading_day: DailyMonitor.EMPTY})
                    else:
                        daily_monitor.update({trading_day: DailyMonitor.NORMAL})
        return daily_df, daily_monitor

    def load_future_minute_by_frame(self, start_date, end_date):
        """ 载入FUND一段交易日中的所有分钟数据，并根据列进行筛选、清洗、清洗
        """
        minute_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)
        sub_minute_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "000000000")
            end_date_time = "{0} {1}".format(sub_end_date, "235900000")
            if self.future_contract_type is not None:
                sub_minute_df = self.ftd.get_future_data(self.code[:-2], start_date_time, end_date_time, "K_1MIN",
                                                         contract_type=self.future_contract_type)
            else:
                sub_minute_df = self.ftd.get_future_data(self.code, start_date_time, end_date_time, "K_1MIN")
            if sub_minute_df.empty:
                sub_minute_df = pd.DataFrame(columns=FUTURE_RAW_MINUTE_COLUMNS)
            else:
                sub_minute_df = sub_minute_df[FUTURE_RAW_MINUTE_COLUMNS]
            sub_minute_list.append(sub_minute_df)
        minute_df = pd.concat(sub_minute_list, axis=0)

        if minute_df.empty:
            minute_df = pd.DataFrame(columns=FUTURE_TARGET_MINUTE_COLUMNS)
            minute_monitor.update({trading_day: MinuteMonitor.EMPTY for trading_day in trading_day_list})
        else:
            minute_df["Timestamp"] = (minute_df["MDDate"] + minute_df["MDTime"]).apply(lambda x: dt.datetime.strptime(x+"000", "%Y%m%d%H%M%S%f").timestamp())
            minute_df = minute_df.reindex(columns=FUTURE_CLEAN_MINUTE_COLUMNS)
            minute_df.columns = FUTURE_TARGET_MINUTE_COLUMNS
            minute_df[["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]] = minute_df[["OpenPrice", "ClosePrice", "HighPrice", "LowPrice"]].fillna(method='ffill')
            minute_df[["Volume", "Amount"]] = minute_df[["Volume", "Amount"]].fillna(0.)
            ###### 分钟数据处理，开盘集合竞价和收盘集合竞价数据剔除 ######
            minute_df.index = minute_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(int(x)))
            minute_df = minute_data_transform(minute_df, ["drop", "drop"])
            minute_df = minute_df.reindex(columns=FUTURE_TARGET_MINUTE_COLUMNS).reset_index(drop=True)
            for trading_day in trading_day_list:
                sub_minute_df = minute_df[minute_df['Date'] == trading_day]
                if sub_minute_df.empty:
                    if self.monitor:
                        minute_monitor.update({trading_day: MinuteMonitor.EMPTY})
                else:
                    if self.monitor:
                        minute_monitor.update({trading_day: MinuteMonitor.NORMAL})
        return minute_df, minute_monitor

    def load_future_tick_by_frame(self, start_date, end_date):
        """ 载入FUND一段交易日中的所有Tick数据，并根据列进行筛选
        """
        tick_monitor = {}
        trading_day_list = Util.get_trading_day(start_date, end_date)
        calc_time_groups = Util.split_calc_date_into_group(trading_day_list, THIRD_MAX_FRAME_LENGTH)
        sub_tick_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            start_date_time = "{0} {1}".format(sub_start_date, "000000000")
            end_date_time = "{0} {1}".format(sub_end_date, "235900000")
            if self.future_contract_type is not None:
                sub_tick_df = self.ftd.get_future_data(self.code[:-2], start_date_time, end_date_time, "TICK",
                                                       contract_type=self.future_contract_type)
            else:
                sub_tick_df = self.ftd.get_future_data(self.code, start_date_time, end_date_time, "TICK")
            if sub_tick_df.empty:
                sub_tick_df = pd.DataFrame(columns=FUTURE_RAW_TICK_COLUMNS)
            else:
                sub_tick_df = sub_tick_df[FUTURE_RAW_TICK_COLUMNS]
                if self.future_contract_type is not None:
                    sub_tick_df["HTSCSecurityID"] = self.code
                sub_tick_df = sub_tick_df.replace({'PreClosePx': 0.0}, np.nan)  # 如遇PreClose为0的，以前值填充之
                sub_tick_df = sub_tick_df.fillna(method='ffill')
                # 将连续竞价期间OpenPrice, HighPrice和LowPrice为0的条目删掉
                sub_tick_df = tickdata_OHL_filter(sub_tick_df)
            sub_tick_list.append(sub_tick_df)
        tick_df = pd.concat(sub_tick_list, axis=0)

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
                    daily_tick_df["VolumeTrade"] = daily_tick_df["TotalVolumeTrade"].diff()
                    daily_tick_df["ValueTrade"] = daily_tick_df["TotalValueTrade"].diff()
                    daily_tick_df.loc[0, "VolumeTrade"] = daily_tick_df.loc[0, "TotalVolumeTrade"]
                    daily_tick_df.loc[0, "ValueTrade"] = daily_tick_df.loc[0, "TotalValueTrade"]
                    daily_tick_df["VolumeTrade"] = daily_tick_df["VolumeTrade"].clip_lower(0)
                    daily_tick_df["ValueTrade"] = daily_tick_df["ValueTrade"].clip_lower(0)
                    daily_tick_df_list.append(daily_tick_df)
            tick_df = pd.concat(daily_tick_df_list, axis=0)
            tick_df = tick_df.reindex(columns=FUTURE_CLEAN_TICK_COLUMNS)
            tick_df.columns = FUTURE_TARGET_TICK_COLUMNS
        return tick_df, tick_monitor

    def load_daily_data(self, start_date, end_date):
        """ 获取股票/指数/可转债/FUND，一段日期日频数据
        """
        t1 = dt.datetime.now()
        if self.code_type == "STOCK":
            daily_df, daily_monitor = self.load_stock_daily_by_frame(start_date, end_date)
        elif self.code_type == "INDEX":
            if self.index_type == "ZZ":
                daily_df, daily_monitor = self.load_index_daily_by_frame(start_date, end_date)
            elif self.index_type == "SHENWAN":
                daily_df, daily_monitor = self.load_industry_daily_by_frame(start_date, end_date)
            elif self.index_type == "THIRD":
                daily_df, daily_monitor = self.load_third_daily_by_frame(start_date, end_date)
        elif self.code_type == "CBOND":
            daily_df, daily_monitor = self.load_cbond_daily_by_frame(start_date, end_date)
        elif self.code_type == "ETF" or self.code_type == "LOF":
            daily_df, daily_monitor = self.load_fund_daily_by_frame(start_date, end_date)
        elif self.code_type == "FUTURE":
            daily_df, daily_monitor = self.load_future_daily_by_frame(start_date, end_date)
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                daily_df, daily_monitor = self.load_industry_daily_by_frame(start_date, end_date)
            else:
                raise Exception("Not Supported Daily Data Yet For Industry Type: {}".format(self.indus_type))
        else:
            raise Exception("Not Supported Daily Data Yet: {}".format(self.code_type))
        t2 = dt.datetime.now()
        self.my_print("{} Load Daily Data Time Cost: {}, Data Size: {}".format(self.code, (t2 - t1).total_seconds(), daily_df.shape))
        return daily_df, daily_monitor

    def load_minute_data(self, start_date, end_date):
        """  获取股票/指数/可转债/FUND，一段日期分钟频数据
        """
        t1 = dt.datetime.now()
        if self.code_type == "STOCK":
            minute_df, minute_monitor = self.load_stock_minute_by_frame(start_date, end_date)
        elif self.code_type == "INDEX":
            if self.index_type == "ZZ":
                minute_df, minute_monitor = self.load_index_minute_by_frame(start_date, end_date)
            elif self.index_type == "SHENWAN":
                minute_df, minute_monitor = self.load_industry_minute_by_frame(start_date, end_date)
            elif self.index_type == "THIRD":
                minute_df, minute_monitor = self.load_third_minute_by_frame(start_date, end_date)
        elif self.code_type == "CBOND":
            minute_df, minute_monitor = self.load_cbond_minute_by_frame(start_date, end_date)
        elif self.code_type == "ETF" or self.code_type == "LOF":
            minute_df, minute_monitor = self.load_fund_minute_by_frame(start_date, end_date)
        elif self.code_type == "FUTURE":
            minute_df, minute_monitor = self.load_future_minute_by_frame(start_date, end_date)
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                minute_df, minute_monitor = self.load_industry_minute_by_frame(start_date, end_date)
            else:
                raise Exception("Not Supported Minute Data Yet For Industry Type: {}".format(self.indus_type))
        else:
            raise Exception("Not Supported Minute Data Yet: {}".format(self.code_type))
        t2 = dt.datetime.now()
        self.my_print("{}-{}-{} Load Minute Data Time Cost: {}, Data Size: {}".format(self.code, start_date, end_date,
                                                                           (t2 - t1).total_seconds(), minute_df.shape))
        return minute_df, minute_monitor

    def load_tick_data(self, start_date, end_date):
        """ 获取一只股票/指数/可转债/FUND，一段日期Tick频数据
        """
        t1 = dt.datetime.now()
        trading_day_list = Util.get_trading_day(start_date, end_date)
        if self.code_type == "STOCK":
            stock_tick_df, tick_monitor = self.load_stock_tick_by_frame(start_date, end_date)
            stock_transaction_df = self.load_stock_transactions_by_frame(start_date, end_date)
            ### 创业板股票TICK时间戳延迟特殊处理
            if 300000 <= int(self.code[0:6]) <= 399999:
                stock_tick_df, status_dict = self.__clean_GEMSecurities(stock_tick_df, stock_transaction_df, trading_day_list)
                tick_monitor.update(status_dict)
            tick_df = self.__align_tick_transaction_data(stock_tick_df, stock_transaction_df, trading_day_list, self.code_type)
        elif self.code_type == "INDEX":
            if self.index_type == "ZZ":
                index_tick_df, tick_monitor = self.load_index_tick_by_frame(start_date, end_date)
            elif self.index_type == "SHENWAN":
                index_tick_df, tick_monitor = self.load_industry_tick_by_frame(start_date, end_date)
            elif self.index_type == "THIRD":
                index_tick_df, tick_monitor = self.load_index_tick_by_frame(start_date, end_date)
            tick_df = self.__align_index_data(index_tick_df, trading_day_list)
        elif self.code_type == "CBOND":
            cbond_tick_df, tick_monitor = self.load_cbond_tick_by_frame(start_date, end_date)
            cbond_transaction_df = self.load_cbond_transactions_by_frame(start_date, end_date)
            tick_df = self.__align_tick_transaction_data(cbond_tick_df, cbond_transaction_df, trading_day_list, self.code_type)
        elif self.code_type == "ETF" or self.code_type == "LOF":
            etf_tick_df, tick_monitor = self.load_fund_tick_by_frame(start_date, end_date)
            etf_transaction_df = self.load_fund_transactions_by_frame(start_date, end_date)
            tick_df = self.__align_tick_transaction_data(etf_tick_df, etf_transaction_df, trading_day_list, self.code_type)
        elif self.code_type == "FUTURE":
            future_tick_df, tick_monitor = self.load_future_tick_by_frame(start_date, end_date)
            tick_df = self.__align_future_data(future_tick_df, trading_day_list)
        elif self.code_type == "INDUSTRY":
            if self.indus_type == "SHENWAN":
                tick_df, tick_monitor = self.load_industry_tick_by_frame(start_date, end_date)
                tick_df = self.__align_index_data(tick_df, trading_day_list)
            else:
                raise Exception("Not Supported Tick Data Yet For Industry Type: {}".format(self.indus_type))
        else:
            raise Exception("Not Supported Tick Data Yet: {}".format(self.code_type))
        t2 = dt.datetime.now()
        self.my_print("{}-{}-{} Load Tick Data Time Cost: {}, Data Size: {}".format(self.code, start_date, end_date,
                                                                            (t2 - t1).total_seconds(), tick_df.shape))
        return tick_df, tick_monitor

    def __clean_GEMSecurities(self, stock_tick_df, stock_transaction_df, trading_day_list):
        """ 清洗创业板股票，如果TICK和TRANSACTION成交额数据对不上，TICK数据延迟3S
        """
        status_dict = {}
        stock_tick_df_list = []
        for trading_day in trading_day_list:
            daily_stock_tick_df = stock_tick_df[stock_tick_df["Date"]==trading_day]
            daily_stock_transaction_df = stock_transaction_df[stock_transaction_df["Date"]==trading_day]
            if daily_stock_tick_df.empty:
                status = TickMonitor.EMPTY
            else:
                daily_stock_tick_df, status = daily_clean_GEMSecurities(trading_day, daily_stock_tick_df, daily_stock_transaction_df)
                self.my_print("GEM Stock Clean Status: {}-{}-{}".format(self.code, trading_day, status))
            status_dict.update({trading_day: status})
            stock_tick_df_list.append(daily_stock_tick_df)
        stock_tick_df_new = pd.concat(stock_tick_df_list, axis=0)
        return stock_tick_df_new, status_dict

    def __align_tick_transaction_data(self, stock_tick_df, stock_transaction_df, trading_day_list, code_type):
        """ 对齐股票/可转债/FUND Tick数据（整合逐笔成交数据）
        """
        aligned_daily_stock_tick_df_list = []
        for trading_day in trading_day_list:
            daily_stock_tick_df = stock_tick_df[stock_tick_df["Date"]==trading_day]
            daily_stock_transaction_df = stock_transaction_df[stock_transaction_df["Date"]==trading_day]
            del daily_stock_transaction_df["Date"]
            del daily_stock_transaction_df["Time"]
            if daily_stock_tick_df.empty or daily_stock_transaction_df.empty:
                continue
            else:
                self.my_print("Tick Transaction Alignment：{}-{}".format(self.code, trading_day))
                aligned_daily_stock_tick_df = daily_tick_transaction_align(trading_day, daily_stock_tick_df, daily_stock_transaction_df, code_type)
                aligned_daily_stock_tick_df_list.append(aligned_daily_stock_tick_df)
        if len(aligned_daily_stock_tick_df_list) != 0:
            aligned_stock_tick_df = pd.concat(aligned_daily_stock_tick_df_list, axis=0)
        else:
            if self.code_type == "STOCK":
                ALIGN_COLUMNS = ALIGN_STOCK_COLUMNS
            elif self.code_type == "CBOND":
                ALIGN_COLUMNS = ALIGN_CBOND_COLUMNS
            elif self.code_type == "ETF" or self.code_type == "LOF":
                ALIGN_COLUMNS = ALIGN_FUND_COLUMNS
            else:
                raise Exception("Not Supported Code Type Yet: {}".format(self.code_type))
            aligned_stock_tick_df = pd.DataFrame(columns=ALIGN_COLUMNS)
        return aligned_stock_tick_df

    def __align_index_data(self, index_tick_df, trading_day_list):
        """ 对齐指数Tick数据
        """
        aligned_daily_index_tick_df_list = []
        for trading_day in trading_day_list:
            daily_index_tick_df = index_tick_df[index_tick_df["Date"]==trading_day]
            if daily_index_tick_df.empty:
                continue
            else:
                self.my_print("Index Tick Alignment：{}-{}".format(self.code, trading_day))
                aligned_daily_index_tick_df = daily_index_align(trading_day, daily_index_tick_df)
                aligned_daily_index_tick_df_list.append(aligned_daily_index_tick_df)
        if len(aligned_daily_index_tick_df_list) != 0:
            aligned_index_tick_df = pd.concat(aligned_daily_index_tick_df_list, axis=0)
        else:
            aligned_index_tick_df = pd.DataFrame(columns=ALIGN_INDEX_COLUMNS)

        return aligned_index_tick_df

    def __align_future_data(self, future_tick_df, trading_day_list):
        """ 对齐指数Tick数据
        """
        aligned_daily_future_tick_df_list = []
        for trading_day in trading_day_list:
            daily_future_tick_df = future_tick_df[future_tick_df["Date"]==trading_day]
            if daily_future_tick_df.empty:
                continue
            else:
                self.my_print("Future Tick Alignment：{}-{}".format(self.code, trading_day))
                aligned_daily_future_tick_df = daily_future_align(trading_day, daily_future_tick_df)
                aligned_daily_future_tick_df_list.append(aligned_daily_future_tick_df)
        if len(aligned_daily_future_tick_df_list) != 0:
            aligned_future_tick_df = pd.concat(aligned_daily_future_tick_df_list, axis=0)
        else:
            aligned_future_tick_df = pd.DataFrame(columns=ALIGN_FUTURE_COLUMNS)

        return aligned_future_tick_df

    def my_print(self, x_str):
        if self.is_executor:
            remote_print(x_str)
        else:
            print(x_str)