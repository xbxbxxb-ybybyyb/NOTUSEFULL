import os
from xbrain_backtest_simple import StrategySignalT0Simple
import time
from xbrain import XBrain
import ray
from xquant.factordata import FactorData
import pandas as pd
import json
import numpy as np
import datetime as dt
from artifacts.parse_format import parse_signal_txt, parse_xbrain_trade_records
from artifacts.backtest_save_and_evaluate import backtest_plot_signal_trade, backtest_trade_evaluation, backtest_trade_evaluation_agg, backtest_plot_trade_only
import uuid
from xquant.marketdata import MarketData


def xbrain_backtest_unit_day(strategy_class, signal_process_path_dir, stock, backtest_date, **kwargs):
    signal_file = os.path.join(signal_process_path_dir,
                               dt.datetime.strptime(backtest_date, "%Y%m%d").strftime("%Y-%m-%d") + ".txt")
    new_signal_file = os.path.join(signal_process_path_dir,
                               dt.datetime.strptime(backtest_date, "%Y%m%d").strftime("%Y-%m-%d") + ".parquet")
    signal_df = parse_signal_txt(signal_file)
    # 用于策略直接加载信号数据
    signal_df.to_parquet(new_signal_file)
    # signal_df = pd.read_parquet(signal_file)


    signal_df["v"] = signal_df["PROBABILITY"].apply(lambda x: np.array(x).argmax())
    bid_th1 = signal_df[signal_df["v"] == 3]["PREDICTED"].min()
    ask_th1 = signal_df[signal_df["v"] == 1]["PREDICTED"].max()
    if np.isnan(bid_th1):
        bid_th1 = 2
    if np.isnan(ask_th1):
        ask_th1 = -2
    print("卖开仓阈值：{}， 买开仓阈值：{}!".format(ask_th1, bid_th1))


    start_date = f"{backtest_date} 093000000"
    end_date = f"{backtest_date} 145959000"
    brain = XBrain(start_date=start_date, end_date=end_date, live=False,
                   init_amount=1000000, commission=0, slippage_multi=0.0,
                   allow_short=True,  # 允许卖空
                   )
    brain.add_feeds(
        datanames=stock,
        time_frame="Tick",  # "EnhancedTICK",
        instrument_type='STOCK'
    )
    # 设置撮合模式
    brain.set_fill_method(fill_method='TRADE_MOCKER_ORDER', mocker_type="NORMAL", send_delay=0.0)  # _ORDER
    brain.add_strategy(strategy_class, signal_file=new_signal_file,
                       init_open_long_th=bid_th1, init_open_short_th=ask_th1,
                       init_close_long_th=ask_th1, init_close_short_th=bid_th1, **kwargs)

    brain.backtest_run()
    brain.generate_report(plot=False, plotname="StrategySignalT0")

    # 获取Analyzers分析的结果
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    trade_records = trade_records[trade_records["IsTradeMock"] == 0]
    trade_records_df = parse_xbrain_trade_records(trade_records)
    trade_summary["股票代码"] = stock
    trade_summary["回测日期"] = backtest_date
    trade_summary = backtest_trade_evaluation(trade_records_df)
    os.system("rm {}".format(new_signal_file))
    return signal_df, trade_records_df, trade_summary

def xbrain_evaluate_unit_day(signal_df, trade_records_df, ma_df, plot_save_dir, plot=False):
    if not trade_records_df.empty:
        stock = trade_records_df["symbol"].iloc[0]
        backtest_date = trade_records_df["tradeDate"].iloc[0]

        if not os.path.exists(plot_save_dir):
            os.makedirs(plot_save_dir)
        plot_save_path = os.path.join(plot_save_dir, f"{stock}-{backtest_date}.html")
        backtest_plot_signal_trade(signal_df, trade_records_df, ma_df, plot_save_dir = plot_save_path, plot = plot, volume_unit = 200, plot_orders = True)
        return plot_save_path
    else:
        return None

