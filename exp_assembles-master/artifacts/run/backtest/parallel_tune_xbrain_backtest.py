import os
from xbrain_backtest_simple import StrategySignalT0Simple
from xbrain_backtest_simple_adj_vol import StrategySignalT0AdjVol
from xbrain import XBrain
import ray
import pandas as pd
from ray import tune
import json
import time
from artifacts.parse_format import parse_signal_txt, parse_xbrain_trade_records
from artifacts.backtest_save_and_evaluate import backtest_trade_evaluation, backtest_trade_evaluation_agg
import uuid
import argparse

def xbrain_backtest_unit_day(strategy_class, signal_df, stock, backtest_date, **kwargs):
    save_uuid = uuid.uuid4()
    new_signal_file = f"/home/appadmin/signal_df_{save_uuid}.parquet"
    signal_df.to_parquet(new_signal_file)
    start_date = f"{backtest_date} 093000000"
    end_date = f"{backtest_date} 145959000"
    brain = XBrain(start_date=start_date, end_date=end_date, live=False,
                   init_amount=1000000, commission=0, slippage_multi=0.0,
                   allow_short=True,  # 允许卖空
                   )
    time_frame = kwargs.pop("MARKET_TYPE") if kwargs.get("MARKET_TYPE", None) else "Tick"
    brain.add_feeds(
        datanames=stock,
        time_frame=time_frame,  # "EnhancedTICK",
        instrument_type='STOCK'
    )
    # 设置撮合模式
    brain.set_fill_method(fill_method='TRADE_MOCKER_ORDER', mocker_type="NORMAL", send_delay=0.0)  # _ORDER
    brain.add_strategy(strategy_class, signal_file=new_signal_file, **kwargs)

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


