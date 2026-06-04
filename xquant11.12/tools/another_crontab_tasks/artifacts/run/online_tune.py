import os
# from backtest.xbrain_backtest_simple import StrategySignalT0Simple
from backtest.xbrain_backtest_simple_vol_double import StrategySignalT0Simple
from xbrain import XBrain
import ray
import pandas as pd
from ray import tune
import json
import time
from artifacts.parse_format import parse_signal_txt, parse_xbrain_trade_records
from artifacts.backtest_save_and_evaluate import backtest_plot_signal_trade, backtest_trade_evaluation, backtest_trade_evaluation_agg, backtest_plot_trade_only
from artifacts.exp_artifacts import ExpArtifacts
import uuid


def xbrain_backtest_unit_day(signal_df, stock, backtest_date, **kwargs):
    save_uuid = uuid.uuid4()
    new_signal_file = f"/home/appadmin/signal_df_{save_uuid}.parquet"
    signal_df.to_parquet(new_signal_file)
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
    brain.add_strategy(StrategySignalT0Simple, signal_file=new_signal_file, **kwargs)

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


def parallel_tune(signal_file_path, plot_save_dir, stock, strategy_name, num_samples=1):
    if not os.path.exists(signal_file_path):
        print("ERRRO: signal_process_path_dir does not exist！")
        return

    def objective(params):
        failed_date_list = []
        trade_summary_list = []
        for backtest_date in days:
            try:
                sub_signal_file_path = os.path.join(signal_file_path, pd.to_datetime(backtest_date).strftime("%Y-%m-%d")+".txt")
                print("backtest_date", sub_signal_file_path)
                signal_df = parse_signal_txt(sub_signal_file_path)
                # signal_df = signal_df[signal_df["DATE"]==pd.to_datetime(backtest_date).strftime("%Y-%m-%d")]
                signal_df, trade_records_df, trade_summary = xbrain_backtest_unit_day(signal_df, stock, backtest_date, **params)
                if not trade_records_df.empty:
                    trade_summary = backtest_trade_evaluation(trade_records_df)
                    trade_summary_list.append(trade_summary)
            except:
                import traceback
                failed_date_list.append((backtest_date, traceback.print_exc()))

        print("failed_date_list:", failed_date_list)
        daily_trade_summary = pd.concat(trade_summary_list)
        daily_market_df = pd.read_parquet(tmp_market_path)
        total_trade_summary = backtest_trade_evaluation_agg(daily_trade_summary, daily_market_df)
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


    save_uuid = uuid.uuid4()
    os.system(f"rm -rf /tmp/tmp_market_{stock}*")
    # 加载行情数据
    tmp_market_path = f"/tmp/tmp_market_{stock}_{save_uuid}.parquet"
    file_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(file_path, "helper_get_marketdata.py")

    days = []
    for file in os.listdir(signal_file_path):
        if file.endswith("txt"):
            day = file.split(".")[0]
            if day >="2023-11-12" and day<="2023-11-28":
                days.append(day)
    days = [day.replace("-", "") for day in sorted(days)]
    print(days)
    if not os.path.exists(plot_save_dir):
        os.makedirs(plot_save_dir)
    start_date = days[0]
    end_date = days[-1]
    os.system(f"python3 {file_path} {stock} {start_date} {end_date} {tmp_market_path}")

    if True:
        config = {
             "init_open_long_th": tune.uniform(1.3, 2.8),
             "init_open_short_th": tune.uniform(-2.0, -1.3),
             'stoploss_th': tune.choice([-5, -3]),  # 订单单价止损比例
             # 'takeprofit_th': tune.grid_search([30]),  # 止盈比例
             'tradesize':tune.choice([400]),  # 每笔交易股数
             'OPEN_PRICE_MODE': tune.choice([0]),
             # 'CLOSE_LOSE_PRICE_MODE': tune.choice([0]),  # 平仓止损
             # 'CLOSE_WIN_PRICE_MODE': tune.choice([0]),  # 平仓止盈
             "DEVIATION_SELF_PRICE": tune.choice([1,2,3]),  # 己方最优报价偏移Tick数
             'HOLD_POSITION_LIMIT': tune.choice([1600,3000]),  # 单边敞口上限
             'SELL_POSITION_LIMIT': tune.choice([10000])  # 单日卖出底仓限制
        }

        from ray.tune.suggest.optuna import OptunaSearch
        optuna_search = OptunaSearch(metric='winmoney_after', mode='max')
        local_dir = os.path.join("/tmp/ray_result", stock+"-"+strategy_name)
        # 可视化查看超参调优结果
        # pip install  -U --trusted-host 168.7.17.225 -i http://168.7.17.225:8081/repository/pypi/simple/ tensorboardX==2.1
        # /opt/anaconda3/bin/tensorboard --logdir=StrategySignalT0Double-0933_fix_volume-0933_fix_volume/ --port 30115
        tune.run(objective, config=config, search_alg=optuna_search,
                 num_samples=num_samples, #resources_per_trial={'gpu': 0},
                 name = stock, local_dir = local_dir)
    else:
        from ray.tune.suggest.basic_variant import BasicVariantGenerator
        searcher = BasicVariantGenerator()
        config = {
             "init_open_long_th": tune.grid_search([2.2, 2.3, 2.4, 2.5]),
             "init_open_short_th": tune.grid_search([-1.5,-1.6, -1.7, -1.8]),
             'stoploss_th': tune.grid_search([-5, -3]),  # 订单单价止损比例
             # 'takeprofit_th': tune.grid_search([30]),  # 止盈比例
             'tradesize':tune.grid_search([400]),  # 每笔交易股数
             'OPEN_PRICE_MODE': tune.grid_search([0, -1]),
             # 'CLOSE_LOSE_PRICE_MODE': tune.grid_search([0]),  # 平仓止损
             # 'CLOSE_WIN_PRICE_MODE': tune.grid_search([0]),  # 平仓止盈
             "DEVIATION_SELF_PRICE": tune.grid_search([2, 3]),  # 己方最优报价偏移Tick数
             'HOLD_POSITION_LIMIT': tune.grid_search([5000, 8000]),  # 单边敞口上限
             'SELL_POSITION_LIMIT': tune.grid_search([10000, 20000])  # 单日卖出底仓限制
        }
        log_dir = "/tmp/ray_results/aaa"
        os.system("rm -rf {}".format(log_dir))
        tune.run(objective, config=config,  search_alg=searcher,
                 name='xbrain_T0_688012_1', local_dir=log_dir)


