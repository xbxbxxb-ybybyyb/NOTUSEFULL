#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/14 8:52
import os
import pandas as pd
from xquant.xqutils.xqfile import FTPFile
from xquant.factordata import FactorData

CBOND_LIVE_PATH = "/data/user/666888/WuKong/CBondLiveStat/DailyReturnFiles/"
LIVE_RET_LOOKBACK_PORTFOLIO = "/data/user/666888/WuKong/CbondPoolManagement/LiveRetLookBack/"

class CBondLiveRetLookBack:
    """"""
    def __init__(self, lookback=5, start_date=None, window=None, save=False):
        today_str = "20201015"
        self.today_str = today_str
        self.lookback = lookback

        self.fa = FactorData()
        self.start_date = start_date
        self.window = window
        self.save = save

        self.next_trading_day = self.fa.tradingday(self.today_str, 2)[-1]
        if self.start_date is None:
            if self.window is None:
                self.date_list = self.fa.tradingday(self.today_str, -self.lookback)
            else:
                self.date_list = self.fa.tradingday(self.today_str, -self.window)
        else:
            if self.window is None:
                self.date_list = self.fa.tradingday(self.start_date, self.today_str)
            else:
                new_start_date = self.fa.tradingday(self.start_date, -self.window)[0]
                self.date_list = self.fa.tradingday(new_start_date, self.today_str)

        print(" Target Date: {}, LookBack Date List: {} ".format(self.today_str, self.date_list))

        self.download_cbond_live_file_from_ftp()

    def download_cbond_live_file_from_ftp(self):
        if not os.path.exists(CBOND_LIVE_PATH):
            os.makedirs(CBOND_LIVE_PATH)

        ftp = FTPFile()
        for date in self.date_list:
            file_name = "{}_T0_CB.xlsx".format(date)
            local_path = os.path.join(CBOND_LIVE_PATH, file_name)
            if not os.path.exists(local_path):
                print(" Start Download CBond Live File From FTP: {} ".format(date))
                ftp.downloadFile("516/ConverBond_T0/" + file_name, local_path)

    @staticmethod
    def convert_cbond_code(int_code):
        cbond = str(int_code).zfill(6)
        if cbond.startswith("11"):
           cbond = cbond + ".SH"
        elif cbond.startswith("12"):
            cbond = cbond + ".SZ"
        return cbond

    def get_cbond_live_daily_ret_file(self, date):
        file_name = os.path.join(CBOND_LIVE_PATH, "{}_T0_CB.xlsx".format(date))
        if not os.path.exists(file_name):
            print(" CBond Live Return File Not Exists: {} ".format(date))
            return pd.DataFrame()
        ret_df = pd.read_excel(file_name, sheet_name="组合证券")
        ret_df["证券代码"] = ret_df["证券代码"].apply(lambda x: self.convert_cbond_code(x))
        ret_df["日期"] = str(date)
        return ret_df

    def get_cbond_live_return(self):
        daily_ret_df_list = []
        for date in self.date_list:
            daily_ret_df_list.append(self.get_cbond_live_daily_ret_file(date))
        ret_df = pd.DataFrame()
        if len(daily_ret_df_list) > 0:
            ret_df = pd.concat(daily_ret_df_list, axis=0)
        return ret_df

    def cbond_daily_return_stat(self):
        """"""
        daily_df = self.get_cbond_live_return()

        daily_stat_dict = {}
        for cbond, cbond_df in daily_df.groupby("证券代码"):
            df = cbond_df.sort_values(by=["日期"]).set_index("日期").iloc[-self.lookback:]
            start_date = df.index.tolist()[0]
            end_date = df.index.tolist()[-1]
            name = df["证券名称"].iloc[0]
            profit = df["盈利"].sum()
            win_ratio = df[df["盈利"] > 0].shape[0] / df.shape[0]
            trade_amount = df["交易金额"].sum()
            ret = df["收益率"].mean()
            trade_num = df["交易次数"].sum()
            trade_dates = df.shape[0]
            price = df["最新价"].iloc[-1]
            daily_stat_dict.update({cbond: {
                "证券代码": cbond,
                "证券名称": name,
                "盈利": profit,
                "日胜率": win_ratio,
                "交易金额": trade_amount,
                "收益率": ret,
                "交易次数": trade_num,
                "交易天数": trade_dates,
                "最新价": price,
                "有效开始日期": start_date,
                "有效结束日期": end_date
            }})

        daily_stat = pd.DataFrame(daily_stat_dict).T
        daily_stat = daily_stat.reindex(columns=["证券代码", "证券名称", "盈利", "日胜率", "交易金额", "收益率",
                                                 "交易次数", "交易天数", "最新价", "有效开始日期", "有效结束日期"])

        win_ratio_less_20 = daily_stat[daily_stat["日胜率"] < 0.2]["证券代码"].tolist()
        win_ratio_between_24 = daily_stat[(daily_stat["日胜率"] >= 0.2) & (daily_stat["日胜率"] < 0.4)]["证券代码"].tolist()
        win_ratio_larger_40 = daily_stat[daily_stat["日胜率"] >= 0.4]["证券代码"].tolist()
        win_ratio_filter = pd.DataFrame([win_ratio_less_20, win_ratio_between_24, win_ratio_larger_40]).T
        win_ratio_filter.columns = ["LT20", "20BT40", "GT40"]

        if self.save:
            local_path = os.path.join(LIVE_RET_LOOKBACK_PORTFOLIO, "{}".format(self.next_trading_day))
            if not os.path.exists(local_path):
                os.makedirs(local_path)

            file_name = os.path.join(local_path, "WuKongRet_{}.xlsx".format(self.next_trading_day))
            daily_stat.to_excel(file_name, index=None)

            file_name = os.path.join(local_path, "WuKongRetFilter_{}.xlsx".format(self.next_trading_day))
            win_ratio_filter.to_excel(file_name, index=None)

        return daily_stat


if __name__ == "__main__":
    lookback = 5
    start_date = None
    window = 20
    save = True
    instance = CBondLiveRetLookBack(lookback=5, start_date=start_date, window=window, save=save)
    daily_stat = instance.cbond_daily_return_stat()
    print(daily_stat.head())


