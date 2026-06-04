#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/11/17 16:11
import pandas as pd
from DataIO.Utils import get_trading_day, get_code_type
from xquant.factordata import FactorData


class StaticInfo(object):
    def __init__(self, code, start_date, end_date):
        self.code = code
        self.code_type = get_code_type(self.code)
        self.start_date = start_date
        self.end_date = end_date
        self.fa = FactorData()

        self.valid_date_list, self.pre_close_dict = self.load_static_info()

    def load_static_info(self):
        """"""
        trading_day_list = get_trading_day(self.start_date, self.end_date)

        if self.code_type == "STOCK":
            daily_df = self.fa.get_factor_value('Basic_factor', stock=[self.code], mddate=trading_day_list,
                                       factor_names=["pre_close", "trade_status", "volume"])
            daily_df = daily_df[(~daily_df["trade_status"].isnull()) & (daily_df["trade_status"] != "待核查") &
                                (daily_df["trade_status"] != "停牌") & (daily_df["volume"] != 0)]
        elif self.code_type == "CBOND":
            daily_df = self.fa.get_factor_value('Basic_factor', stock=[self.code], mddate=trading_day_list,
                                       factor_names=["pre_close", "trade_status", "volume"], category="bond")
            daily_df = daily_df[(~daily_df["trade_status"].isnull()) & (daily_df["trade_status"] != "待核查") &
                                (daily_df["trade_status"] != "停牌") & (daily_df["trade_status"] != "0") &
                                (daily_df["volume"] != 0)]
        if daily_df.empty:
            daily_df = pd.DataFrame(columns=["date", "pre_close"])
        else:
            daily_df = daily_df.droplevel(1).dropna()
            daily_df["date"] = list(map(str, list(daily_df.index)))

        valid_date_list = sorted(list(set(daily_df["date"].tolist())))
        pre_close_dict = daily_df.set_index("date")["pre_close"].to_dict()

        return valid_date_list, pre_close_dict

    def load_valid_dates(self):
        return self.valid_date_list

    def load_pre_close_dict(self):
        return self.pre_close_dict