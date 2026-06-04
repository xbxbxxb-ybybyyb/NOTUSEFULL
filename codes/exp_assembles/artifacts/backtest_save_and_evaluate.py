import sys
sys.path.insert(0, "../")
import os
import pandas as pd
import plotly
pyplt = plotly.offline.plot
from artifacts.backtest_plot import analyze1, analyze2, plot_signal_fig
from artifacts.parse_format import parse_online_trade_records, parse_xbrain_trade_records, parse_signal_txt, parse_ats_trade_records
from artifacts.backtest_metrics import  analysis_trade_summary, analysis_total_trade_summray

def plot_trade_fig_only(trade_record_df, ma_df, plot = False):
    df_order = parse_online_trade_records(trade_record_df)
    df_order = parse_xbrain_trade_records(df_order)
    df_ma = ma_df
    mkdata_df = df_ma[((df_ma["MDTime"] >= "092500000") & (df_ma["MDTime"] <= "113000000")) | (
        ((df_ma["MDTime"] >= "130000000") & (df_ma["MDTime"] <= "150000000")))]
    mkdata_df["Date"] = mkdata_df.apply(lambda x: pd.to_datetime(x["MDDate"] + " " + x["MDTime"][:-3]), axis=1)

    visual_path_offline = "/home/appadmin/{}.html".format(ma_df["MDDate"].iloc[0])
    fig_signal1 = analyze1(mkdata_df, pd.DataFrame(), df_order, visual_path_offline, plot=plot)
    return fig_signal1, None


def plot_signal_fig_only(signal_df, plot = False):
    return plot_signal_fig(signal_df, plot)


def plot_signal_trade_fig(signal_df, trade_record_df, ma_df, plot = False, plot_save_path = "./"):
    df_ma = ma_df
    mkdata_df = df_ma[((df_ma["MDTime"] >= "092500000") & (df_ma["MDTime"] <= "113000000")) | (
    ((df_ma["MDTime"] >= "130000000") & (df_ma["MDTime"] <= "150000000")))]
    mkdata_df["Date"] = mkdata_df.apply(lambda x: pd.to_datetime(x["MDDate"] + " " + x["MDTime"][:-3]), axis=1)
    # 将ATS线下回测格式转换为标准格式
    trade_record_df = parse_ats_trade_records(trade_record_df)
    print("plot_signal_trade_fig save path：", plot_save_path)
    fig_signal1 = analyze1(mkdata_df, signal_df, trade_record_df, plot_save_path, plot = plot)
    fig_signal2 = analyze2(mkdata_df, signal_df, trade_record_df, plot_save_path, plot = plot)

    return fig_signal1, fig_signal2


def evaluate_trade_summary(trade_records_df):
    return analysis_trade_summary(trade_records_df)

def evaluate_total_trade_summray(daily_trade_summary, daily_market_df):
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
        fig_signal1 = plot_signal_fig_only(signal_df)
        fig_signal1, fig_signal2 = plot_signal_trade_fig(signal_df, trade_records_df, ma_df, plot=False)
        print(22222)

        with open("/home/appadmin/plot_{}.html".format(backtest_date), "w") as f:
            f.write(fig_signal1.to_html(full_html=False))
            # f.write(trade_records_df.to_html())
        os.system("curl ftp://168.8.2.68/013150/ -T /home/appadmin/plot_{}.html -u 'ftphzh:ftphzh2602'".format(backtest_date))
    except:
        import traceback
        print(traceback.print_exc())
        print("绘图失败！")
    # handout: end-exclude