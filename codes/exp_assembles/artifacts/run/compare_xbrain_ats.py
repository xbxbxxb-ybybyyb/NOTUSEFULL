import os
from datetime import datetime
from xquant.marketdata import MarketData
import pandas as pd
import numpy as np

# 加载xbrain回测数据或Ats回测数据
stock, strategyModelName, th, prob, start_date, end_date = ('300212.SZ',  "All_test_multi", 1.6, 0.66, "20230801", "20231101")

backtest_date = "20230913"
backtest_date1 = datetime.strptime(backtest_date, "%Y%m%d").strftime("%Y-%m-%d")

xbrain_base_trade_dir = f"/data/user/016869/exp_result/{strategyModelName}/backtest/xbrain_result/{stock}/th{th}_probs{prob}"
xbrain_base_signal_dir = xbrain_base_trade_dir

ats_base_trade_dir = f"/data/user/016869/exp_result/{strategyModelName}/ats_result/{stock}/th{th}_probs{prob}/"
ats_base_signal_dir = f"/data/user/016869/exp_result/{strategyModelName}/signal_files_txt/{stock}/th{th}_probs{prob}/test/"



print("xbrain_base_trade_dir:", xbrain_base_trade_dir)
print("xbrain_base_signal_dir:", xbrain_base_signal_dir)

print("ats_base_trade_dir:", ats_base_trade_dir)
print("ats_base_signal_dir:", ats_base_signal_dir)



# 加载成交数据
x_records = pd.read_parquet(os.path.join(xbrain_base_trade_dir, "trade_records_{}.parquet".format(backtest_date)))

##################################################################################
# 加载绩效数据
trade_summary_list = []
for file in os.listdir(xbrain_base_trade_dir):
    if file.startswith("trade_summary_") and file.endswith("parquet"):
        trade_summary_list.append(pd.read_parquet(os.path.join(xbrain_base_trade_dir, file)))

x_results_all = pd.concat(trade_summary_list)
x_results_all = x_results_all.sort_values(by=["回测日期"])
x_results = pd.read_parquet(os.path.join(xbrain_base_trade_dir, "trade_summary_{}.parquet".format(backtest_date)))

if True:
    # 加载成交数据
    a_records_all = pd.read_excel(os.path.join(ats_base_trade_dir, f"param+sell/{stock}_records.xls"))
    a_records = a_records_all[a_records_all["tradeDate"] == backtest_date1]

    # 加载绩效数据
    a_results_all = pd.read_excel(
        os.path.join(ats_base_trade_dir, f"param+sell/{stock}_result.xls".format(backtest_date)))
    a_results_all["MDDate"] = a_results_all["监控日期"].apply(lambda x: pd.to_datetime(x).strftime("%Y%m%d"))
    a_results_all = a_results_all.sort_values(by=["MDDate"])

    if not "税后回转盈亏" in a_results_all.columns:
        a_results_all["税后回转盈亏"] = a_results_all["回转盈亏"] - a_results_all["卖成交金额"] * 0.0005
        sum_amount = a_results_all["卖成交金额"]
        a_results_all["税后回转盈亏收益率"] = a_results_all["税后回转盈亏"] / sum_amount
        a_results_all["税后回转盈亏收益率"] = a_results_all["税后回转盈亏收益率"].replace(np.nan, 0)
        #     print(a_results_all["税后回转盈亏收益率"])
        a_results_all["税后回转盈亏收益率(年化)"] = a_results_all["税后回转盈亏收益率"] * 252
    else:
        print("绩效分析已添加。")


print("x_results_all税后回转盈亏mean:", x_results_all["税后回转盈亏"].mean())
print("a_results_all税后回转盈亏mean:", a_results_all["税后回转盈亏"].mean())

print("x_results_all卖成交金额mean:", x_results_all["卖成交金额"].mean())
print("a_results_all卖成交金额mean:", a_results_all["卖成交金额"].mean())


##################################################################################
import sys
sys.path.append("/tmp/pycharm_project_710/")
from artifacts.backtest_save_and_evaluate import plot_signal_trade_fig
from artifacts.parse_format import parse_signal_txt

ma = MarketData()
ma_df = ma.get_data_by_date("Stock", stock, backtest_date)
ats_signal_df = parse_signal_txt(os.path.join(ats_base_signal_dir, "{}.txt".format(backtest_date1)))
xbrain_signal_df = pd.read_parquet(os.path.join(xbrain_base_signal_dir, "{}.parquet".format(backtest_date1)))

fig, _ = plot_signal_trade_fig(ats_signal_df, a_records, ma_df, plot_save_path = "./ats_plot.html", plot = False)
fig1, _ = plot_signal_trade_fig(xbrain_signal_df, x_records, ma_df, plot_save_path = "./xbrain_plot.html", plot = False)

os.system("curl ftp://168.8.2.68/013150/ -T ats_plot.html -u 'ftphzh:ftphzh2602'")
os.system("curl ftp://168.8.2.68/013150/ -T xbrain_plot.html -u 'ftphzh:ftphzh2602'")