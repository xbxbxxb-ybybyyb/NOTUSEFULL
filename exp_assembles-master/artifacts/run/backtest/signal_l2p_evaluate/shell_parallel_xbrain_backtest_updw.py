import os
import sys
sys.path.append("../")
os.system('sh install.sh')
from xbrain_backtest_evaluate import StrategySignalEvaluate
import argparse
import time
from xbrain import *
import ray
import pandas as pd
import json
import datetime as dt
from artifacts.parse_format import parse_xbrain_trade_records
from artifacts.backtest_save_and_evaluate import backtest_trade_evaluation, backtest_trade_evaluation_agg, backtest_plot_trade_only
import traceback
from artifacts.parse_param import BackTestParams

pd.set_option("display.max_columns", None)

def xbrain_backtest_unit_day(StrategyClass, backtest_params, stock, backtest_date, time_frame = "tick", **strategy_kwargs):
    try:
        signal_process_path_dir = backtest_params.get_signal_path(stock, process_signal = False) # 获取信号文件
        pred_th_up = backtest_params.pred_up
        pred_th_dw = backtest_params.pred_dw
        backtest_outpath_dir = backtest_params.get_result_path() # 获取回测结果路径

        signal_file = os.path.join(signal_process_path_dir,
                                   dt.datetime.strptime(backtest_date, "%Y%m%d").strftime("%Y-%m-%d") + ".txt")

        print("卖开仓阈值：{}， 买开仓阈值：{}!".format(pred_th_up, pred_th_dw))

        start_date = f"{backtest_date} 093000000"
        end_date = f"{backtest_date} 145959000"
        brain = XBrain(start_date=start_date, end_date=end_date, live=False,
                       init_amount=1000000, commission=0, slippage_multi=0.0,
                       allow_short=True,  # 允许卖
                       )
        brain.add_feeds(
            datanames=stock,
            time_frame=time_frame,  # "EnhancedTICK",
            instrument_type='STOCK'
        )
        # 设置撮合模式
        brain.set_fill_method(fill_param=FillParamOrder(METHOD="TRADE_MOCKER_ORDER"), fill_price=FillPrice.THIS_CLOSE, verbose=1)  # _ORDER
        # print(StrategyClass)
        brain.add_strategy(StrategyClass, SIGNAL_FILE=signal_file, INIT_PRED_UP=pred_th_up, INIT_PRED_DW=pred_th_dw)

        brain.backtest_run()
        brain.generate_report(plot=False, plotname="StrategySignalEvaluate")

        # 获取Analyzers分析的结果
        # print(os.path.join(backtest_outpath_dir, "{}.parquet".format(backtest_date)))
        trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
        # trade_records.to_parquet(os.path.join(backtest_outpath_dir, "{}.parquet".format(backtest_date)))
        trade_records = trade_records[trade_records["IsTradeMock"] == 0]
        trade_records_df = parse_xbrain_trade_records(trade_records)
        trade_summary["股票代码"] = stock
        trade_summary["回测日期"] = backtest_date
        trade_summary = backtest_trade_evaluation(trade_records_df)
        # 保存成交数据
        trade_records_df.to_parquet(os.path.join(backtest_outpath_dir, "{}_{}.parquet".format(stock, backtest_date)))
    except:
        print(traceback.print_exc())
        trade_summary = pd.DataFrame()
    return trade_summary


@ray.remote(max_calls=5)
def xbrain_backtest_unit_day_remote(StrategyClass, backtest_params, stock, backtest_date,
                             time_frame="EnhancedTICK", plot_trade=False, **strategy_kwargs):
    return xbrain_backtest_unit_day(StrategyClass, backtest_params, stock, backtest_date,
                             time_frame=time_frame, plot_trade=plot_trade, **strategy_kwargs)