def parallel_run(strategy_class, signal_process_path_dir, plot_save_dir, stock = '688012.SH', start_date = None, end_date = None, **kwargs):
    @ray.remote
    def main_inner(md_df, *args, **kwargs):
        try:
            signal_df, trade_records_df, trade_summary = xbrain_backtest_unit_day(strategy_class, *args, **kwargs)
            if not trade_records_df.empty:
                backtest_date = trade_records_df["tradeDate"].iloc[0]
                if not os.path.exists(plot_save_dir):
                    os.makedirs(plot_save_dir)
                # （1）保存成交数据
                trade_records_df.to_parquet(os.path.join(plot_save_dir, "{}.parquet".format(backtest_date)))
                #（2）保存信号成交图
                xbrain_evaluate_unit_day(signal_df, trade_records_df, md_df, plot_save_dir)
                return trade_summary
            else:
                return pd.DataFrame()
        except:
            import traceback
            print(traceback.print_exc())
            return pd.DataFrame()

    if not os.path.exists(signal_process_path_dir):
        print("ERRRO: signal_process_path_dir does not exist！", signal_process_path_dir)
        return
    days = []
    for v in os.listdir(signal_process_path_dir):
        if v.endswith("txt"):
            try:
                days.append(dt.datetime.strptime(v[:-4], "%Y-%m-%d").strftime("%Y%m%d"))
            except:
                pass
    days = sorted(days)
    if start_date and end_date:
        start_date = start_date.replace("-", "")
        end_date =  end_date.replace("-", "")
        days = [day for day in days if day>=start_date and day<=end_date]
    print("parallel backtest days: ", days)

    save_uuid = uuid.uuid4()
    os.system(f"rm -rf /tmp/tmp_market_{stock}*")
    # 加载行情数据
    tmp_market_path = f"/tmp/tmp_market_{stock}_{save_uuid}.parquet"
    file_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(file_path, "helper_get_marketdata.py")
    os.system(f"python3 {file_path} {stock} {days[0]} {days[-1]} {tmp_market_path}")
    daily_market_df = pd.read_parquet(tmp_market_path)
    tasks = []
    for backtest_date in days:
        sub_market_df = daily_market_df[daily_market_df["MDDate"]==backtest_date]
        tasks.append(main_inner.remote(sub_market_df, signal_process_path_dir, stock, backtest_date, plot = False,**kwargs))
    trade_summary_list = ray.get(tasks)

    daily_trade_summary = pd.concat(trade_summary_list).reset_index()
    if not daily_trade_summary.empty:
        daily_trade_summary = daily_trade_summary.sort_values(by = ["回测日期"]).reset_index()
        trade_summary_path = os.path.join(plot_save_dir, f"daily_trade_summary_{stock}_{days[0]}_{days[-1]}_result.xls")
        daily_trade_summary.to_excel(trade_summary_path)

        # 按日汇总的成交绩效数据
        total_trade_summary = backtest_trade_evaluation_agg(daily_trade_summary, daily_market_df)
        total_trade_summary_path = os.path.join(plot_save_dir, f"total_trade_summary_{stock}_{days[0]}_{days[-1]}.csv")
        if not total_trade_summary.empty:
            total_trade_summary["信号路径"] = plot_save_dir
        total_trade_summary.to_csv("{}".format(total_trade_summary_path), encoding="utf-8")
        pd.set_option("display.max_columns", None)
        print("total_trade_summary:", total_trade_summary)
    else:
        print(f"回测绩效数据为空：{stock} {days[0]} {days[-1]} {signal_process_path_dir}")


def get_backtest_path(stock, strategy_name, **kwargs):
    online_path = False
    if online_path:
        dir_dict = {"688012.SH": "688012.SH_trade_v1.2"}
        stock = "688012.SH"
        signal_dir = f"/data/user/016869/AutoMiningFrame/trade_data/COO/{stock}-{dir_dict[stock]}/mm_ai_signal/online"
        # signal_probs_path = f"/data/user/016869/AutoMiningFrame/trade_data/COO/{stock}-{dir_dict[stock]}/{dir_dict[stock]}/th{label_th1}_table1.json"
        plot_save_dir = "/home/appadmin/"
    else:
        exp_name = kwargs["exp_name"]
        label_th1 = kwargs["label_th1"]
        prob = kwargs["prob"]
        label_name = kwargs["label_name"]
        base_dir = f"/dfs/group/800657/exp_results/{exp_name}/{version_alias}/{label_name}-{stock}"
        signal_dir = os.path.join(base_dir,
                                  f"label_th@{label_th1}-probs_up@{prob}-probs_dw@{prob}/signal_files_processed/")
        plot_save_dir = signal_dir.replace("signal_files_processed", f"{strategy_name}")

    return signal_dir, plot_save_dir


