#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/7/30 13:10
import os
import shutil
import datetime as dt
import numpy as np
import pandas as pd
from ScheduledTask.getPredictionSignal import get_signal_corr
from ScheduledTask.FTPDownloadDir import FTP_OP
from xquant.factordata import FactorData
fa = FactorData()

COLLECT_RETUEN_PATH = "/data/user/015629/Easy/CollectReturnStat/"
LIVE_BT_CMP_PATH = "/data/user/015629/Easy/LiveBTCompare/"
BT_RESULT_PATH = "/data/user/015629/BT_Results/Stock/results/"
RESULT_DAILY_COLUMNS = ['总盈利', '交易总市值', '交易次数', '获利次数', '胜率',  '盈亏比',  '平均收益率',
                        '市值收益率', '获利收益率', '亏损收益率',  '最大单笔亏损', '平均持仓时间']

def convert_win_ratio(win_ratio):
    if isinstance(win_ratio, str):
        win_ratio = float(win_ratio)
    win_ratio = int(round(win_ratio * 100, 0))
    win_ratio = "{}%".format(win_ratio)
    return win_ratio

def convert_holding_time(h_time):
    hour = str(int(h_time) // 60)
    minute = str(int(h_time)- int(hour) * 60)
    second = str(int((np.float(h_time) - int(h_time)) * 60))
    h_time = "{}:{}:{}".format(hour, minute ,second)
    return h_time

def convert_live_code(code):
    code = str(code).zfill(6)
    if code[0] == '6':
        return code + '.SH'
    else:
        return code + '.SZ'

class CollectEasyTrackResult:
    """"""
    def __init__(self, today_str, cv_start_date, cv_end_date, cv_param_date):
        self.today_str = today_str
        self.cv_start_date = cv_start_date
        self.cv_end_date = cv_end_date
        self.cv_param_date = cv_param_date

        self.bt_research_path = self.get_bt_result_path(bt_type="Research")
        self.bt_prod_path = self.get_bt_result_path(bt_type="Production")
        self.down_today_live_return_file(self.today_str)
        self.collect_bt_result_daily_file()

    def get_bt_result_path(self, bt_type="Research"):
        root_path = BT_RESULT_PATH + "{}-{}/".format(self.today_str, self.today_str)
        if not os.path.exists(root_path):
            raise Exception(" Today BT Result Path Not Exists ")

        portfolio = "EasyTrack"
        amountSize = 5
        initialAmount = amountSize * 100000000
        overwrite_params = {'maxTurnoverPerOrder': 1800000, 'maxExposure': 8000000}
        executor_str = "SignalExecutorEasy"
        signal_csv_dir = "Separate0812ModelSignals"
        prod_signal_csv_dir = "ProductionEasy0812Signals"
        name =  'cv-{}-{}_{}-{}-{}-{}-{}-{}-{}'.format(self.cv_start_date, self.cv_end_date, self.cv_param_date, portfolio,
                                                        signal_csv_dir, executor_str,
                                                        initialAmount,
                                                        str(overwrite_params["maxTurnoverPerOrder"] // 10000),
                                                        str(overwrite_params["maxExposure"] // 10000) )
        if bt_type == "Research":
            result_dir_name = "bt-{}-{}-{}-research-use-{}_{}/".format(self.today_str, self.today_str, portfolio, name, signal_csv_dir)
        elif bt_type == "Production":
            result_dir_name = "bt-{}-{}-{}-production-use-{}_{}/".format(self.today_str, self.today_str, portfolio, name,
                                                                       prod_signal_csv_dir)
        bt_result_path = os.path.join(root_path, result_dir_name)
        return bt_result_path

    def collect_bt_result_daily_file(self):
        if not os.path.exists(self.bt_research_path):
            print( " BT Research Path Not Exists ")
        if not os.path.exists(self.bt_prod_path):
            print(" BT Production Path Not Exists ")

        root_path = COLLECT_RETUEN_PATH + "{}/".format(self.today_str)
        if not os.path.exists(root_path):
            os.makedirs(root_path)

        bt_research_file = os.path.join(self.bt_research_path, "result_daily.xls")
        if not os.path.exists(bt_research_file):
            print( " BT Research File Not Exists ")
        else:
            shutil.copyfile(bt_research_file, root_path + "{}_research_result_daily.xls".format(self.today_str))
            bt_research_file = os.path.join(self.bt_research_path, "TotalSummary.xls")
            shutil.copyfile(bt_research_file, root_path + "{}_research_TotalSummary.xls".format(self.today_str))

        bt_prod_file = os.path.join(self.bt_prod_path, "result_daily.xls")
        if not os.path.exists(bt_prod_file):
            print( " BT Production File Not Exists ")
        else:
            shutil.copyfile(bt_prod_file, root_path + "{}_production_result_daily.xls".format(self.today_str))
            bt_prod_file = os.path.join(self.bt_prod_path, "TotalSummary.xls")
            shutil.copyfile(bt_prod_file, root_path + "{}_production_TotalSummary.xls".format(self.today_str))

    @staticmethod
    def down_today_live_return_file(date):
        root_path = COLLECT_RETUEN_PATH + "{}/".format(date)
        if not os.path.exists(root_path):
            os.makedirs(root_path)
        local_file_name = "{}_T0_easy.xlsx".format(date)
        if os.path.exists(root_path + local_file_name):
            print(" Today Live Return File Has Been Downloaded ")
        else:
            ftp = FTP_OP()
            ftp.download_file("/Xquant/516/T0/Easy_2020/", root_path, local_file_name)
            print( " {} is Downloaded ".format(local_file_name))

    def collect_bt_result_daily(self):
        root_path = COLLECT_RETUEN_PATH + "{}/".format(self.today_str)
        result_daily_type = []
        file_name = "{}_T0_easy.xlsx".format(self.today_str)
        live_file = os.path.join(root_path, file_name)
        if not os.path.exists(live_file):
            live_result_daily = pd.DataFrame(columns=RESULT_DAILY_COLUMNS)
        else:
            live_result_daily = pd.read_excel(live_file, sheet_name="当日汇总").iloc[:1]
            live_result_daily["胜率"] = live_result_daily["胜率"].apply(lambda x: convert_win_ratio(x))
            live_result_daily["平均持仓时间"] = live_result_daily["平均持仓时间"].apply(lambda x: convert_holding_time(x))
            live_result_daily = live_result_daily.reindex(columns=RESULT_DAILY_COLUMNS)
            result_daily_type.append("Production")

        file_name = "{}_research_result_daily.xls".format(self.today_str)
        bt_file = os.path.join(root_path, file_name)
        if not os.path.exists(bt_file):
            bt_result_daily = pd.DataFrame(columns=RESULT_DAILY_COLUMNS)
        else:
            bt_result_daily = pd.read_excel(bt_file)
            bt_result_daily = bt_result_daily.reindex(columns=RESULT_DAILY_COLUMNS)
            result_daily_type.append("BT")

        file_name = "{}_production_result_daily.xls".format(self.today_str)
        prod_file = os.path.join(root_path, file_name)
        if not os.path.exists(prod_file):
            prod_result_daily = pd.DataFrame(columns=RESULT_DAILY_COLUMNS)
        else:
            prod_result_daily = pd.read_excel(prod_file)
            prod_result_daily = prod_result_daily.reindex(columns=RESULT_DAILY_COLUMNS)
            result_daily_type.append("ProductionBT")

        concat_result_daily = pd.concat([live_result_daily, bt_result_daily, prod_result_daily], axis=0)
        if concat_result_daily.empty:
            return
        concat_result_daily["日期"] = self.today_str
        concat_result_daily.index = result_daily_type

        root_path = LIVE_BT_CMP_PATH + "{}/".format(self.today_str)
        if not os.path.exists(root_path):
            os.makedirs(root_path)
        file_name = os.path.join(root_path, "concat_result_daily_{}.xlsx".format(self.today_str))
        concat_result_daily.to_excel(file_name)

    def analyze_result_daily_details(self):
        root_path = COLLECT_RETUEN_PATH + "{}/".format(self.today_str)
        file_name = "{}_T0_easy.xlsx".format(self.today_str)
        live_file = os.path.join(root_path, file_name)
        if not os.path.exists(live_file):
            live_result_daily = pd.DataFrame(columns=["Prod_Profit", "Prod_Amount", "Symbol"])
        else:
            live_result_daily = pd.read_excel(live_file, sheet_name="组合证券")
            live_result_daily["证券代码"] = live_result_daily["证券代码"].apply(lambda x: convert_live_code(x))
            live_result_daily = live_result_daily.set_index("证券代码")[["盈利", "交易金额"]]
            live_result_daily.columns = ["Prod_Profit", "Prod_Amount"]
            live_result_daily["Symbol"] = live_result_daily.index.tolist()

        file_name = "{}_research_TotalSummary.xls".format(self.today_str)
        bt_file = os.path.join(root_path, file_name)
        if not os.path.exists(bt_file):
            bt_result_daily = pd.DataFrame(columns=["BT_Profit", "BT_Amount", "Symbol"])
        else:
            bt_result_daily = pd.read_excel(bt_file).set_index("ModelFileName")[["afterCostProfit", "cumOpenAmount"]]
            bt_result_daily.columns = ["BT_Profit", "BT_Amount"]
            bt_result_daily["Symbol"] = bt_result_daily.index.tolist()

        file_name = "{}_production_TotalSummary.xls".format(self.today_str)
        prod_file = os.path.join(root_path, file_name)
        if not os.path.exists(prod_file):
            prod_result_daily = pd.DataFrame(columns=["ProdBT_Profit", "ProdBT_Amount", "Symbol"])
        else:
            prod_result_daily = pd.read_excel(prod_file).set_index("ModelFileName")[["afterCostProfit", "cumOpenAmount"]]
            prod_result_daily.columns = ["ProdBT_Profit", "ProdBT_Amount"]
            prod_result_daily["Symbol"] = prod_result_daily.index.tolist()

        concat_result_daily = pd.merge(pd.merge(live_result_daily, bt_result_daily, on="Symbol", how="outer"), prod_result_daily, on="Symbol", how="outer")
        concat_result_daily = concat_result_daily.set_index("Symbol")
        concat_result_daily["ProfitDiff"] = (concat_result_daily["BT_Profit"] - concat_result_daily["Prod_Profit"]).abs()
        concat_result_daily["AmountDiff"] = (concat_result_daily["BT_Amount"] - concat_result_daily["Prod_Amount"]).abs()
        concat_result_daily = concat_result_daily.sort_values(by=["ProfitDiff", "AmountDiff"])
        explicit_diff = concat_result_daily[concat_result_daily["ProfitDiff"] >= 3000]
        if explicit_diff.shape[0] > 20:
            print( " More Then 20 Stocks Profit Diff >= 3000, Select Top 50 ")
            explicit_diff = explicit_diff.iloc[:50]

        if explicit_diff.empty:
            print(" No Stock Profit Diff Larger Than 3000 ")
            return

        valid_stocks = explicit_diff.index.tolist()
        signal_corr = get_signal_corr("Separate0812ModelSignals", "ProductionEasy0812Signals",  valid_stocks, self.today_str)
        explicit_diff = pd.concat([explicit_diff, signal_corr], axis=1)
        explicit_diff = explicit_diff.reindex(columns=["Prod_Profit", "BT_Profit", "ProdBT_Profit",
                                                       "Prod_Amount", "BT_Amount", "ProdBT_Amount",
                                                       "ProfitDiff", "AmountDiff", "Corr_BeforeTen", "Corr_AfterTen"])
        explicit_diff = explicit_diff.sort_values(by="ProfitDiff", ascending=False)
        explicit_diff["ProfitDiff"] = explicit_diff["Prod_Profit"] - explicit_diff["BT_Profit"]
        explicit_diff.columns = ["Prod盈利", "BT盈利", "ProdBT盈利", "Prod成交额", "BT成交额", "ProdBT成交额",
                                 "Prod盈利 - BT盈利", "成交额差", "10点前相关性", "10点后相关性"]
        root_path = LIVE_BT_CMP_PATH + "{}/".format(self.today_str)
        if not os.path.exists(root_path):
            os.makedirs(root_path)
        file_name = os.path.join(root_path, "single_stock_diff_details_{}.xlsx".format(self.today_str))
        explicit_diff.to_excel(file_name)

    def collect_result(self):
        """"""
         # Step 1: 汇总整体指标
        self.collect_bt_result_daily()

         # Step 2: 汇总差距较大的股票
        self.analyze_result_daily_details()


if __name__ == "__main__":
    today_str = "20201104"
    cv_start_date = "20200817"
    cv_end_date = "20201030"
    cv_param_date = today_str
    collectETR = CollectEasyTrackResult(today_str, cv_start_date, cv_end_date, cv_param_date)
    collectETR.collect_result()