def parallel_tune(strategy_class, signal_file_path, plot_save_dir, stock, strategy_name, num_samples=1, start_date = None, end_date = None, **strategy_params):
    if not os.path.exists(signal_file_path):
        print("ERRRO: signal_process_path_dir does not exist！")
        return

    def objective(params):
        params.update(strategy_params)
        failed_date_list = []
        trade_summary_list = []
        for backtest_date in days:
            try:
                print("backtest_date", backtest_date)
                signal_df = pd.read_parquet(signal_file_path)
                signal_df = signal_df[signal_df["DATE"]==pd.to_datetime(backtest_date).strftime("%Y-%m-%d")]
                signal_df, trade_records_df, trade_summary = xbrain_backtest_unit_day(strategy_class, signal_df, stock, backtest_date, **params)
                if not trade_records_df.empty:
                    trade_summary = backtest_trade_evaluation(trade_records_df)
                    trade_summary_list.append(trade_summary)
            except:
                import traceback
                failed_date_list.append((backtest_date, traceback.print_exc()))

        print("failed_date_list:", failed_date_list)
        if trade_summary_list:
            daily_trade_summary = pd.concat(trade_summary_list)
            total_trade_summary = backtest_trade_evaluation_agg(daily_trade_summary)
            total_trade_summary = total_trade_summary.reindex(columns = [
                         "日均成交额",
                         "日均成交量",
                        "日均收益_税后",
                        "最大底仓年化收益率",
                        "年化收益率",
                        "最大底仓",
                        "日盈亏比_税后",
                        "日胜率_税后",
                         "最大回撤",
                        "底仓使用率",
                        "日均敞口数量"
                        ])
            total_trade_summary = total_trade_summary.rename(columns = {
                         "日均收益_税后": "winmoney_after",
                         # "最大回撤": "mdd",
                        })
            res_dict = total_trade_summary.iloc[0].to_dict()
            print(total_trade_summary)
            print(res_dict)
            tune.report(**res_dict)
        else:
            tune.report(**{
                "日均成交额":0,
                "日均成交量":0,
                "winmoney_after":0,
                "最大底仓年化收益率":0,
                "年化收益率":0,
                "最大底仓":0,
                "日盈亏比_税后":0,
                "日胜率_税后":0,
                "最大回撤":0,
                "底仓使用率":0,
                "日均敞口数量":0
            })

    signal_df = pd.read_parquet(signal_file_path)
    if not "DATE" in signal_df.columns:
        signal_df["DATE"] = signal_df["PERIOD_BEGIN"].apply(lambda x:x.strftime("%Y-%m-%d"))
        signal_df.to_parquet(signal_file_path)
    days = list(set(signal_df["DATE"].tolist()))
    print("days:", days)
    days = [day.replace("-", "") for day in sorted(days)]
    if start_date and end_date:
        start_date = start_date.replace("-", "")
        end_date =  end_date.replace("-", "")
        days = [day for day in days if day>=start_date and day<=end_date]
    if not os.path.exists(plot_save_dir):
        os.makedirs(plot_save_dir)

    if False:
        config = {
             "init_open_long_th": tune.quniform(1.5, 3.0, 0.1),
             "init_open_short_th": tune.quniform(-2.6, -1.3, 0.1),
             # 'stoploss_th': tune.choice([-5]),  # 订单单价止损比例
             # 'optimal_price_stoploss_th':tune.choice([-10]),
             # 'takeprofit_th': tune.grid_search([30]),  # 止盈比例
             'tradesize':tune.choice([400]),  # 每笔交易股数
             'OPEN_PRICE_MODE': tune.choice([0]),
             # 'CLOSE_LOSE_PRICE_MODE': tune.choice([0]),  # 平仓止损
             # 'CLOSE_WIN_PRICE_MODE': tune.choice([0]),  # 平仓止盈
             "DEVIATION_SELF_PRICE": tune.choice([1]),  # 己方最优报价偏移Tick数
        }

        from ray.tune.suggest.optuna import OptunaSearch
        optuna_search = OptunaSearch(metric='winmoney_after', mode='max')
        local_dir = os.path.join(signal_file_path,"../..", stock+"-"+strategy_name)
        os.system("rm -rf {}".format(local_dir))
        # 可视化查看超参调优结果
        # pip install  -U --trusted-host 168.7.17.225 -i http://168.7.17.225:8081/repository/pypi/simple/ tensorboardX==2.1
        # /opt/anaconda3/bin/tensorboard --logdir=StrategySignalT0Double-0933_fix_volume-0933_fix_volume/ --port 30115
        tune.run(objective, config=config, search_alg=optuna_search,
                 num_samples=num_samples,
                 name = stock, local_dir = local_dir)
    else:
        from ray.tune.suggest.basic_variant import BasicVariantGenerator
        searcher = BasicVariantGenerator()
        config = {
             "init_open_long_th": tune.grid_search([1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8]),
             "init_open_short_th": tune.grid_search([-1.4, -1.6, -1.8, -2.0, -2.2, -2.4, -2.6]),
            # "init_open_long_th": tune.grid_search([1.6]),
            # "init_open_short_th": tune.grid_search([-1.4]),
             # 'stoploss_th': tune.grid_search([-5, -3]),  # 订单单价止损比例
             # 'takeprofit_th': tune.grid_search([30]),  # 止盈比例
             'tradesize':tune.grid_search([400]),  # 每笔交易股数
             'OPEN_PRICE_MODE': tune.grid_search([0]),
             # 'CLOSE_LOSE_PRICE_MODE': tune.grid_search([0]),  # 平仓止损
             # 'CLOSE_WIN_PRICE_MODE': tune.grid_search([0]),  # 平仓止盈
             "DEVIATION_SELF_PRICE": tune.grid_search([1]),  # 己方最优报价偏移Tick数
        }
        local_dir = os.path.join(signal_file_path,"../..", stock + "-" + strategy_name)
        os.system("rm -rf {}".format(local_dir))
        # 可视化查看超参调优结果
        # pip install  -U --trusted-host 168.7.17.225 -i http://168.7.17.225:8081/repository/pypi/simple/ tensorboardX==2.1
        # /opt/anaconda3/bin/tensorboard --logdir=StrategySignalT0Double-0933_fix_volume-0933_fix_volume/ --port 30115
        tune.run(objective, config=config,  search_alg=searcher,
                 name=stock, local_dir=local_dir)


def get_backtest_path(stock, online_path = False, **kwargs):
    # online_path是否读取线上信号文件路径
    if online_path:
        # dir_dict = {"688012.SH": "688012.SH_trade_v1.2"}
        # stock = "688012.SH"
        # signal_dir = f"/data/user/016869/AutoMiningFrame/trade_data/COO/{stock}-{dir_dict[stock]}/mm_ai_signal/online"
        # plot_save_dir = "/home/appadmin/"
        label_name = kwargs["label_name"]
        flag = False
        for exp_name in ["unite_semi_v1.1", "semi_v1.1", "computer_v1.1", "nation_innovation_v1.1"]:
            base_dir = f"/data/user/013150/trade_data/COO/{exp_name}"
            parquet_path = os.path.join(base_dir, f"signal_files/{label_name}-{stock}.parquet")
            if not os.path.exists(parquet_path):
                continue
            flag = True
            break
        if flag == False:
            raise Exception("无满足要求的线上文件格式！", parquet_path)
        signal_dir = parquet_path
        plot_save_dir = signal_dir
    else:
        exp_name = kwargs["exp_name"]
        version_alias = kwargs["version_alias"]
        label_name = kwargs["label_name"]
        signal_dir = f"/data/user/013150/exp_result/{exp_name}/{version_alias}/signal_files/{label_name}-{stock}.parquet"
        plot_save_dir = signal_dir

    return signal_dir, plot_save_dir


