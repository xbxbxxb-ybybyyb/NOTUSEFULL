#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/4/9 19:24
# 根据每天所给组合，生成需要补充参数的股票列表
import os
import shutil
import pandas as pd
from xquant.factordata import FactorData

PARAMS_FILE_COLUMNS = ["symbol",  "shortTriggerRatio", "shortCloseRatio", "shortRiskRatio", "longTriggerRatio",
                       "longCloseRatio", "longRiskRatio"]
PARAMS_LOCAL_PATH = "/data/user/015629/EasyInferSignal/portfolioInfo/"
T0_PORTFOLIO_PATH = "/data/user/011477/order/T0/T0_CV_Split/"


class DailyLiveStockList(object):
    """"""
    def __init__(self, next_trading_day, change_pct=0.2, small_model=False):
        self.next_trading_day = next_trading_day
        self.change_pct = change_pct
        self.small_model = small_model
        self.fa = FactorData()
        self.last_trade_date = self.fa.tradingday(self.next_trading_day, -2)[0]
        print(" Last Trade Date: {}, Next Trade Date: {}".format(self.last_trade_date, self.next_trading_day))

    def get_live_stock_list(self):
        """"""
        existing_valid_param_stock_list = self.get_existing_valid_param_stock_list()

        last_date_portfolio_info = self.get_live_portfolio_info(self.last_trade_date)
        live_portfolio_info = self.get_live_portfolio_info(self.next_trading_day)
        last_date_stock_list = last_date_portfolio_info["证券代码"].tolist()
        live_stock_list = live_portfolio_info["证券代码"].tolist()
        not_valid_param_stock_list = list(set(live_stock_list).difference(existing_valid_param_stock_list))
        print(" Last Date Stock Num: {}, Next Date Stock Num: {} ".format(len(last_date_stock_list), len(live_stock_list)))

        concat_portfolio = pd.merge(last_date_portfolio_info, live_portfolio_info, on="证券代码", how="outer").fillna(1.)
        concat_portfolio = concat_portfolio[concat_portfolio["证券代码"].isin(live_stock_list)]
        concat_portfolio["ChangePct"] = (concat_portfolio["证券额度_y"] / concat_portfolio["证券额度_x"] - 1.).abs()
        add_stock_list = concat_portfolio[concat_portfolio["ChangePct"] >= self.change_pct]["证券代码"].tolist()

        # 额度变动超过20%的标的 + 无效参数的标的
        net_add_stock_list = sorted(list(set(add_stock_list).union(not_valid_param_stock_list)))
        if self.small_model:
            small_model_list = os.listdir("/data/user/015629/chensf/Easy_20201001/")
            net_add_stock_list = sorted(list(set(net_add_stock_list).intersection(small_model_list)))
        print(" Net Add Stock Num: {} ".format(len(net_add_stock_list)))

        return live_stock_list, net_add_stock_list

    def get_existing_valid_param_stock_list(self):
        paramter_str = "parameters_small/" if self.small_model else "parameters/"
        local_path = os.path.join(PARAMS_LOCAL_PATH, paramter_str)
        if not os.path.exists(local_path):
            os.makedirs(local_path)
        param_file_name = os.path.join(local_path, "easy_live_params.csv")
        valid_stock_list = []
        if os.path.exists(param_file_name):
            params_df = pd.read_csv(param_file_name).dropna(how='any', axis=0)
            params_df.columns = PARAMS_FILE_COLUMNS
            params_df = params_df[~(params_df["longTriggerRatio"] == 999999)]
            valid_stock_list = params_df["symbol"].tolist()
        print(" Existing Valid Param Stock Num: {} ".format(len(valid_stock_list)))
        return valid_stock_list

    @staticmethod
    def get_live_portfolio_info(date, portfolio="easy"):
        local_path = os.path.join(PARAMS_LOCAL_PATH, "portfolios")
        if not os.path.exists(local_path):
            os.makedirs(local_path)
            
        file_name = "{}_{}.xlsx".format(date, portfolio)
        remote_file = T0_PORTFOLIO_PATH + date + "/" + file_name
        all_file_name = "{}_{}.xlsx".format(date, portfolio)
        all_file = T0_PORTFOLIO_PATH + date + "/" + all_file_name
        if os.path.exists(all_file):
            remote_file = all_file
            
        port_file_name = os.path.join(local_path, file_name)
        if not os.path.exists(port_file_name):
            shutil.copyfile(remote_file, port_file_name)

        port_df = pd.read_excel(port_file_name)
        port_df = port_df[["证券代码", "证券额度"]]
        return port_df


if __name__=="__main__":
    next_trading_day = "20210409"
    change_pct = 0.2
    small_model = False
    dls = DailyLiveStockList(next_trading_day, change_pct, small_model)
    live_stock_list, net_add_stock_list = dls.get_live_stock_list()








