#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/4/9 20:43
import os
import json
import numpy as np
import pandas as pd
from xquant.xqutils.xqfile import HDFSFile
from xquant.factordata import FactorData
from CV_NEW.GetHighVol import get_high_vol_speed
from ScheduledTask.DailyLiveStockList import DailyLiveStockList

PARAMS_FILE_COLUMNS = ["symbol", "shortTriggerRatio", "shortCloseRatio", "shortRiskRatio", "longTriggerRatio",
                       "longCloseRatio", "longRiskRatio"]
LIVE_PARAMS_COLUMNS = ["symbol", "shortTriggerRatio", "shortCloseRatio", "shortRiskRatio", "longTriggerRatio",
                       "longCloseRatio", "longRiskRatio", "OrderCapacity", "perOrderAmountLimit", "HighVol"]
PARAMS_LOCAL_PATH = "/data/user/015629/EasyInferSignal/portfolioInfo/"


class GenerateLiveParams(object):
    """"""
    def __init__(self, cv_start_date, cv_end_date, next_trading_day, portfolio="easy", pct_change=0.2, lookback=20,
                 init_amount=int(5e8), small_model=False, signal_csv_dir="Everest20210201_20210515", executor_str="SignalExecutorEasy",
                 overwrite_params={'maxTurnoverPerOrder': 1800000, 'maxExposure': 8000000},
                 hdfs_root="cv/Stock/Results/", save=True):

        self.cv_start_date = cv_start_date
        self.cv_end_date = cv_end_date
        self.next_trading_day = next_trading_day
        self.portfolio = portfolio
        self.pct_change = pct_change
        self.lookback = lookback
        self.init_amount = init_amount
        self.small_model = small_model
        self.signal_csv_dir = signal_csv_dir
        self.executor_str = executor_str
        self.overwrite_params = overwrite_params
        self.hdfs_root = hdfs_root
        self.save = save

        self.result_dir_name = 'cv-{}-{}_{}-{}-{}-{}-{}-{}-{}/'.format(self.cv_start_date, self.cv_end_date, self.next_trading_day, self.portfolio,
                                                                       self.signal_csv_dir, self.executor_str, self.init_amount,
                                                                       str(self.overwrite_params["maxTurnoverPerOrder"] // 10000),
                                                                       str(self.overwrite_params["maxExposure"] // 10000))
        self.output_dir = os.path.join(self.hdfs_root, self.result_dir_name)

        self.dls = DailyLiveStockList(self.next_trading_day, self.pct_change, self.small_model)
        self.live_stock_list, self.net_add_stock_list = self.dls.get_live_stock_list()
        self.last_trade_date = self.dls.last_trade_date
        parameter_str = "parameters_small/" if self.small_model else "parameters/"
        self.local_param_path = os.path.join(PARAMS_LOCAL_PATH, parameter_str)

    def generate_live_params(self):
        """"""
        # Step 1: Load Existing Params
        valid_existing_param_df = self.get_valid_existing_params_df()
        new_param_df = self.load_live_params_from_cv()

        new_invalid_stock_list = new_param_df[new_param_df["longTriggerRatio"] == 999999]["symbol"].tolist()
        existing_valid_stock_list = valid_existing_param_df[valid_existing_param_df["longTriggerRatio"] != 999999]["symbol"].tolist()
        net_add_stock_list = list(set(self.net_add_stock_list).difference(set(new_invalid_stock_list).intersection(existing_valid_stock_list)))

        sub_existing_param_df = valid_existing_param_df[~valid_existing_param_df["symbol"].isin(net_add_stock_list)]
        concat_params_df = sub_existing_param_df.append(new_param_df[new_param_df["symbol"].isin(net_add_stock_list)])
        concat_params_df = concat_params_df.sort_values(by=["symbol"]).reset_index(drop=True)

        # Generate High Vol and OrderCapacity
        print(" Generate High Vol and OrderCapacity ")
        order_param_info = self.get_order_params_info()

        live_param_df = pd.merge(concat_params_df, order_param_info, on="symbol")
        live_param_df = live_param_df.reindex(columns=LIVE_PARAMS_COLUMNS)

        if self.save:
            existing_file_name = self.local_param_path + "easy_live_params_valid_exist.csv"
            valid_existing_param_df.to_csv(existing_file_name, index=None)

            concat_file_name = self.local_param_path + "easy_live_params.csv"
            concat_params_df.to_csv(concat_file_name, index=None)

            live_file_name = self.local_param_path + "easy_live_params_{}.csv".format(self.next_trading_day)
            live_param_df.to_csv(live_file_name, index=None)

        print(" Live Parameters File Generated Done: {} ".format(self.next_trading_day))

    def get_valid_existing_params_df(self):
        if not os.path.exists(self.local_param_path):
            os.makedirs(self.local_param_path)
        param_file_name = os.path.join(self.local_param_path, "easy_live_params.csv")
        if os.path.exists(param_file_name):
            params_df = pd.read_csv(param_file_name).dropna(how='any', axis=0)
            params_df = params_df[~(params_df["longTriggerRatio"] == 999999)]
            params_df.columns = PARAMS_FILE_COLUMNS
        else:
            params_df = pd.DataFrame(columns=PARAMS_FILE_COLUMNS)
        return params_df

    def load_live_params_from_cv(self):
        print(" Load Live Trigger Parameters From CV ")
        hf = HDFSFile()
        triggers = {}
        invalid_params_stock_list = []
        for stock in self.net_add_stock_list:
            trigger_file = self.output_dir + "{}/triggerRatio.json".format(stock)
            if hf.exists(trigger_file):
                with hf.open(trigger_file, "rb") as f:
                    data = f.read()
                    trigger_dict = json.loads(data)
            else:
                trigger_dict = {}
                trigger_dict["shortTriggerRatio"] = -999999
                trigger_dict["shortCloseRatio"] = 0
                trigger_dict["shortRiskRatio"] = 0.2
                trigger_dict["longTriggerRatio"] = 999999
                trigger_dict["longCloseRatio"] = 0
                trigger_dict["longRiskRatio"] = -0.2

                invalid_params_stock_list.append(stock)

            triggers[stock] = trigger_dict

        print(" Missing Params Stock List: {}, {} ".format(len(invalid_params_stock_list), invalid_params_stock_list))

        live_param_df = pd.DataFrame(triggers).T
        live_param_df["symbol"] = live_param_df.index
        live_param_df = live_param_df.reindex(columns=PARAMS_FILE_COLUMNS).reset_index(drop=True)

        return live_param_df

    def get_order_params_info(self):
        high_vol_dict = get_high_vol_speed("ZeusDataLib", self.live_stock_list, self.last_trade_date,
                                           self.last_trade_date, lookback=self.lookback)
        high_vol = {stock: high_vol_dict[stock].get(self.last_trade_date, 0.) for stock in self.live_stock_list}
        mean_volume = self.get_daily_mean_volume(self.live_stock_list, self.last_trade_date, self.lookback)
        order_df = pd.DataFrame({"HighVol": high_vol, "MeanVolume": mean_volume})
        order_df["symbol"] = order_df.index
        order_df["OrderCapacity"] = order_df["MeanVolume"] / 100 * 0.2
        order_df["perOrderAmountLimit"] = order_df["OrderCapacity"] / 100
        return order_df

    @staticmethod
    def get_daily_mean_volume(stock_list, date, lookback=20):
        fa = FactorData()
        date_list = fa.tradingday(date, -(lookback * 2))
        volume = fa.get_factor_value("Basic_factor", stock_list, date_list, ["volume"]).unstack()["volume"] * 100
        volume_slice = volume.iloc[-lookback:]
        mean_volume_dict = volume_slice.mean().to_dict()
        for stock in stock_list:
            if stock not in mean_volume_dict:
                mean_volume_dict.update({stock: 0})
            else:
                if pd.isnull(mean_volume_dict[stock]):
                    mean_volume_dict.update({stock: 0})
        return mean_volume_dict

def run_live():
    cv_start_date = "20210719"
    cv_end_date = "20210917"
    next_trading_day = "20210924"
    portfolio = "easy"
    pct_change = 0.2
    # lookback = 20
    # initialAmount = int(5e8)
    # executor_str = "SignalExecutorEasy"
    # overwrite_params = {'maxTurnoverPerOrder': 1800000, 'maxExposure': 8000000}
    # hdfs_root = "cv/Stock/Results/"
    # save = True

    small_model = False
    signal_csv_dir = "Everest20210201_20210515"
    glp = GenerateLiveParams(cv_start_date=cv_start_date, cv_end_date=cv_end_date, next_trading_day=next_trading_day,
                             portfolio=portfolio, pct_change=pct_change, small_model=small_model, signal_csv_dir=signal_csv_dir)
    glp.generate_live_params()


#    small_model = True
#    signal_csv_dir = "Easy_20201001"
#    glp = GenerateLiveParams(cv_start_date=cv_start_date, cv_end_date=cv_end_date, next_trading_day=next_trading_day,
#                             portfolio=portfolio, pct_change=pct_change, small_model=small_model, signal_csv_dir=signal_csv_dir)
#    glp.generate_live_params()


if __name__ == "__main__":
    run_live()