def main_parallel_run(StrategyClass, backtest_params, symbol_list, pred_up = None, pred_dw = None, time_frame = "EnhancedTICK", plot_trade = False, **strategy_kwargs):
    ######################按标的按天并行回测######################
    tasks = []
    for symbol in symbol_list:
        signal_process_path_dir = backtest_params.get_signal_path(symbol, pred_up=pred_up, pred_dw=pred_dw)
        # 获取回测日期
        days = backtest_params.get_valid_backtest_dates()
        for backtest_date in days:
            # xbrain_backtest_unit_day(StrategyClass, backtest_params,
            #                                        symbol, backtest_date, time_frame=time_frame, plot_trade=plot_trade,
            #                                        **strategy_kwargs)
            # assert 1==0
            tasks.append(
                xbrain_backtest_unit_day_remote.remote(StrategyClass, backtest_params,
                                                       symbol, backtest_date, time_frame=time_frame, plot_trade = plot_trade, **strategy_kwargs))
    trade_summary_list = ray.get(tasks)
    ######################汇总绩效######################
    daily_trade_summary = pd.concat(trade_summary_list).reset_index()
    if daily_trade_summary.empty:
        print(f"回测绩效数据为空：{symbol} {days[0]} {days[-1]} {signal_process_path_dir}")
        return pd.DataFrame()

    symbol_list = sorted(set(daily_trade_summary["标的"].tolist()))
    backtest_outpath = backtest_params.get_result_path()  # 获取回测结果路径
    total_trade_summary_list = []
    for symbol in symbol_list:
        sub_daily_trade_summary = daily_trade_summary[daily_trade_summary["标的"]==symbol]
        sub_daily_trade_summary = sub_daily_trade_summary.sort_values(by=["回测日期"]).reset_index()
        # 按日汇总的区间的成交绩效数据
        sub_total_trade_summary = backtest_trade_evaluation_agg(sub_daily_trade_summary)
        if not sub_total_trade_summary.empty:
            sub_total_trade_summary["信号路径"] = backtest_outpath
            sub_total_trade_summary["策略名称"] = str(StrategyClass)
        total_trade_summary_list.append(sub_total_trade_summary)
        trade_summary_path = os.path.join(backtest_outpath, f"daily_trade_summary_{symbol}_{days[0]}_{days[-1]}_result.xls")
        sub_daily_trade_summary.to_excel(trade_summary_path)

    total_trade_summary = pd.concat(total_trade_summary_list)
    print("total_trade_summary:", total_trade_summary)
    return total_trade_summary


def prepare_params(meta_param_dict):
    exp_name1 = meta_param_dict["exp_name"]
    version_alias1 = meta_param_dict["version_alias"]
    symbol_list1 = meta_param_dict["symbol_list"]
    pred_up1 = meta_param_dict["pred_up"]
    pred_dw1 = meta_param_dict["pred_dw"]
    start_date1 = meta_param_dict["start_date"]
    end_date1 = meta_param_dict["end_date"]
    strategy_params1 = meta_param_dict["strategy_params"]
    strategy_class_name1 = meta_param_dict["strategy_class_name"]
    strategy_params1['INIT_PRED_UP'] = pred_up1
    strategy_params1['INIT_PRED_DW'] = pred_dw1

    strategy_name_version = f"{strategy_class_name1}-"
    pkeys = ["INIT_PRED_DW", "INIT_PRED_UP", "UNIT_TRADE_SIZE"]
    for pkey in pkeys:
        sub_name = str(strategy_params[pkey]).replace("-", "").replace(":", "")
        strategy_name_version = strategy_name_version + sub_name + "_"
    strategy_name_version = strategy_name_version.strip("_")
    print("strategy_name_version: ", strategy_name_version)

    if artifacts_format:
        # 研究信号路径
        task_params = BackTestParams(
            online_or_research_path=False,
            strategy_name = strategy_name_version,
            exp_name=exp_name1,
            version_alias=version_alias1,
            start_date = start_date1,
            end_date= end_date1,
            pred_up = 1.1,
            pred_dw = 1.1
        )
        symbol_list_all = task_params.get_valid_symbols() if len(symbol_list)==0 else symbol_list
    else:
        # 线上信号路径
        task_params = BackTestParams(
            online_or_research_path=True,
            strategy_name = strategy_name_version,
            exp_name=exp_name1,
            start_date=start_date1,
            end_date=end_date1
        )
        symbol_list_all = task_params.get_valid_symbols() if len(symbol_list1) == 0 else symbol_list1
    return {"task_params": task_params, "strategy_params": strategy_params1,"symbol_list": symbol_list_all}


