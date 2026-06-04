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


def ats_backtest_unit(start_date, end_date, signal_path_dir, signalName, result_save_path, local_cluster=True, num_workers=10, use_jar_version = "v0"):
    class TaskDemo(BatchRunner):
        def create_backtest_meta(self):
            tasks = []
            return tasks

    if not os.path.exists(result_save_path):
        os.makedirs(result_save_path)

    # 策略jar包存储路径，用户需提前上传
    if use_jar_version == "v0":
        strategy_path = "/data/user/013150/trade_data/backtest/backup202307_v0"
        strategy_param_path = os.path.join(strategy_path, "params/param.json")
    if use_jar_version == "v1":
        strategy_path = "/data/user/013150/trade_data/backtest/backup202308_v1"
        strategy_param_path = os.path.join(strategy_path, "params/param.json")
    # 策略日志存储路径，按照策略ID分别打包成不同zip包。创建失败的策略实例无日志zip包
    log_path = os.path.join(base_dir, "backtest/log")

    fa = FactorData()
    days = fa.tradingday(start_date, end_date)
    # 创建回测任务
    t = TaskDemo(strategy_path=strategy_path, log_path=log_path,
                 cpus_per_node=2, mem_per_node=6, workers=num_workers, local_cluster=local_cluster, auto_close=False)
    strategy_param = json.load(open(strategy_param_path, "r"))
    strategy_param["策略标的"] = SYMBOL

    task_list = []
    for date in days:
        date = datetime.strptime(date, "%Y%m%d").strftime("%Y-%m-%d")
        publisher_file = os.path.join(signal_path_dir, "{}.txt".format(date))
        task_list.append(
            {
                "Strategy": "STARArbitrageSubStrategy",
                "BackTestTimeFrame": "PERIOD_Tick",
                "MarketDataSortType": "RECEIVE_TIME",
                "ReportTimeFrame": "PERIOD_Tick",
                "MarketDataTunnel": "CUSTOMIZED",
                'SpecHistoryMDService': 'XQUANT',
                'SpecHisotryMDServiceParam': {'xquantStartDate': date, 'xquantEndDate': date},
                "StartDate": None,
                "EndDate": None,
                "Match": "CUSTOMIZED",
                "CustomizedXmlFile": "bean.xml",
                "StrategyType": "CONSUMER",
                "PublisherFile": publisher_file,
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
            })
    print("[signal_path]:", signal_path_dir, "task_num:", len(task_list))

    res_dict = t.run(task_list)
    # 分析运行结果
    analyze_tool = AnalyzeTool(log_path=log_path, res_dict=res_dict)
    # 获取本次回测的所有task_id
    task_ids = analyze_tool.get_all_task_ids()

    trade_records_list = []
    backtest_result_df_list = []

    write = pd.ExcelWriter(
        os.path.join(result_save_path, "{}_records.xls".format(signalName)))
    for t_id in task_ids:
        resp_df = analyze_tool.get_result_by_task_id(t_id)
        # print(resp_df)

        # 获取本次任务的执行流水
        try:
            trade_records_df = analyze_tool.get_trade_records_by_task_id(t_id)
            print(os.path.join(log_path, t_id), "trade_records_df: ", trade_records_df.shape)
            backtest_result_df = analyze_tool.get_last_trade_reports_by_task_id(t_id)
            backtest_result_df["税后回转盈亏"] = backtest_result_df["回转盈亏"] - backtest_result_df["卖成交金额"] * 0.001
            sum_amount = (backtest_result_df["卖成交金额"] + backtest_result_df["买成交金额"]).iloc[0]
            backtest_result_df["税后回转盈亏收益率"] = backtest_result_df["税后回转盈亏"] / (sum_amount) if sum_amount else 0
            backtest_result_df["税后回转盈亏收益率(年化)"] = backtest_result_df["税后回转盈亏收益率"] * 252

            trade_records_df.to_excel(write, sheet_name=str(trade_records_df.createDate[0])[:10],
                                      index=False)  # 写入文件的Sheet1
        except:
            print(t_id)
            print("暂无相关行情数据!")
            continue

        if not backtest_result_df.empty:
            backtest_result_df_list.append(backtest_result_df)

    write.save()
    write.close()

    if backtest_result_df_list:
        backtest_result = pd.concat(backtest_result_df_list)
        try:
            backtest_result.drop(columns=["TimeStamp", "tick时间", "逐笔成交时间"], inplace=True)
        except:
            pass

        columns = list(backtest_result.columns)
        columns.insert(0, columns.pop(columns.index("监控日期")))
        backtest_result = backtest_result.loc[:, columns]
        backtest_result.to_excel(os.path.join(result_save_path, "{}_result.xls".format(signalName)))
    print("回测结果：")


def ats_main(SYMBOL, StrategyModelName, start_date, end_date, local_cluster = False, online_signal_backtest = False):
     # 线上信号回测
    if online_signal_backtest == False:
        signal_path_base_dir = os.path.join(base_dir, "{}-{}".format(SYMBOL, StrategyModelName), "signal_files_txt")
        result_save_path = os.path.join(base_dir, "{}-{}".format(SYMBOL, StrategyModelName), "Ats_result")

        signal_list = os.listdir(signal_path_base_dir)
        signal_list = [i for i in signal_list if i.startswith("th")]
        print("[signal_list]:", signal_list)

        #对每组阈值都运行回测，
        for signalName in signal_list[:]:
            signal_path_dir = os.path.join(signal_path_base_dir, signalName)
            ats_backtest_unit(start_date, end_date, signal_path_dir=signal_path_dir,
                          signalName=signalName, result_save_path=os.path.join(result_save_path, "v0"),
                          local_cluster=local_cluster, num_workers=20, use_jar_version="v0")
            ats_backtest_unit(start_date, end_date, signal_path_dir=signal_path_dir,
                          signalName=signalName, result_save_path=os.path.join(result_save_path, "v1"),
                          local_cluster=local_cluster, num_workers=20, use_jar_version="v1")
    else:
        signal_path_dir = "/data/user/013150/trade_data/COO/688599.SH-688599.SH_trade_v1.2/mm_ai_signal/online"
        result_save_path = "/home/appadmin/"
        signalName = "onlneSignal"
        SYMBOL = "688599.SH"
        StrategyModelName = "688599.SH_trade_v1.2"
        start_date, end_date = "20230731", "20230731"

        ats_backtest_unit(start_date, end_date, signal_path_dir=signal_path_dir, signalName=signalName,
                      result_save_path=result_save_path,
                      local_cluster=local_cluster, num_workers=20)