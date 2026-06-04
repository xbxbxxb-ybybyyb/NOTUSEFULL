import os
import pandas as pd
import time
import sys
from xquant.strategy.ats_backtest.batch_runner import BatchRunner
import json
from xquant.strategy.ats_backtest.analyze.analyze_tool import AnalyzeTool
from xquant.factordata import FactorData
import ray
from datetime import datetime
from xquant.compute.ray_cluster import recycle_ray_cluster

time.sleep(3)


def ats_backtest_unit(SYMBOL,start_date, end_date, signal_path_dir, result_save_path):
    if not os.path.exists(result_save_path):
        os.makedirs(result_save_path)

    class TaskDemo(BatchRunner):
        def create_backtest_meta(self):
            tasks = []
            return tasks
    # 策略jar包存储路径，用户需提前上传
    strategy_path = "/data/user/013150/trade_data/backtest/backup202311_v4/"
    # 策略日志存储路径，按照策略ID分别打包成不同zip包。创建失败的策略实例无日志zip包
    log_path = "/data/user/013150/trade_data/backtest/log/"
    lib_path = "/data/user/013150/trade_data/backtest/lib_l2p/"
    # 创建回测任务
    params_path = "/data/user/013150/trade_data/backtest/backup202311_v4/param/"
    t = TaskDemo(strategy_path=strategy_path, log_path=log_path, lib_path=lib_path, params_path=params_path,
                 cpus_per_node=2, mem_per_node=4, workers=2, local_cluster=True)
    os_param = "/data/user/013150/trade_data/backtest/backup202311_v4/param/param+sell.json"
    if os.path.exists(os_param):
        strategy_param = json.load(
            open("/data/user/013150/trade_data/backtest/backup202311_v4/param/param+sell.json", "r"))
    else:
        print("param path error")
        strategy_param = json.load(
            open("/data/user/013150/trade_data/backtest/backup202311_v4/param/param+sell.json", "r"))
    strategy_param["策略标的"] = SYMBOL

    res_dict = t.run([
        {
            "Strategy": "STARAccumulativeSubStrategy",
            "BackTestTimeFrame": "PERIOD_Tick",
            "MarketDataSortType": "RECEIVE_TIME",
            "ReportTimeFrame": "PERIOD_Tick",
            "MarketDataTunnel": "CUSTOMIZED",
            'SpecHistoryMDService': 'XQUANT',
            'SpecHisotryMDServiceParam': {'xquantStartDate': start_date, 'xquantEndDate': end_date},
            "StartDate": None,
            "EndDate": None,
            "Match": "CUSTOMIZED",
            "CustomizedXmlFile": "bean.xml",
            "StrategyType": "CONSUMER",
            "PublisherFile": signal_path_dir,
            "BenchMarks": [],
            "BaseCash": 5000000,
            "Commission": 0.0003,
            "StampDuty": 0.001,
            "Environment": "UAT",
            "IndicatorFile": "",
            "EventIndicatorFile": "",
            "Universe": [
                {
                    "Symbol": SYMBOL,
                    "Quantity": 200000,
                    "BuySecAcc": "devjy998a",
                    "SellSecAcc": "devjy998a",
                    "BuyTradeAcc": "devjy998a",
                    "SellTradeAcc": "devjy998a",
                    "PortfolioNo": "1",
                    "PortfolioType": "1"
                }
            ],
            "future_position": [],
            "StrategyParam": strategy_param
        }])

    # 分析运行结果
    analyze_tool = AnalyzeTool(log_path=log_path, res_dict=res_dict)
    # 获取本次回测的所有task_id
    task_ids = analyze_tool.get_all_task_ids()

    trade_records_df = pd.DataFrame()
    for t_id in task_ids:
        try:
            trade_records_df = analyze_tool.get_trade_records_by_task_id(t_id)
            print(os.path.join(log_path, t_id), "trade_records_df: ", trade_records_df.shape)
            backtest_result_df = analyze_tool.get_last_trade_reports_by_task_id(t_id)
            backtest_result_df["税后回转盈亏"] = backtest_result_df["回转盈亏"] - backtest_result_df["卖成交金额"] * 0.001
            sum_amount = (backtest_result_df["卖成交金额"] + backtest_result_df["买成交金额"]).iloc[0]
            backtest_result_df["税后回转盈亏收益率"] = backtest_result_df["税后回转盈亏"] / (sum_amount) if sum_amount else 0
            backtest_result_df["税后回转盈亏收益率(年化)"] = backtest_result_df["税后回转盈亏收益率"] * 252
            write = pd.ExcelWriter(os.path.join(result_save_path, "trade_records_{}.xlsx".format(start_date)))

            trade_records_df.to_excel(write, sheet_name='trade', index=False)  # 写入文件的Sheet1

            backtest_result_df.to_excel(write, sheet_name='profit', index=False)
            write.save()
            write.close()
        except:
            print("暂无相关行情数据!")

    ### 回测委托为空，模拟字段名
    if trade_records_df.empty:
        content = {"symbol": ["000000.SH"],
                   'side': ["ASK"],
                   'quantity': ["0"],
                   'entrustQty': ["0"],
                   'orderStatus': ["CANCELL"],
                   'entrustPx': ["0"],
                   'cumAmount': ["0"],
                   'price': ["0"],
                   'createDate': [pd.to_datetime("1970-01-01 00:00:00")],
                   'filledDate': [pd.to_datetime("1970-01-01 00:00:00")],
                   'tradeDate': [pd.to_datetime("1970-01-01")]
                   }
        trade_records_df = pd.DataFrame(content)

    print("trade_records_df:", trade_records_df.shape)
    return trade_records_df




def ats_main(SYMBOL, start_date, end_date, signal_path_dir, result_save_path, online_signal_backtest = False):
     # 线上信号回测
    if online_signal_backtest == False:
        trade_records_df = ats_backtest_unit(SYMBOL,start_date, end_date, signal_path_dir, result_save_path)
    else:
        signal_path_dir = "/data/user/013150/trade_data/COO/688599.SH-688599.SH_trade_v1.2/mm_ai_signal/online"
        result_save_path = "/home/appadmin/"
        signalName = "onlneSignal"
        SYMBOL = "688599.SH"
        StrategyModelName = "688599.SH_trade_v1.2"
        start_date, end_date = "20230731", "20230731"
        trade_records_df = ats_backtest_unit(SYMBOL,start_date, end_date, signal_path_dir, result_save_path)
    return trade_records_df
