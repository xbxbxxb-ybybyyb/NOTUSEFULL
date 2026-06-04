import os
from datetime import datetime
from xquant.marketdata import MarketData
import pandas as pd
import numpy as np
import sys
from artifacts.backtest_save_and_evaluate import backtest_plot_signal_trade, backtest_trade_evaluation
from artifacts.parse_format import parse_signal_txt

symbol_list = [("688041.SH", 1.5, -1.5)]

backtest_date = "20240123"
backtest_date1 = backtest_date[:4] + "-" + backtest_date[4:6] + "-" + backtest_date[6:]

# base_dir = f"/data/user/016869/exp_result/exp_l3_kc50_th10_60s/xgboost_base/"
# base_dir = "/data/user/016869/AutoMiningFrame/trade_data/COO/l2p_000977.SZ/"
# base_dir = "/data/user/016869/AutoMiningFrame/trade_data/COO/computer_v1.1/"
base_dir = f"/dfs/group/800657/exp_results/exp_l3_kc50_th12_60s_extra59/xgboost_base/"


xbrain_name = "StrategySignalT0SwiftProfit-EnhancedTICK_093300_False_15000_600_2_5_4_1.5"#"StrategySignalT0Simple-Tick_093300_False_15000_1600"
ats_name = "STARAccumulativeSubStrategy-202403_v6_0933_1.5"

# 加载xbrain回测数据或Ats回测数据
for stock,pred_th_up, pred_th_dw  in symbol_list:
    base_dir = os.path.join(base_dir, f"LabelFirstPeak_th12_60s-{stock}/pred_th_up@{'%.2f'%pred_th_up}-pred_th_dw@{'%.2f'%abs(pred_th_dw)}")
    backtest_date1 = datetime.strptime(backtest_date, "%Y%m%d").strftime("%Y-%m-%d")
    xbrain_base_signal_dir = os.path.join(base_dir, "signal_files_processed")
    xbrain_base_trade_dir =  os.path.join(base_dir, xbrain_name)

    ats_base_signal_dir = os.path.join(base_dir, "signal_files_processed")
    ats_base_trade_dir = os.path.join(base_dir, ats_name)

    print("xbrain_base_trade_dir:", xbrain_base_trade_dir)
    print("xbrain_base_signal_dir:", xbrain_base_signal_dir)

    print("ats_base_trade_dir:", ats_base_trade_dir)
    print("ats_base_signal_dir:", ats_base_signal_dir)
    ####################################################################

    # 加载成交数据
    x_records = pd.read_parquet(os.path.join(xbrain_base_trade_dir, "{}.parquet".format(backtest_date1)))
    for file in os.listdir(xbrain_base_trade_dir):
        if file.startswith("daily_trade_summary"):
            try:
                x_results_all = pd.read_excel(os.path.join(xbrain_base_trade_dir,file))
            except:
                x_results_all = pd.read_excel(os.path.join(xbrain_base_trade_dir, file), engine="openpyxl")
    x_results = backtest_trade_evaluation(x_records)
    x_results_all = x_results_all[x_results_all["回转盈亏"] != 0]  # 剔除成交量为0

    if True:
        # 加载成交数据
        a_records_all = pd.read_excel(os.path.join(ats_base_trade_dir, f"{stock}_records.xls"))
        a_records = a_records_all[a_records_all["tradeDate"] == backtest_date1]

        # 加载绩效数据
        a_results_all = pd.read_excel(os.path.join(ats_base_trade_dir, f"{stock}_result.xls".format(backtest_date)))
        a_results_all = a_results_all[a_results_all["回转盈亏"] != 0]  # 剔除成交量为0

        a_results_all["MDDate"] = a_results_all["监控日期"].apply(lambda x: pd.to_datetime(x).strftime("%Y%m%d"))
        a_results_all = a_results_all.sort_values(by=["MDDate"])

        if not "税后回转盈亏" in a_results_all.columns:
            a_results_all["监控日期"] = a_results_all["监控日期"].apply(
                lambda x: pd.to_datetime(x).strftime("%Y-%m-%d"))
            a_results_all["税后回转盈亏"] = a_results_all["回转盈亏"] - a_results_all["卖成交金额"] * 0.0005
            sum_amount = a_results_all["卖成交金额"]
            a_results_all["税后回转盈亏收益率"] = a_results_all["税后回转盈亏"] / sum_amount
            a_results_all["税后回转盈亏收益率"] = a_results_all["税后回转盈亏收益率"].replace(np.nan, 0)
            a_results_all["税后回转盈亏收益率(年化)"] = a_results_all["税后回转盈亏收益率"] * 252
        else:
            print("绩效分析已添加。")
        print(a_results_all)
        a_results = a_results_all[a_results_all["MDDate"]==backtest_date]


    print("x_results_all税后回转盈亏mean:", x_results["税后回转盈亏"].mean())
    print("a_results_all税后回转盈亏mean:", a_results["税后回转盈亏"].mean())

    print("x_results_all卖成交金额mean:", x_results["卖成交金额"].mean())
    print("a_results_all卖成交金额mean:", a_results["卖成交金额"].mean())

    ##################################################################################

    ma = MarketData()
    ma_df = ma.get_data_by_date("Stock", stock, backtest_date)
    ats_signal_df = parse_signal_txt(os.path.join(ats_base_signal_dir, "{}.txt".format(backtest_date1)))
    xbrain_signal_df = parse_signal_txt(os.path.join(xbrain_base_signal_dir, "{}.txt".format(backtest_date1)))

    def highlight_vals(s, col):
        is_flag = pd.Series(data=False, index=s.index)
        is_flag[col] = s[col] == "BID"
        return ['background-color: pink' if is_flag.any() else 'background-color: lightgreen' for v in is_flag]
    ats_table = a_records.style.apply(lambda x: highlight_vals(x, col="side"), axis=1).to_html()
    xbrain_table = x_records.style.apply(lambda x: highlight_vals(x, col="side"), axis=1).to_html()

    with open("/data/user/013150/exp_result/plot_tmp/{}_ats_plot.html".format(backtest_date), "a") as f:
        f.write(ats_table)

    with open("/data/user/013150/exp_result/plot_tmp/{}_xbrain_plot.html".format(backtest_date), "a") as f:
        f.write(xbrain_table)


    if True:
        path1 = os.path.join(ats_base_trade_dir, "{}-{}.html".format(stock, backtest_date1))
        path2 = os.path.join(xbrain_base_trade_dir, "{}-{}.html".format(stock, backtest_date1))
        fig, _ = backtest_plot_signal_trade(ats_signal_df, a_records, ma_df, plot_save_dir = path1, plot = False)
        fig1, _ = backtest_plot_signal_trade(xbrain_signal_df, x_records, ma_df, plot_save_dir = path2, plot = False)

        with open(path1, "a") as f:
            f.write(ats_table)

        with open(path2, "a") as f:
            f.write(xbrain_table)

    os.system("curl ftp://168.8.2.68/013150/ -T {} -u 'ftphzh:ftphzh2602'".format(path1))
    # os.system("curl ftp://168.8.2.68/013150/ -T {} -u 'ftphzh:ftphzh2602'".format(path2))