if __name__ == '__main__':
    t1  = time.time()
    # 运行示例：
    #python3 shell_parallel_xbrain_backtest_updw.py --symbol 688981.SH --pred_up 1.2 --pred_dw -1.2 --exp_name exp_l2p_688981.SH --version xgboost_base --strategy StrategySignalT0SwiftProfit --artifacts
    parser = argparse.ArgumentParser(description='strategy tune.')
    parser.add_argument('-u', '--pred_up', type=float, default=1.0, help='pred_th_up')
    parser.add_argument('-d', '--pred_dw', type=float, default=1.0, help='pred_th_dw')
    parser.add_argument('-x', '--strategy', type=str, default="StrategySignalEvaluate", help='xbrain strategy name')
    parser.add_argument('-e', '--exp_name', type=str, default="HS_tick2", help='Description for exp_name parameter')
    parser.add_argument('-v', '--version', type=str, default = "xgboost_base", help='version_alias, default xgboost_base')
    parser.add_argument('-l', '--label', type=str, default="LabelFirstPeak_th10_120s",help='label_name, default LabelFirstPeak_th10_120s.')
    # 默认为False，传参--artifacts解析值才为True
    parser.add_argument('-f','--artifacts', default = True, action='store_true', help='Use artifacts format')
    parser.add_argument('-sd', '--start_date', type=str, default="20241014", help='Start date, eg. 20231206.')
    parser.add_argument('-ed', '--end_date', type=str, default="20241014", help='End date, eg 20240123.')

    # 解析策略参数
    args = parser.parse_args()
    exp_name = args.exp_name
    version_alias = args.version
    label_name = args.label
    artifacts_format = args.artifacts
    start_date = args.start_date
    end_date = args.end_date
    strategy_class_name = args.strategy

    ###############修改策略参数##################
    try:
        from main_aimr import load_param_dict
        # 获取当前docker被分配到的运行参数
        from xquant.compute.aimr import AIMR
        param_id = int(AIMR.getParam())
        params_dict = load_param_dict(param_id)
        symbol_list = params_dict["symbol_list"]
        label_name, exp_name, version_alias = params_dict["label_name"],params_dict["exp_name"], params_dict["version_alias"]
    except:
        exp_list = [
            ("LabelFirstPeak_th10_60s", "KG101_model", 'HS_tick2'),
            # ("LabelFirstPeakAdjust0_th10_60s", "exp_l3_hs300_new_flying5_levelone",
            #  'LabelFirstPeakAdjust0_th10_60s_factor133_arbitrade0_120_log2')
        ]
        label_name, exp_name, version_alias = exp_list[0]
        symbol_list = ['688012.SH']  # backtest_params.get_valid_symbols()

    ray.init(num_cpus=8, local_mode=False, ignore_reinit_error=True,  _system_config={"object_spilling_config": json.dumps(
        {"type": "filesystem", "params": {"directory_path": "/dfs/user/013150"}, })},
             log_to_driver= False
             )

    strategy_params = {'AM_START_PERIOD': '09:33:00',
                     'CANCEL_WAIT_SECONDS': 3,
                     'LOG_LEVEL': 'info',
                     'LOSS_LIMIT': -2,
                     'MAX_HOLD_SIZE': 1600,
                     'MAX_SELL_SIZE': 10000,
                     'MDD_LOSS_LIMIT': -2,
                     'PRICE_DEVIATION': 1,
                     'UNIT_PRICE': 0.01,
                     'UNIT_TRADE_SIZE': 400,
                     'WIN_LIMIT': 1.5}

    meta_param_dict = {
        "exp_name": exp_name,
        "version_alias": version_alias,
        "pred_up": 1.1,
        "pred_dw": -1.1,
        "symbol_list": symbol_list,
        "start_date": "20240930",
        "end_date": "20240930",
        "strategy_class_name": "StrategySignalEvaluate",
        "strategy_params": strategy_params,
        "time_frame": "EnhancedTick"
    }


    run_params = prepare_params(meta_param_dict)
    total_trade_summary = main_parallel_run(eval(strategy_class_name), run_params["task_params"],
                                            run_params["symbol_list"], **run_params["strategy_params"],
                                            time_frame = "EnhancedTick")
    # print(total_trade_summary)
    ray.shutdown()
    print("总耗时：", time.time()-t1)

