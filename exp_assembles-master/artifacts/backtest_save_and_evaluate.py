import sys
sys.path.insert(0, "../")
import os
import pandas as pd
import plotly
pyplt = plotly.offline.plot
from artifacts.backtest_plot import analyze1,analyze1_v2,analyze2, analyze_signal
from artifacts.parse_format import  parse_signal_txt, parse_ats_trade_records
from artifacts.backtest_metrics import  analysis_trade_summary, analysis_total_trade_summray
from xquant.xqutils.perf_profile import profile

def backtest_plot_trade_only(trade_records_df_day, ma_df_day, plot = False, plot_save_dir = "./", volume_unit = 500, plot_orders = False):
    """
    只根据交易数据，绘制每日的交易买卖点时刻图。
    :param trade_records_df_day:   输入为ATS线下回测成交数据格式
    :param ma_df_day: 线上行情数据，从xquant.marketdata获取
    :param plot: 是否show图片
    :param plot_save_dir: 图片保存路径
    :param volume_unit: 成交量最小单位，用于控制图中成交点的大小
    :param plot_orders: 是否绘制成交明细表格
    :return:
    """
    df_order = parse_ats_trade_records(trade_records_df_day)
    df_ma = ma_df_day
    mkdata_df = df_ma[((df_ma["MDTime"] >= "092500000") & (df_ma["MDTime"] <= "113000000")) | (
        ((df_ma["MDTime"] >= "130000000") & (df_ma["MDTime"] <= "150000000")))]
    mkdata_df["Date"] = mkdata_df.apply(lambda x: pd.to_datetime(x["MDDate"] + " " + x["MDTime"][:-3]), axis=1)

    fig_signal1 = analyze1(mkdata_df, pd.DataFrame(), df_order, plot_save_dir, plot=plot, volume_unit = volume_unit,  plot_orders = plot_orders)
    fig_signal2 = analyze2(mkdata_df, pd.DataFrame(), df_order, plot_save_dir, plot = plot)
    return fig_signal1, fig_signal2


def backtest_plot_signal_only(signal_df_day, plot = False, relative_size = True):
    """
    只根据信号数据，绘制每日的信号点时刻图。
    :param signal_df_day: 标准信号格式数据，需包含PROBABILITY分类结果列，五分类列可通过online_model.generate_probs_v3生成
    :param plot:  是否show图片
    :param relative_size: 为True根据预测值幅度调整点的大小
    :return:
    """
    # 只绘制信号数据
    if type(signal_df_day["PROBABILITY"].iloc[0])==str:
        signal_df_day["PROBABILITY"] = signal_df_day["PROBABILITY"].apply(lambda x: eval(x))
    return analyze_signal(signal_df_day, plot, relative_size)

def backtest_plot_signal_trade(signal_df_day, trade_records_df_day, ma_df_day, plot = False, plot_save_dir = "./", volume_unit = 500, plot_orders = False, plot_orderbook = True):
    """
    根据信号的分类结果和交易数据，绘制每日的信号、交易点时刻图。
    :param signal_df_day: 标准信号格式数据，需包含PROBABILITY分类结果列，可通过online_model.generate_probs_v3生成
    :param trade_records_df_day: 输入为ATS线下回测成交数据格式
    :param ma_df_day:  线上行情数据，从xquant.marketdata获取
    :param plot:  是否show图片
    :param plot_save_dir: 图片保存路径
    :param volume_unit: 成交量最小单位，用于控制图中成交点的大小
    :param plot_orders: 是否绘制成交明细表格
    :param plot_orderbook:  是否绘制一二档行情
    :return:
    """
    # 输入为ATS线下回测成交数据格式
    if os.path.isdir(plot_save_dir):
        date = ma_df_day["MDDate"].iloc[0]
        plot_save_path = os.path.join(plot_save_dir, "plot_{}.html".format(date))
    else:
        plot_save_path = plot_save_dir
    if type(signal_df_day["PROBABILITY"].iloc[0])==str:
        # 读取excel时，PROBABILITY字段类型是str
        signal_df_day["PROBABILITY"] = signal_df_day["PROBABILITY"].apply(lambda x: eval(x))
    df_ma = ma_df_day
    mkdata_df = df_ma[((df_ma["MDTime"] >= "092500000") & (df_ma["MDTime"] <= "113000000")) | (
    ((df_ma["MDTime"] >= "130000000") & (df_ma["MDTime"] <= "150000000")))]
    mkdata_df["Date"] = pd.to_datetime(df_ma["MDDate"]+df_ma["MDTime"], format ="%Y%m%d%H%M%S%f")
    # 将ATS线下回测格式转换为标准格式
    trade_record_df = parse_ats_trade_records(trade_records_df_day)
    print("backtest_plot_signal_trade save path：", plot_save_path)
    fig_signal1 = analyze1(mkdata_df, signal_df_day, trade_record_df, plot_save_path, plot = plot, volume_unit = volume_unit, plot_orders = plot_orders)
    if plot_orderbook:
        fig_signal2 = analyze2(mkdata_df, signal_df_day, trade_record_df, plot_save_path, plot = plot)
    else:
        fig_signal2 = None
    return fig_signal1, fig_signal2