def get_backtest_path(online_path, stock, strategy_name, **kwargs):
    if online_path:
        dir_dict = {"688012.SH": "688012.SH_trade_v1.2"}
        stock = "688012.SH"
        signal_dir = f"/data/user/016869/AutoMiningFrame/trade_data/COO/{stock}-{dir_dict[stock]}/mm_ai_signal/online"
        # signal_probs_path = f"/data/user/016869/AutoMiningFrame/trade_data/COO/{stock}-{dir_dict[stock]}/{dir_dict[stock]}/th{label_th1}_table1.json"
        plot_save_dir = "/home/appadmin/"
    else:
        exp_name = kwargs["exp_name"]
        label_name = kwargs["label_name"]
        signal_dir = f"/data/user/013150/exp_result/{exp_name}/xgboost_base/signal_files/{label_name}-{stock}.parquet"
        plot_save_dir = signal_dir

    return signal_dir, plot_save_dir


if __name__ == '__main__':
    local_mode = False
    online_path = True  # 是否读取线上信号文件路径

    symbol_list = ["688012.SH"]

    params_file = "0933_fix_volume.json"
    strategy_name = "StrategySignalT0Double-{}".format(params_file.split(".")[0])
    strategy_name_version = strategy_name+"-"+params_file.split(".")[0]
    label_name = "LabelFirstPeak_th10_120s"
    exp_name = "exp_national_innovation_v1"

    t1 = time.time()
    for stock in symbol_list:
        signal_process_dir, plot_save_dir = get_backtest_path(online_path, stock, strategy_name,
                                                              exp_name=exp_name,
                                                              label_name = label_name)
        print(signal_process_dir, plot_save_dir)
        ray.init(num_cpus=30, ignore_reinit_error=True, local_mode=False,
                 _system_config={"object_spilling_config": json.dumps(
                     {"type": "filesystem", "params": {"directory_path": "/dfs/user/013150/tmp/"}, })},
                 log_to_driver=False
                 )
        parallel_tune(signal_process_dir, plot_save_dir, stock, strategy_name_version, num_samples=80)
        print("总耗时：", time.time() - t1)