if __name__ == '__main__':
    strategy_params_total = {
        "StrategySignalT0Simple": {
            "tradesize": 400,
            "HOLD_POSITION_LIMIT": 1600,
            "SELL_POSITION_LIMIT": 10000,
            "ADJUST_VOLUME": False,
            "DEVIATION_SELF_PRICE": 1,
            "START_PERIOD": "09:30:30",
            "optimal_price_stoploss_th": -3,
            "takeprofit_th": 30,
            "stoploss_th": -5
        }
    }
    symbol_list = ["300373.SZ"]
    label_name = "LabelFirstPeak_th10_120s"
    exp_name = "exp_national_innovation_v1"
    version_alias = "xgboost_base"

    local_mode = True
    artifacts_format = True  # 是否使用artifacts格式
    #################################
    strategy_class = StrategySignalT0Simple  # StrategySignalT0AdjVol
    strategy_name = strategy_class.__name__
    strategy_params = strategy_params_total[strategy_name]
    strategy_name = f"{strategy_name}-{strategy_params['ADJUST_VOLUME']}_{strategy_params['START_PERIOD'].replace(':', '')}"
    print("strategy_name: ", strategy_name)
    #################################

    t1  = time.time()
    if local_mode:
        backtest_date = "20230818"
        stock = "300373.SZ"
        pd.set_option("display.max_rows", None)
        # signal_process_dir, plot_save_dir = get_backtest_path(online_path, stock, strategy_name)
        signal_process_dir, plot_save_dir = get_backtest_path(stock, strategy_name,exp_name = exp_name, version_alias =version_alias,
                        label_name = label_name, label_th1 = 1.4, prob = 0.66)
        signal_df, trade_records_df, trade_summary = xbrain_backtest_unit_day(strategy_class, signal_process_dir, stock=stock,
                                                                              backtest_date=backtest_date,
                                                                              **strategy_params)
        ma = MarketData()
        ma_df = ma.get_data_by_date("Stock", stock, backtest_date)
        # 绘制可视化图
        plot_save_path = xbrain_evaluate_unit_day(signal_df, trade_records_df, ma_df, plot_save_dir, plot=False)
        backtest_date1 = backtest_date[:4] + "-" + backtest_date[4:6]+"-" +backtest_date[6:]
        source_path = os.path.join(plot_save_dir, f"{stock}-{backtest_date1}.html")
        print("source_path:", source_path)
        os.system("cp {} /dfs/group/800657/exp_results/plot_tmp/{}_xbrain_plot.html".format(source_path, backtest_date))
        print(trade_records_df)
        print(trade_summary)
    else:
        for stock in symbol_list:
            # if stock!= "300373.SZ":
            #     continue
            ray.init(num_cpus=30, ignore_reinit_error=True, local_mode=False,
                     _system_config={"object_spilling_config": json.dumps(
                         {"type": "filesystem", "params": {"directory_path": "/dfs/user/013150/tmp/"}, })},
                     log_to_driver=False
                     )
            for label_th1 in [1.4]:
                for prob in [0.66]:
                    print(stock, label_th1, prob)
                    if artifacts_format:
                        signal_process_dir, plot_save_dir = get_backtest_path(stock, strategy_name, exp_name=exp_name, version_alias =version_alias,
                                                                              label_name = label_name, label_th1 = label_th1, prob =prob)
                    else:
                        # 也可以指定自己的信号文件路径
                        signal_process_dir = "/dfs/group/800657/exp_results/All_test_multi/signal_files_txt/com_new180/000977.SZ/th1.6_probs0.68/test"
                        plot_save_dir = signal_process_dir
                    parallel_run(strategy_class, signal_process_dir, plot_save_dir, stock, **strategy_params)
    print("总耗时：", time.time()-t1)
