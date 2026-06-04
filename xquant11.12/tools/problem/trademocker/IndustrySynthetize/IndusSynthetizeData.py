#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/3/2 17:12
from FactorDataTool.Config import INDUSTRY_TYPE
from DataInterface.Config import TICK_SUFFIX, INDEX_TARGET_TICK_COLUMNS, TICK_INDEX_HBASE_COLUMNS
from Utils.HelpFunc import my_print
from FactorDataTool.FDTool import FDTool
import os
import copy
import datetime as dt
import pandas as pd
import numpy as np
from xquant.factordata import FactorData

WEIGHT_COLUMNS = ["Weight", "Return"]
SLICE_COLUMNS_NAMES = ["Weight", "Return", "Volume", "Amount"]
BasePrice = 1000.


class IndusSynthetizeData:
    def __init__(self, library, indus_code, tick_play_lag=0):
        self.library = library
        self.indus_code = indus_code
        self.indus_type, self.indus = self.indus_code.split(".")
        assert self.indus_type in INDUSTRY_TYPE, "ONLY SUPPORT CITICS OR SW OR SHENWAN"

        self.tick_play_lag = tick_play_lag

        self.stock_list_dict = {}  ### 每个交易日成分股列表

        self.fa = FactorData()

        self.fd = FDTool(self.library)

    def synthetize_industry_tick_data(self, start_date, end_date):
        """ 获取一段交易日区间内行业指数合成数据 """
        my_print(" Start Synthetize Industry Tick Data: {}-{}-{} ".format(self.indus_code, start_date, end_date))

        t1 = dt.datetime.now()

        # 获取交易日列表, 每个交易日成分股列表字典和所有成分股集合, 前一日成分股权重信息
        trading_day_list = self.fa.tradingday(start_date, end_date)
        first_date = trading_day_list[0]
        pre_start_date = self.fa.tradingday(first_date, -2)[0]
        pre_trading_day_list = [pre_start_date] + trading_day_list[:-1]

        self.stock_list_dict, full_stock_list = self.get_constitute_stock_info(pre_trading_day_list, self.indus_code)

        if not full_stock_list:
            my_print("Empty Stock List: {}-{}-{}".format(self.indus_code, trading_day_list[0], trading_day_list[-1]))
            return pd.DataFrame(columns=INDEX_TARGET_TICK_COLUMNS + ["IsMock"])

        weight_df = self.load_weight_data(pre_trading_day_list, full_stock_list)

        # 生成初始空DataFrame
        fill_tick_df = self.get_fill_tick_data(trading_day_list, self.indus)

        indus_tick_df_list = []
        for pre_trading_day, trading_day in zip(pre_trading_day_list, trading_day_list):
            stock_list = self.stock_list_dict[pre_trading_day]
            daily_weight = weight_df.loc[pre_trading_day].loc[stock_list, "FreeFloatShares"]
            daily_fill_tick_df = fill_tick_df[fill_tick_df["Date"] == trading_day]
            daily_stock_tick_df_dict = self.load_stock_tick_df(trading_day, stock_list, daily_weight)
            if not daily_stock_tick_df_dict:
                sub_indus_tick_df = pd.DataFrame(columns=INDEX_TARGET_TICK_COLUMNS)
                my_print(" Empty Stock Data: {}-{} ".format(self.indus_code, trading_day))
            else:
                sub_indus_tick_df = self.synthetize_daily_tick_data(daily_fill_tick_df, daily_stock_tick_df_dict)
                if sub_indus_tick_df.empty:
                    sub_indus_tick_df = pd.DataFrame(columns=INDEX_TARGET_TICK_COLUMNS)
                    my_print(" Empty Synthetize Industry Data: {}-{} ".format(self.indus_code, trading_day))

            indus_tick_df_list.append(sub_indus_tick_df)

        if len(indus_tick_df_list) == 0:
            indus_tick_df = pd.DataFrame(columns=INDEX_TARGET_TICK_COLUMNS + ["IsMock"])
        else:
            indus_tick_df = pd.concat(indus_tick_df_list, axis=0)
            indus_tick_df["IsMock"] = 0

        t2 = dt.datetime.now()

        my_print(" {} Synthetize Industry Data Time Cost: {} ".format(self.indus_code, round((t2 - t1).total_seconds(),2)))

        return indus_tick_df

    def get_constitute_stock_info(self, trading_day_list, indus_code):
        """ 获取行业每个交易日成分股
        """
        stock_list_dict = dict()
        stock_list = []
        for trading_day in trading_day_list:
            # 获取行业成分股
            # indus_stock_list = self.fa.hset("INDUSTRY", trading_day, indus_code)["stock"].tolist()
            indus_stock_list = self.fd.hset("INDUSTRY", trading_day, indus_code)
            # 过滤掉当天不交易的股票
            if len(indus_stock_list)!=0:
                trade_status = self.fa.get_factor_value('Basic_factor', stock=indus_stock_list, mddate=[trading_day],
                                                        factor_names=["trade_status", "volume"])
                trade_status = trade_status.droplevel(1)
                trade_status.columns = ["TradeStatus", "Volume"]
                trade_status["TradeFlag"] = ((~trade_status["TradeStatus"].isnull())
                                                 & (trade_status["TradeStatus"] != "待核查")
                                                 & (trade_status["TradeStatus"] != "停牌")
                                                 & (trade_status["Volume"] != 0))
                valid_indus_stock_list = trade_status[trade_status["TradeFlag"] == True].index.tolist()
                if len(valid_indus_stock_list)!=0:
                    stock_list.extend(indus_stock_list)
                    stock_list_dict[trading_day] = indus_stock_list

        stock_list = list(set(stock_list))

        return stock_list_dict, stock_list

    @staticmethod
    def get_fill_tick_data(trading_day_list, indus):
        start_datetime_list = [dt.datetime.strptime(date + "093012", "%Y%m%d%H%M%S") for date in trading_day_list]
        datetime_list = []
        for start_datetime in start_datetime_list:
            datetime_list.extend(
                [start_datetime + dt.timedelta(seconds=3) * i for i in range(2396)]
                + [start_datetime + dt.timedelta(seconds=12603) + dt.timedelta(seconds=3) * i for i in range(2335)]
            )

        date_list = np.repeat(trading_day_list, 4731)
        time_list = [v.strftime("%H%M%S%f")[:-3] for v in datetime_list]
        timestamp_list = [v.timestamp() for v in datetime_list]
        fill_tick_df = pd.DataFrame(index=date_list, columns=INDEX_TARGET_TICK_COLUMNS)
        fill_tick_df["Code"] = indus
        fill_tick_df["Timestamp"] = timestamp_list
        fill_tick_df["Date"] = date_list
        fill_tick_df["Time"] = time_list
        fill_nan_columns = ["OpenPrice", "HighPrice", "LowPrice", "LastPrice", "Volume", "Amount", "TotalVolume",
                            "TotalAmount", "PreviousClose"]
        fill_tick_df.loc[:, fill_nan_columns] = [np.nan for _ in fill_nan_columns]
        fill_tick_df = fill_tick_df.reindex(columns=INDEX_TARGET_TICK_COLUMNS)

        return fill_tick_df

    def load_weight_data(self, pre_trading_day_list, full_stock_list):
        daily_df = self.fa.get_factor_value('Basic_factor', stock=full_stock_list, mddate=pre_trading_day_list,
                                       factor_names=["free_float_shares"])
        daily_df.columns = ["FreeFloatShares"]
        return daily_df

    def load_stock_tick_df(self, trading_day, stock_list, weight):
        """ HBASE中获取行业股票池的TICK数据
        """
        stock_tick_df_dict = {}
        ### 获取行业成分股TICK数据
        for stock in stock_list:
            stock_tick_df = self.get_stock_tick_data(stock, trading_day)
            if not stock_tick_df.empty:
                stock_tick_df["Weight"] = weight[stock] * stock_tick_df["LastPrice"]
                stock_tick_df["Return"] = stock_tick_df["LastPrice"].pct_change()
            else:
                stock_tick_df = pd.DataFrame(columns=stock_tick_df.columns.tolist() + WEIGHT_COLUMNS)
                my_print(" Empty Data: {}-{} ".format(stock, trading_day))
            stock_tick_df_dict[stock] = stock_tick_df

        return stock_tick_df_dict

    @staticmethod
    def get_stock_tick_midprice(bidPriceDf, askPriceDf, lastPriceDf):
        midPriceList = []
        for itick in range(0, bidPriceDf.shape[0]):
            bidPrice = bidPriceDf.loc[itick]
            askPrice = askPriceDf.loc[itick]
            if bidPrice is not None and askPrice is not None:
                midPrice = (bidPrice[0] + askPrice[0] ) / 2
            elif bidPrice is not None:
                midPrice = bidPrice[0]
            elif askPrice is not None:
                midPrice = askPrice[0]
            else:
                midPrice = lastPriceDf.iloc[itick]
            midPriceList.append(midPrice)
        return midPriceList

    def get_stock_tick_data(self, stock, date, map_col=True):
        '''获取HBase中某个股票历史某交易日的Tick频数据'''
        HBASE_COLUMNS = TICK_INDEX_HBASE_COLUMNS
        try:
            tick_df = self.fa.get_factor_value(self.library, stock, date, HBASE_COLUMNS)
        except:
            tick_df = pd.DataFrame(columns=HBASE_COLUMNS)
        if map_col:
            tick_df.columns = list(map(lambda x: x.replace("{0}_".format(TICK_SUFFIX), ""), tick_df.columns.to_list()))

        return tick_df

    def synthetize_daily_tick_data(self, fill_tick_df, stock_tick_df_dict):
        # 保存每个股票时间戳信息
        timestamp_dict = dict()
        for stock, stock_tick_df in stock_tick_df_dict.items():
            if stock_tick_df.empty:
                timestamp_dict[stock] = np.array([])
            else:
                timestamp_dict[stock] = stock_tick_df["Timestamp"].values

        daily_indus_df = copy.deepcopy(fill_tick_df).reset_index(drop=True)
        daily_indus_df["Return"] = np.nan

        # 定位每个股票当前时间戳
        curr_index_dict = dict()
        for tick, this_tick_timestamp in enumerate(daily_indus_df["Timestamp"]):
            curr_slice_dict = dict()  # 保存当前TICK所有股票数据信息
            curr_slice_data = {var: [] for var in SLICE_COLUMNS_NAMES}
            for stock in timestamp_dict:
                tick_curr_index = curr_index_dict.get(stock, 0)   # 默认Index从0开始
                tick_timestamp_array = timestamp_dict[stock]
                while (tick_curr_index < tick_timestamp_array.shape[0]
                       and tick_timestamp_array[tick_curr_index] <= this_tick_timestamp - self.tick_play_lag):
                    tick_curr_index += 1
                if tick_curr_index < 1:  # 当天股票TICK数据为空
                    continue
                curr_index_dict[stock] = tick_curr_index - 1
                curr_slice_dict[stock] = stock_tick_df_dict[stock].iloc[curr_index_dict[stock]]
                for var in SLICE_COLUMNS_NAMES:
                    curr_slice_data[var].append(curr_slice_dict[stock][var])

            ret, volume, amount = self.synthetize_stock_slice_data(curr_slice_data)

            daily_indus_df.loc[tick, "Volume"] = volume
            daily_indus_df.loc[tick, "Amount"] = amount
            daily_indus_df.loc[tick, "Return"] = ret

        daily_indus_df["LastPrice"] = BasePrice * (1. + daily_indus_df["Return"]).cumprod()
        daily_indus_df["TotalVolume"] = daily_indus_df["Volume"].cumsum()
        daily_indus_df["TotalAmount"] = daily_indus_df["Amount"].cumsum()
        daily_indus_df = daily_indus_df.reindex(columns=INDEX_TARGET_TICK_COLUMNS)

        return daily_indus_df

    @staticmethod
    def synthetize_stock_slice_data(slice_dict):
        if not slice_dict:
            return np.nan, np.nan, np.nan

        weight = slice_dict["Weight"] / np.nansum(slice_dict["Weight"])
        ret = np.nansum(slice_dict["Return"] * weight)
        volume = np.nansum(slice_dict["Volume"])
        amount = np.nansum(slice_dict["Amount"])

        return ret, volume, amount


if __name__ == "__main__":
    lib_name = "XHFDataLib"
    indus_code = "CITICS.b10l02"
    start_date = "20180817"
    end_date = "20180817"
    instance = IndusSynthetizeData(lib_name, indus_code)
    indus_tick_df = instance.synthetize_industry_tick_data(start_date, end_date)
    indus_tick_df.to_pickle("/data/user/015629/MISC/indus_tick_df.pkl")