if __name__ == '__main__':
    strategy_params_total = {
        "StrategySignalT0Simple": {
            "ADJUST_VOLUME": False,
            "START_PERIOD": "09:33:00",
            "HOLD_POSITION_LIMIT": 1600,
            "SELL_POSITION_LIMIT": 15000,
            "optimal_price_stoploss_th": -3,
            'stoploss_th': -5,  # 订单单价止损比例
            "MARKET_TYPE": "Tick"
        },
        "StrategySignalT0AdjVol": {
            "ADJUST_VOLUME": False,
            "START_PERIOD": "09:33:00",
            "HOLD_POSITION_LIMIT": 3000,
            "SELL_POSITION_LIMIT": 15000,
            "optimal_price_stoploss_th":-3,
            'stoploss_th': -5,  # 订单单价止损比例
            "MARKET_TYPE": "Tick"
        }
    }

    # 运行示例： python3 parallel_tune_xbrain_backtest.py --symbol 000977.SZ --exp_name exp_l2p_000977.SZ --version xgboost_base --strategy StrategySignalT0Simple --artifacts
    parser = argparse.ArgumentParser(description='strategy tune.')
    # Add the desired command line arguments
    parser.add_argument('-s', '--symbol', type=str, default="000977.SZ", help='symbol')
    parser.add_argument('-exp', '--exp_name', type=str, help='Description for exp_name parameter')
    parser.add_argument('-v', '--version', type=str, default = "xgboost_base", help='version_alias, default xgboost_base')
    parser.add_argument('-x', '--strategy', type=str, default="StrategySignalT0Simple", help='xbrain strategy name')
    parser.add_argument('-l', '--label', type=str, default="LabelFirstPeak_th10_120s",help='label_name, default LabelFirstPeak_th10_120s.')
    parser.add_argument('-f','--artifacts', default = True, action='store_true', help='Use artifacts format')

    args = parser.parse_args()
    symbol = args.symbol
    symbol_list = []
    symbol_list.append(symbol)
    exp_name = args.exp_name
    version_alias = args.version
    label_name = args.label
    artifacts_format = args.artifacts
    strategy_class = eval(args.strategy)#StrategySignalT0AdjVol

    #################################
    strategy_name = strategy_class.__name__
    strategy_params = strategy_params_total[strategy_name]
    strategy_name_version = f"{strategy_name}-"
    pkeys = ["MARKET_TYPE", "START_PERIOD", "ADJUST_VOLUME", "SELL_POSITION_LIMIT", "HOLD_POSITION_LIMIT"]
    if strategy_name == "StrategySignalT0AdjVol":
        pkeys.extend(["optimal_price_stoploss_th", "stoploss_th"])
    for pkey in pkeys:
        strategy_name_version = strategy_name_version+str(strategy_params[pkey]).replace("-", "").replace(":", "")+"_"
    strategy_name_version = strategy_name_version.strip("_")
    print("strategy_name:", strategy_name_version)
    #################################

    t1 = time.time()
    success_list = []
    for stock in symbol_list:
        if ray.is_initialized():
            ray.shutdown()
        ray.init(num_cpus=30, ignore_reinit_error=True, local_mode=False,
                 _system_config={"object_spilling_config": json.dumps(
                     {"type": "filesystem", "params": {"directory_path": "/dfs/user/013150/tmp/"}, })},
                 log_to_driver=False
                 )
        if artifacts_format:
            signal_process_dir, plot_save_dir = get_backtest_path(stock,
                                                                  exp_name=exp_name,
                                                                  version_alias = version_alias,
                                                                  label_name = label_name)
        else:
            # 也可以指定自己的信号文件路径
            flag = False
            signal_process_dir, plot_save_dir = get_backtest_path(stock, online_path=True, label_name = label_name)

        parallel_tune(strategy_class, signal_process_dir, plot_save_dir, stock, strategy_name_version,
                      num_samples=1, start_date="20231115",end_date="20231220", **strategy_params)
        success_list.append(stock)
        print("总耗时：", time.time() - t1)

    print("success_list:", success_list)