import os
from xbrain_backtest_simple_adj_vol import StrategySignalT0AdjVol
from xbrain_backtest_simple import StrategySignalT0Simple
from xbrain_backtest_simple_kaodang import StrategySignalT0SwiftProfit
import argparse
import time
from xbrain import XBrain
import xbrain
import ray
import pandas as pd
import json
import datetime as dt
from artifacts.parse_format import parse_signal_txt, parse_xbrain_trade_records
from artifacts.backtest_save_and_evaluate import backtest_plot_signal_trade, backtest_trade_evaluation, backtest_trade_evaluation_agg, backtest_plot_trade_only
import uuid
from xquant.marketdata import MarketData
from artifacts import exp_artifacts, model_save_and_evaluate




def xbrain_backtest_unit_day(StrategyClass, signal_process_path_dir, stock, backtest_date, pred_th_up = None, pred_th_dw = None, **kwargs):
    signal_file = os.path.join(signal_process_path_dir,
                               dt.datetime.strptime(backtest_date, "%Y%m%d").strftime("%Y-%m-%d") + ".txt")
    new_signal_file = os.path.join(signal_process_path_dir,
                               dt.datetime.strptime(backtest_date, "%Y%m%d").strftime("%Y-%m-%d") + ".parquet")
    signal_df = parse_signal_txt(signal_file)
    # 用于策略直接加载信号数据
    signal_df.to_parquet(new_signal_file)

    print("卖开仓阈值：{}， 买开仓阈值：{}!".format(pred_th_up, pred_th_dw))


    start_date = f"{backtest_date} 093000000"
    end_date = f"{backtest_date} 145959000"
    brain = XBrain(start_date=start_date, end_date=end_date, live=False,
                   init_amount=1000000, commission=0, slippage_multi=0.0,
                   allow_short=True,  # 允许卖
                   )
    time_frame = kwargs.pop("MARKET_TYPE") if kwargs.get("MARKET_TYPE", None) else "Tick"
    brain.add_feeds(
        datanames=stock,
        time_frame=time_frame,  # "EnhancedTICK",
        instrument_type='STOCK'
    )
    # 设置撮合模式
    brain.set_fill_method(fill_method='TRADE_MOCKER_ORDER', mocker_type="NORMAL", send_delay=0.0)  # _ORDER
    brain.add_strategy(StrategyClass, signal_file=new_signal_file,
                       init_open_long_th=pred_th_up, init_open_short_th=pred_th_dw,
                       init_close_long_th=pred_th_dw, init_close_short_th=pred_th_up, **kwargs)

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
        # backtest_plot_signal_trade(signal_df, trade_records_df, ma_df, plot_save_dir = plot_save_path, plot = plot, volume_unit = 200, plot_orders = True)
        return plot_save_path
    else:
        return None

def parallel_run(StrategyClass, signal_process_path_dir, plot_save_dir, stock = '688012.SH', pred_th_up = None, pred_th_dw = None, start_date = None, end_date = None, **kwargs):
    @ray.remote
    def main_inner(md_df, *args, **kwargs):
        try:
            signal_df, trade_records_df, trade_summary = xbrain_backtest_unit_day(*args, **kwargs)
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
                day = dt.datetime.strptime(v[:-4], "%Y-%m-%d").strftime("%Y%m%d")
                days.append(day)
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
        tasks.append(main_inner.remote(sub_market_df, StrategyClass, signal_process_path_dir, stock, backtest_date, plot = False, pred_th_up = pred_th_up, pred_th_dw = pred_th_dw, **kwargs))
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

