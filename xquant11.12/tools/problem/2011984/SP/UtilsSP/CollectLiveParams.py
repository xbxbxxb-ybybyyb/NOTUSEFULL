#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/11/12 10:26
import os
import json
import pandas as pd
from xquant.factordata import FactorData
EVEREST_LOCAL_PATH = "/data/user/015629/Easy/productionParams/"
# EVEREST_DST_PATH = "/data/user/015629/MISC/LiveParams/"
EVEREST_DST_PATH = "/data/user/011668/SP_Data/SP_Params/LiveParams"


class CollectLiveParams(object):
    def __init__(self, strategy, start_date, end_date, save=True, save_path=""):
        self.strategy = strategy
        self.start_date = start_date
        self.end_date = end_date
        self.save = save
        self.save_path = save_path
        if self.strategy == "Everest":
            self.local_path = EVEREST_LOCAL_PATH
            self.dir_prefix = "Easy"
            self.portfolio_prefix = "easy"
        else:
            pass

        self.fa = FactorData()
        self.date_list = self.fa.tradingday(self.start_date, self.end_date)

    def run(self):
        """"""
        for date in self.date_list:
            strategy_save_path = os.path.join(os.path.join(self.save_path, self.strategy), "{}_{}".format(self.dir_prefix, date))
            if os.path.exists(strategy_save_path):
                print('Everest Portfolio File Exist')
                return
            date_portfolio_paths = [path for path in os.listdir(self.local_path) if "{}_{}".format(self.dir_prefix, date) in path]
            print(" {} - {} Have {} Live Portfolio Dir: {} ".format(self.strategy, date, len(date_portfolio_paths), date_portfolio_paths))

            # Collect Date Live Params
            collect_json_params_dict, collect_portfolio_file_dict, collect_portfolio_no_list = dict(), dict(), []
            for portfolio_path in date_portfolio_paths:
                local_portfolio_path = os.path.join(self.local_path, portfolio_path)
                json_param_dict, portfolio_file_dict, portfolio_no_list = self.get_live_params_and_portfolio(date, self.portfolio_prefix, local_portfolio_path)
                collect_json_params_dict.update(json_param_dict)
                collect_portfolio_file_dict.update(portfolio_file_dict)

                replicated_portfolio_no_list = sorted(set(collect_portfolio_no_list).intersection(portfolio_no_list))
                if len(replicated_portfolio_no_list) > 0:
                    raise Exception(" {} - {} Replicated Portfolios: {} ".format(self.strategy, portfolio_path, replicated_portfolio_no_list))

            print(" {} - {} Have {} Portfolios, {} Codes ".format(self.strategy, date, len(collect_portfolio_file_dict.keys()), len(collect_json_params_dict.keys())))

            if self.save:
                strategy_save_path = os.path.join(os.path.join(self.save_path, self.strategy), "{}_{}".format(self.dir_prefix, date))
                os.makedirs(strategy_save_path, exist_ok=True)
                for symbol, json_params in collect_json_params_dict.items():
                    json_save_path = os.path.join(strategy_save_path, "JsonParam")
                    os.makedirs(json_save_path, exist_ok=True)
                    save_file_name = os.path.join(json_save_path, "{}.json".format(symbol))
                    with open(save_file_name, "w+", encoding="UTF-8") as f:
                        json.dump(json_params, f, ensure_ascii=False, indent=4)
                        f.close()

                for portfolio_file_name, portfolio_df in collect_portfolio_file_dict.items():
                    save_file_name = os.path.join(strategy_save_path, portfolio_file_name)
                    portfolio_df.to_excel(save_file_name, index=False)

            print(" Strategy {} Collect Live Params Done: {} ".format(self.strategy, date))

    @staticmethod
    def get_live_params_and_portfolio(date, portfolio_prefix, local_portfolio_path):
        json_param_path = os.path.join(local_portfolio_path, "JsonParam")
        json_file_list = os.listdir(json_param_path)
        json_param_dict = dict()
        for json_file in json_file_list:
            symbol = json_file[:-5]
            json_file_path = os.path.join(json_param_path, json_file)
            with open(json_file_path, "rb") as f:
                data = f.read()
                data = json.loads(data)
            json_param_dict.update({symbol: data})

        portfolio_no_list = []
        portfolio_file_dict = dict()
        portfolio_files = [file for file in os.listdir(local_portfolio_path) if file.startswith(portfolio_prefix) and file.endswith(".xlsx")]
        if len(portfolio_files) == 0:
            print(" No Portfolio File Exists: {} ".format(local_portfolio_path))
        else:
            for portfolio_file_name in portfolio_files:
                portfolio, trade_date = portfolio_file_name.split("_")[1], portfolio_file_name.split("_")[-1].split(".")[0]
                assert trade_date == date, " Portfolio Date {} Not Today {}".format(trade_date, date)
                portfolio_no_list.append(portfolio)
                portfolio_df = pd.read_excel(os.path.join(local_portfolio_path, portfolio_file_name))
                portfolio_file_dict.update({portfolio_file_name: portfolio_df})

            assert len(portfolio_no_list) == len(set(portfolio_no_list)), " Replicated Portfolio File Exists: {} ".format(local_portfolio_path)

        return json_param_dict, portfolio_file_dict, portfolio_no_list


if __name__ == "__main__":
    strategy = "Everest"
    start_date = "20211111"
    end_date = "20211112"
    save = True
    save_path = EVEREST_DST_PATH
    clp = CollectLiveParams(strategy, start_date, end_date, save, save_path)
    clp.run()