def backtest_plot_signal_trade_db(signal_df_day, trade_records_df_day, ma_df_day, plot = False, plot_save_dir = "./", volume_unit = 500, plot_orders = False):
    """
    将信号成交数据输入到数据库
    :param signal_df_day:
    :param trade_records_df_day:
    :param ma_df_day:
    :param plot:
    :param plot_save_dir:
    :param volume_unit:
    :param plot_orders:
    :return:
    """
    # 输入为ATS线下回测成交数据格式
    if os.path.isdir(plot_save_dir):
        date = ma_df_day["MDDate"].iloc[0]
        plot_save_path = os.path.join(plot_save_dir, "plot_{}.html".format(date))
    else:
        plot_save_path = plot_save_dir
    if type(signal_df_day["PROBABILITY"].iloc[0])==str:
        # 读取excel时，PROBABILITY字段类型是str
        signal_df_day["PROBABILITY"] = signal_df_day["PROBABILITY"].apply(lambda x: eval(x))
    df_ma = ma_df_day
    mkdata_df = df_ma[((df_ma["MDTime"] >= "092500000") & (df_ma["MDTime"] <= "113000000")) | (
    ((df_ma["MDTime"] >= "130000000") & (df_ma["MDTime"] <= "150000000")))]
    mkdata_df["Date"] = mkdata_df.apply(lambda x: pd.to_datetime(x["MDDate"] + " " + x["MDTime"][:-3]), axis=1)
    # 将ATS线下回测格式转换为标准格式
    trade_record_df = parse_ats_trade_records(trade_records_df_day)
    print("backtest_plot_signal_trade save path：", plot_save_path)
    fig_signal1 = analyze1_v2(mkdata_df, signal_df_day, trade_record_df, plot_save_path, plot = plot, volume_unit = volume_unit, plot_orders = plot_orders)
#     fig_signal2 = analyze2(mkdata_df, signal_df_day, trade_record_df, plot_save_path, plot = plot)

    return fig_signal1


def backtest_trade_evaluation(trade_records_df):
    """
    统计每一天的绩效数据
    :param trade_records_df: 成交数据明细，ATS线下回测标准数据结构
    :return:
    """
    return analysis_trade_summary(trade_records_df)


def backtest_trade_evaluation_agg(daily_trade_summary, daily_market_df = pd.DataFrame()):
    """
    将每一天的绩效数据，聚合成整段区间的收益率数据
    :param daily_trade_summary: 每一天的绩效数据，可由backtest_trade_evaluation生成
    :param daily_market_df: 行情数据，可不传
    :return:
    """
    return analysis_total_trade_summray(daily_trade_summary, daily_market_df)



if __name__=="__main__":
    try:
        SYMBOL = sys.argv[1]
        backtest_date = sys.argv[2]
        signal_file = sys.argv[3]
        result_path_dir = sys.argv[4]
    except:
        SYMBOL = "002594.SZ"
        backtest_date = "20230818"
        base_dir = "/data/user/013150/exp_result/002594.SZ-002594.SZ_trade_v00"
        signal_file = os.path.join(base_dir, "signal_files_txt/th0.9_probs0.6/test/2023-08-18.txt")
        trade_file =  os.path.join(base_dir, "backtest/xbrain_result/trade_records_20230818.parquet")

    try:
        #TODO: 必须先计算5分类，才能化图
        from MDCDataProvider.MDCDataProvider import MDCDataProvider
        mdc = MDCDataProvider()
        ma_df = mdc.get_data_by_date("StockTick", SYMBOL, backtest_date.replace("-", ""))
        mdc.dfs.close()
        print(ma_df)
        del mdc

        trade_records_df = pd.read_parquet(trade_file)
        signal_df = parse_signal_txt(signal_file)
        fig_signal1 = backtest_plot_signal_only(signal_df)
        fig_signal1, fig_signal2 = backtest_plot_signal_trade(signal_df, trade_records_df, ma_df, plot=False)

        with open("/home/appadmin/plot_{}.html".format(backtest_date), "w") as f:
            f.write(fig_signal1.to_html(full_html=False))
            # f.write(trade_records_df.to_html())
        os.system("curl ftp://168.8.2.68/013150/ -T /home/appadmin/plot_{}.html -u 'ftphzh:ftphzh2602'".format(backtest_date))
    except:
        import traceback
        print(traceback.print_exc())
        print("绘图失败！")
    # handout: end-exclude