def get_backtest_path(symbol,  process_singal = True, online_path = False,  **kwargs):
    # online_path, 是否读取线上信号文件路径
    if online_path:
        # dir_dict = {"688012.SH": "688012.SH_trade_v1.2"}
        # stock = "688012.SH"
        # signal_dir = f"/data/user/016869/AutoMiningFrame/trade_data/COO/{stock}-{dir_dict[stock]}/mm_ai_signal/online"
        pred_th_up = kwargs["pred_th_up"]
        pred_th_dw = kwargs["pred_th_dw"]
        label_name = kwargs["label_name"]
        exp_name = kwargs["exp_name"]
        flag = False
        for exp_name in [exp_name]+["unite_semi_v1.1", "semi_v1.1", "computer_v1.1", "nation_innovation_v1.1"]:
            base_dir = f"/data/user/013150/trade_data/COO/{exp_name}"
            parquet_path = os.path.join(base_dir, f"signal_files/{label_name}-{stock}.parquet")
            if not os.path.exists(parquet_path):
                continue
            flag = True
            break
        if flag == False:
            raise Exception("无满足要求的线上文件格式！", parquet_path)
        signal_dir = os.path.join(base_dir, f"{label_name}-{stock}/pred_th_up@{'%.2f'%pred_th_up}-pred_th_dw@{'%.2f'%abs(pred_th_dw)}/signal_files_processed")
        print(signal_dir)
        if process_singal:
            signal_df_load = pd.read_parquet(parquet_path)
            # 存储该阈值信号文件
            model_save_and_evaluate.model_signal_process_long_short_pred_th_classify(signal_df_load,
                                                                                 pred_th_up=pred_th_up,
                                                                                 pred_th_dw=pred_th_dw,
                                                                                 symbol=stock,
                                                                                 signal_process_base_dir=signal_dir)
    else:
        exp_name = kwargs["exp_name"]
        version_alias = kwargs["version_alias"]
        pred_th_up = kwargs["pred_th_up"]
        pred_th_dw = kwargs["pred_th_dw"]
        label_name = kwargs["label_name"]
        # expa = exp_artifacts.ExpArtifacts(exp_name=exp_name, exp_base = "/dfs/group/800657/exp_results")
        expa = exp_artifacts.ExpArtifacts(exp_name=exp_name)
        expa.activate_version_to_save(version_alias = version_alias)
        signal_dir = expa.path_of_signal_process_save(evaluate_type="long_short_pred_th_classify",
                                                                   version_alias=version_alias,
                                                                   label_name=label_name,
                                                                   symbol=symbol,
                                                                   pred_th_up=pred_th_up, pred_th_dw=pred_th_dw)
        if process_singal:
            signal_df_load = expa.model_signal_load(version_alias = version_alias, label_name=label_name, symbol=symbol)
            model_save_and_evaluate.model_signal_process_long_short_pred_th_classify(signal_df_load, pred_th_up=pred_th_up,
                                                                                     pred_th_dw=pred_th_dw,
                                                                                     symbol=symbol,
                                                                                     signal_process_base_dir=signal_dir)

    return signal_dir


