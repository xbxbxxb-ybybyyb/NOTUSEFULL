from backtest.xbrain_backtest_utils import parse_signal_file, parse_xbrain_trade_records, parse_trade_summary, max_drawdown
import os
from backtest.xbrain_backtest_simple import StrategySignalT0Simple
from xbrain import XBrain
import ray
from xquant.factordata import FactorData
import pandas as pd
from ray import tune
import json
import numpy as np
import datetime as dt
from artifacts.parse_format import parse_signal_txt
from artifacts.backtest_save_and_evaluate import plot_signal_trade_fig, evaluate_trade_summary, evaluate_total_trade_summray
from artifacts.exp_artifacts import ExpArtifacts
import uuid
from MDCDataProvider.MDCDataProvider import MDCDataProvider


def xbrain_backtest_unit_day(signal_process_path_dir, stock, backtest_date, prob1=0.60, th1=None, **kwargs):
    signal_file = os.path.join(signal_process_path_dir,
                               dt.datetime.strptime(backtest_date, "%Y%m%d").strftime("%Y-%m-%d") + ".txt")
    new_signal_file = os.path.join(signal_process_path_dir,
                               dt.datetime.strptime(backtest_date, "%Y%m%d").strftime("%Y-%m-%d") + ".parquet")
    signal_df = parse_signal_txt(signal_file)
    # 用于策略直接加载信号数据
    signal_df.to_parquet(new_signal_file)

    signal_df["v"] = signal_df["PROBABILITY"].apply(lambda x: np.array(x).argmax())
    bid_th1 = signal_df[signal_df["v"] == 3]["PREDICTED"].min()
    ask_th1 = signal_df[signal_df["v"] == 1]["PREDICTED"].max()
    if np.isnan(bid_th1):
        bid_th1 = 2
    if np.isnan(ask_th1):
        ask_th1 = -2
    print("prob1 {}, th {},卖开仓阈值：{}， 买开仓阈值：{}!".format(prob1, th1, ask_th1, bid_th1))


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
    brain.set_fill_method(fill_method='TRADE_MOCKER_ORDER', mocker_type="NORMAL")  # _ORDER
    brain.add_strategy(StrategySignalT0Simple, signal_file=new_signal_file,
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
    trade_summary = evaluate_trade_summary(trade_records_df)
    print(trade_summary)
    print(trade_records_df)
    return signal_df, trade_records_df, trade_summary

def xbrain_evaluate_unit_day(signal_df, trade_records_df, ma_df, plot_save_dir, plot=False):
    if not trade_records_df.empty:
        stock = trade_records_df["symbol"].iloc[0]
        backtest_date = trade_records_df["tradeDate"].iloc[0]

        if not os.path.exists(plot_save_dir):
            os.makedirs(plot_save_dir)
        plot_save_path = os.path.join(plot_save_dir, f"{stock}-{backtest_date}.html")
        fig_signal1, fig_signal2 = plot_signal_trade_fig(signal_df, trade_records_df, ma_df, plot_save_path = plot_save_path, plot = plot)
        return fig_signal1, fig_signal2
    else:
        return None, None


def parallel_run(signal_process_path_dir, plot_save_dir, stock = '688012.SH', prob1 = 0.64, th1 = 1.2):
    @ray.remote(max_calls=1)
    def main_inner(md_df, *args, **kwargs):
        try:
            signal_df, trade_records_df, trade_summary = xbrain_backtest_unit_day(*args, **kwargs)
            xbrain_evaluate_unit_day(signal_df, trade_records_df, md_df, plot_save_dir)
            return trade_summary
        except:
            import traceback
            print(traceback.print_exc())
            return pd.DataFrame()

    days = []
    for v in os.listdir(signal_process_path_dir):
        if v.endswith("txt"):
            try:
                days.append(dt.datetime.strptime(v[:-4], "%Y-%m-%d").strftime("%Y%m%d"))
            except:
                pass
    days = sorted(days)
    print("parallel backtest days: ", days)

    save_uuid = uuid.uuid4()
    os.system(f"rm -rf tmp_market_{stock}*")
    # 加载行情数据
    tmp_market_path = f"/tmp/tmp_market_{stock}_{save_uuid}.parquet"
    file_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(file_path, "helper_get_marketdata.py")
    os.system(f"python3 {file_path} {stock} {days[0]} {days[-1]} {tmp_market_path}")
    daily_market_df = pd.read_parquet(tmp_market_path)
    tasks = []
    for backtest_date in days:
        sub_market_df = daily_market_df[daily_market_df["MDDate"]==backtest_date]
        tasks.append(main_inner.remote(sub_market_df, signal_process_path_dir, stock, backtest_date, prob1 = prob1,th1 = th1,  plot = False))
    trade_summary_list = ray.get(tasks)

    daily_trade_summary = pd.concat(trade_summary_list).reset_index()
    daily_trade_summary = daily_trade_summary.sort_values(by = ["回测日期"]).reset_index()
    trade_summary_path = os.path.join(plot_save_dir, f"daily_trade_summary_{stock}_{days[0]}_{days[-1]}_result.xls")
    daily_trade_summary.to_excel(trade_summary_path)

    # 按日汇总的成交绩效数据
    total_trade_summary = evaluate_total_trade_summray(daily_trade_summary, daily_market_df)
    total_trade_summary_path = os.path.join(plot_save_dir, f"total_trade_summary_{stock}_{days[0]}_{days[-1]}.csv")
    if not total_trade_summary.empty:
        total_trade_summary["信号路径"] = plot_save_dir
    total_trade_summary.to_csv("{}".format(total_trade_summary_path), encoding="utf-8")

    # os.system("curl ftp://168.8.2.68/013150/ -T {} -u 'ftphzh:ftphzh2602'".format(result_path))
    # os.system("curl ftp://168.8.2.68/013150/ -T {} -u 'ftphzh:ftphzh2602'".format(trade_summary_path))


def parallel_tune(signal_path_dir,signal_probs_path, stock = '688012.SH', strategyModelName = "688012.SH_trade_v1.2", start_date = "20230721", end_date = "20230821", plot = False):
    def objective(params):
        prob1 = params.pop("prob1")
        prob2 = params.pop("prob2")
        th1 = params.pop("th1")

        fa = FactorData()
        days = fa.tradingday(start_date, end_date)

        result_path_dir = f"/data/user/016869/exp_result/{stock}-{strategyModelName}/backtest/xbrain_result/th{th1}_probs{prob1}/"
        if not os.path.exists(result_path_dir):
            os.makedirs(result_path_dir)
        failed_date_list = []
        for backtest_date in days:
            try:
                main(signal_path_dir, signal_probs_path, stock, backtest_date, strategyModelName, prob1 = prob1, result_path_dir = result_path_dir, plot = plot)
            except:
                import traceback
                failed_date_list.append((backtest_date, traceback.print_exc()))

        trade_summary_list = []
        for day in days:
            try:
                trade_summary_list.append(pd.read_parquet(os.path.join(result_path_dir, f"trade_summary_{day}.parquet")))
            except:
                pass
        trade_summary = pd.concat(trade_summary_list)
        print(trade_summary)
        trade_summary.to_excel(os.path.join(result_path_dir, f"trade_summary_{strategyModelName}_{days[0]}_{days[-1]}.xls"))

        res_dict = {}
        _, _, mdd, mdd_ratio = max_drawdown(trade_summary["税后回转盈亏"].cumsum().values)
        res_dict["mdd"] = mdd
        res_dict['trade_time'] = trade_summary["成交次数"].mean()
        res_dict['cancle_time'] = trade_summary['撤单次数'].mean()
        res_dict['buy_amount'] = trade_summary["买成交金额"].mean()
        res_dict['sell_amount'] = trade_summary["卖成交金额"].mean()
        res_dict['profit_withcost'] = trade_summary['税后回转盈亏'].mean()
        res_dict['yield_withcost'] = trade_summary['税后收益率'].mean()
        res_dict['yield_annual_withcost'] = trade_summary['年化收益率'].mean()
        res_dict['position'] = trade_summary['敞口数量'].mean()

        tune.report(**res_dict)

    config = {
        "dates": (start_date, end_date),
        "th1": tune.grid_search([1.5]),
        "prob1": tune.grid_search([0.64]),
        'prob2': 0.64
    }
    from ray.tune.suggest.basic_variant import BasicVariantGenerator
    searcher = BasicVariantGenerator()
    tune.run(objective, config=config,  search_alg=searcher,
             # resources_per_trial={'gpu': 0},
             name='xbrain_T0_688012_1', local_dir='/tmp/ray_results')


def parallel_tune_oneday(signal_path_dir,signal_probs_path, stock = '688012.SH', strategyModelName = "688012.SH_trade_v1.2", backtest_date = None, plot = True):
    def objective(params):
        prob1 = params.pop("prob1")
        prob2 = params.pop("prob2")
        th1 = params.pop("th1")
        trade_size = params.pop("trade_size")
        hold_position_limit = params.pop("hold_position_limit")
        start_date, end_date = params.pop("dates")

        fa = FactorData()
        days = fa.tradingday(start_date, end_date)

        result_path_dir = f"/data/user/016869/exp_result/{stock}-{strategyModelName}/backtest/xbrain_result/th{th1}_probs{prob1}/{trade_size}_{hold_position_limit}"
        if not os.path.exists(result_path_dir):
            os.makedirs(result_path_dir)
        failed_date_list = []
        for backtest_date in days:
            try:
                main(signal_path_dir, signal_probs_path, stock, backtest_date,
                     strategyModelName, prob1 = prob1, result_path_dir = result_path_dir, plot = plot, plot_name="{}_{}".format(trade_size, hold_position_limit),
                     tradesize = trade_size, HOLD_POSITION_LIMIT = hold_position_limit)
            except:
                import traceback
                failed_date_list.append((backtest_date, traceback.print_exc()))

        trade_summary_list = []
        for day in days:
            try:
                trade_summary_list.append(pd.read_parquet(os.path.join(result_path_dir, f"trade_summary_{day}.parquet")))
            except:
                pass
        trade_summary = pd.concat(trade_summary_list)
        trade_summary.to_excel(os.path.join(result_path_dir, f"trade_summary_{strategyModelName}_{days[0]}_{days[-1]}.xls"))

        res_dict = {}
        _, _, mdd, mdd_ratio = max_drawdown(trade_summary["税后回转盈亏"].cumsum().values)
        res_dict["mdd"] = mdd
        res_dict['trade_time'] = trade_summary["成交次数"].mean()
        res_dict['cancle_time'] = trade_summary['撤单次数'].mean()
        res_dict['buy_amount'] = trade_summary["买成交金额"].mean()
        res_dict['sell_amount'] = trade_summary["卖成交金额"].mean()
        res_dict['profit_withcost'] = trade_summary['税后回转盈亏'].mean()
        res_dict['yield_withcost'] = trade_summary['税后收益率'].mean()
        res_dict['yield_annual_withcost'] = trade_summary['年化收益率'].mean()
        res_dict['position'] = trade_summary['敞口数量'].mean()

        tune.report(**res_dict)

    config = {
        "dates": (backtest_date, backtest_date),
        "th1": tune.grid_search([1.2]),
        "prob1": tune.grid_search([0.62]),
        'prob2': 0.64,
        "trade_size": tune.grid_search([200, 400]),
        "hold_position_limit": tune.grid_search([400, 600, 800, 1600])
    }
    from ray.tune.suggest.basic_variant import BasicVariantGenerator
    searcher = BasicVariantGenerator()
    tune.run(objective, config=config,  search_alg=searcher,
             # resources_per_trial={'gpu': 0},
             name='xbrain_T0_688012_1', local_dir='/tmp/ray_results')


if __name__ == '__main__':
    local_mode = False
    online = False #是否读取线上信号文件路径

    params = [
        # ("688012.SH", "exp_l2p_688012.SH", 1.2, 0.62),
        ("688111.SH", "exp_l2p_688111.SH", 1.2, 0.62),
        ("603019.SH", "exp_l2p_603019.SH", 1.2, 0.62),
        ("000858.SZ", "exp_l2p_000858.SZ", 1.2, 0.62),
        ("002594.SZ", "exp_l2p_002594.SZ", 1.2, 0.62),
        ("000977.SZ", "exp_l2p_000977.SZ", 1.2, 0.62),
        ("002230.SZ", "exp_l2p_002230.SZ", 1.2, 0.62),
    ]
    strategy_name = "StrategySignalT0"

    for param in params:
        if param[0]!= "688012.SH":
            continue
        print(param)
        stock, strategyModelName, label_th1, prob = param
        expa = ExpArtifacts(exp_name=strategyModelName)
        version_alias = "xgboost_base"
        label_name = "LabelFirstPeak_th10_120s"

        if online:
            dir_dict = {"688012.SH":"688012.SH_trade_v1.2"}
            signal_process_dir = f"/data/user/016869/AutoMiningFrame/trade_data/COO/{stock}-{dir_dict[stock]}/mm_ai_signal/online"
            signal_probs_path = f"/data/user/016869/AutoMiningFrame/trade_data/COO/{stock}-{dir_dict[stock]}/{dir_dict[stock]}/th{label_th1}_table1.json"
            plot_save_dir = "/home/appadmin/"
        else:
            signal_process_dir = expa.path_of_signal_process_save(
                version_alias=version_alias,
                label_name=label_name,
                symbol=stock,
                label_th1=label_th1,
                label_th2=2,
                probs_up=prob,
                probs_dw=prob)
            signal_probs_path = os.path.join(os.path.dirname(os.path.dirname(signal_process_dir)), f"th{label_th1}_table1.json")
            plot_save_dir = signal_process_dir.replace("signal_files_processed", f"{strategy_name}")


        if local_mode:
            signal_df, trade_records_df, trade_summary = xbrain_backtest_unit_day(signal_process_dir, stock = stock,
                                                                   backtest_date = "20231120",  prob1=prob,
                                                                   tradesize=200, HOLD_POSITION_LIMIT=800)
            # 绘制可视化图
            xbrain_evaluate_unit_day(signal_df, trade_records_df, plot_save_dir, plot=False)


        else:
            ray.init(num_cpus=30, ignore_reinit_error=True, local_mode=False, _system_config={"object_spilling_config": json.dumps(
                {"type": "filesystem", "params": {"directory_path": "/data/user/013150/tmp/"}, })})
            if True:
                parallel_run(signal_process_dir,plot_save_dir, stock, th1 = label_th1, prob1 =prob)
            else:
                # parallel_tune(signal_path_dir,signal_probs_path, stock, strategyModelName)
                result_path_dir = f"/data/user/016869/exp_result/{stock}-{strategyModelName}/backtest/xbrain_result/th{th}_probs{prob}"
                parallel_tune_oneday(signal_path_dir,signal_probs_path, stock, strategyModelName, backtest_date="20231018",plot = True)