if __name__ == '__main__':
    strategy_params_total = {
        "StrategySignalT0Simple":{
            "tradesize":400,
            "HOLD_POSITION_LIMIT":1600,
            "SELL_POSITION_LIMIT":30000,
            "ADJUST_VOLUME":False,
            "DEVIATION_SELF_PRICE":1,
            "START_PERIOD": "09:33:00",
            "optimal_price_stoploss_th":-3,
            "takeprofit_th": 30,
            "stoploss_th":-5,
            "MARKET_TYPE": "Tick"
        },
        "StrategySignalT0AdjVol":{
            "tradesize": 400,
            "HOLD_POSITION_LIMIT": 5000,
            "SELL_POSITION_LIMIT": 30000,
            "ADJUST_VOLUME": False,
            "DEVIATION_SELF_PRICE": 3,
            "START_PERIOD": "09:33:00",
            "optimal_price_stoploss_th": -5,
            "takeprofit_th": 30,
            "stoploss_th": -5,
            "MARKET_TYPE": "EnhancedTick"
        },
        "StrategySignalT0SwiftProfit": {
            "tradesize": 200,
            "HOLD_POSITION_LIMIT": 600,
            "SELL_POSITION_LIMIT": 30000,
            "ADJUST_VOLUME": False,
            "DEVIATION_SELF_PRICE": 1,
            "START_PERIOD": "09:33:00",
            "optimal_price_stoploss_th": -2,
            "takeprofit_th": 4,
            "swift_takeprofit_th": 1,
            "stoploss_th": -5,
            "MARKET_TYPE": "EnhancedTick"
        }
    }

    # 运行示例：
    # python3 parallel_xbrain_backtest_updw.py --symbol 000977.SZ --pred_up 1.4 --pred_dw -1.4 --exp_name exp_l2p_000977.SZ --strategy StrategySignalT0Simple

    symbol_list = [
        ("688256.SH", 1.3, -1.2),
        ("688256.SH", 1.5, -1.4),
        # ("688981.SH", 1.2, -1.2),
        # ("688012.SH", 1.4, -1.4),
        # ("688256.SH", 1.6, -1.6),
        # ("688271.SH", 1.4, -1.4),
        # ("688390.SH", 1.6, -1.6),
        # ("688041.SH", 1.7, -1.7),
        # ("688041.SH", 1.5, -1.5),
    ]
    exp_name = "exp_l3_zzkc_flying4"
    version_alias = "LabelFirstPeak_th12_60s_factor98_log2_huber1"
    local_mode = False
    label_name = "LabelFirstPeak_th12_60s"
    artifacts_format = True
    strategy_class = eval("StrategySignalT0AdjVol")#StrategySignalT0AdjVol

    #################################
    strategy_name = strategy_class.__name__
    strategy_params = strategy_params_total[strategy_name]
    strategy_name_version = f"{strategy_name}-"
    pkeys = ["MARKET_TYPE", "START_PERIOD", "ADJUST_VOLUME", "SELL_POSITION_LIMIT", "HOLD_POSITION_LIMIT"]
    if strategy_name == "StrategySignalT0AdjVol":
        pkeys.extend(["optimal_price_stoploss_th", "stoploss_th"])
    if strategy_name == "StrategySignalT0SwiftProfit":
        pkeys.extend(["optimal_price_stoploss_th", "stoploss_th", "takeprofit_th", "swift_takeprofit_th"])
    for pkey in pkeys:
        sub_name = str(strategy_params[pkey]).replace("-", "").replace(":", "")
        strategy_name_version = strategy_name_version + sub_name + "_"
    strategy_name_version = strategy_name_version.strip("_")
    print("strategy_name_version: ", strategy_name_version)
    #################################

    t1  = time.time()
    if local_mode:
        backtest_date = "20240520" # "20231128"
        stock, pred_th_up, pred_th_dw  = "688256.SH", 1.2, -1.2
        # stock, pred_th_up, pred_th_dw = "688256.SH", 1.5, -1.5
        # stock, pred_th_up, pred_th_dw  = "300373.SZ", 2.4,-1.4
        pd.set_option("display.max_rows", None)
        if artifacts_format:
            signal_process_dir = get_backtest_path(stock, process_singal = False, online_path=False,
                                                   exp_name=exp_name, version_alias = version_alias,
                                                   label_name=label_name, pred_th_up=pred_th_up,
                                                   pred_th_dw=pred_th_dw)
            plot_save_dir = signal_process_dir.replace("signal_processed", strategy_name)
        else:
            # 也可以指定自己的信号文件路径
            signal_process_dir = get_backtest_path(stock, online_path=True, process_singal=False,
                                                   exp_name=exp_name,
                                                   pred_th_up=pred_th_up, pred_th_dw=pred_th_dw,
                                                   label_name=label_name)
            plot_save_dir = os.path.join(signal_process_dir, "..", "new_mocker_" + strategy_name_version)
        # signal_process_dir = "/data/user/013150/exp_result/backtest_analysis/signal_files"
        plot_save_dir = "/data/user/013150/exp_result/plot_tmp/"
        strategy_params["DEVIATION_SELF_PRICE"] = 1
        signal_df, trade_records_df, trade_summary = xbrain_backtest_unit_day(strategy_class,
                                                                              signal_process_dir, stock=stock,
                                                                              backtest_date=backtest_date,
                                                                              pred_th_up=pred_th_up,
                                                                              pred_th_dw=pred_th_dw,
                                                                              **strategy_params
                                                                              )
        ma = MarketData()
        ma_df = ma.get_data_by_date("Stock", stock, backtest_date)
        # 绘制可视化图
        # plot_save_dir = "/data/user/013150/exp_result/plot_tmp/"
        plot_save_path = xbrain_evaluate_unit_day(signal_df, trade_records_df, ma_df, plot_save_dir, plot=False)
        backtest_date1 = backtest_date[:4] + "-" + backtest_date[4:6]+"-" +backtest_date[6:]
        source_path = os.path.join(plot_save_dir, f"{stock}-{backtest_date1}.html")
        print("source_path:", source_path)
        os.system("cp {} /data/user/013150/exp_result/plot_tmp/{}_xbrain_plot.html".format(source_path, backtest_date))
        # os.system("curl ftp://168.8.2.68/013150/ -T {} -u 'ftphzh:ftphzh2602'".format(plot_save_path))
        # print(trade_records_df)
        print(trade_summary)
    else:
        for stock, pred_th_up, pred_th_dw in symbol_list:
            ray.init(num_cpus=10, ignore_reinit_error=True, local_mode=False, _system_config={"object_spilling_config": json.dumps(
                {"type": "filesystem", "params": {"directory_path": "/dfs/user/013150/tmp/"}, })},
                     log_to_driver= False
                     )
            if artifacts_format:
                signal_process_dir = get_backtest_path(stock, process_singal = False, online_path=False,
                                                       exp_name=exp_name, version_alias = version_alias,
                                                       pred_th_up=pred_th_up, pred_th_dw=pred_th_dw, label_name=label_name)
                plot_save_dir = signal_process_dir.replace("signal_files_processed", strategy_name_version)
            else:
                # 也可以指定自己的信号文件路径
                signal_process_dir = get_backtest_path(stock, online_path=True, process_singal= True,
                                                       exp_name = exp_name,
                                                       pred_th_up=pred_th_up, pred_th_dw=pred_th_dw,
                                                       label_name=label_name)
                plot_save_dir = os.path.join(signal_process_dir, "..", "compare_l2p_"+strategy_name_version)

            print("plot_save_dir:", plot_save_dir)
            parallel_run(strategy_class, signal_process_dir, plot_save_dir, stock, start_date="20240426",end_date="20240613",
                         pred_th_up = pred_th_up, pred_th_dw = pred_th_dw, **strategy_params)
    print("总耗时：", time.time()-t1)

