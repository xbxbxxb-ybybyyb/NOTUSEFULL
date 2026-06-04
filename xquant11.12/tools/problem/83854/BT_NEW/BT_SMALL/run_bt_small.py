import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
import json
import Utils_BT.HelperFunctions as hf
from BT_NEW.bt_single import bt_single
from BT_NEW.copy_signals_to_share import copy_signals_to_share
from xquant.pyfile import Pyfile
from analyze_result import analyze_result


def run_bt_small(is_cp_signal2share, is_bt_300_500, is_bt_production_signals):

    executor_str = 'SignalExecutorTesting'
    max_tasks = 300

    import BT_NEW.BT_SMALL.CONFIG_SMALL as bt_config_small
    config = bt_config_small.BacktestConfig()
    trade_portfolio = config.trade_portfolio
    today_str = config.today_str
    model_prefix = '20190101_48_end'
    py = Pyfile()

    if is_cp_signal2share:
        src_path = config.signal_path + "ModelSignalDataSet/"
        dst_path = 'ModelProduction/' + model_prefix + '/signals/'
        symbols = config.codes
        upload_date = [config.today_str]
        end_date = config.EndDateTime
        copy_signals_to_share(upload_date, symbols, src_path, dst_path, end_date, is_big=False)

    if is_bt_300_500:
        # h300
        portfolio = 'h300'
        print("Running backtest of {}...".format(portfolio))
        bt_dir = ('666888/ModelProduction/{}/bt_info/{}-{}/{}/'
                  .format(model_prefix, today_str, today_str, portfolio))
        symbols, init_quantities = hf.get_symbols_quantities_from_json(
            bt_dir + '{}_quantity.json'.format(portfolio)
        )
        signal_csv_dir = '666888/ModelProduction/' + model_prefix + '/signals/'
        trigger_json_dir = '666888/production_triggers/{}/'.format(portfolio)
        with py.open('production_triggers/{}/come_from.json'.format(portfolio), 'rb') as f:
            name = f.read()
            name = json.loads(name)
        hdfs_root = '666888/bt/'
        result_dir_name = 'bt-{}-{}-{}-use-{}/'.format(today_str, today_str, portfolio, name)
        output_dir = hdfs_root + result_dir_name
        overwrite_params = {'maxTurnoverPerOrder': 1800000, 'maxExposure': 5000000}

        bt_single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir,
                  max_tasks, **overwrite_params)
        analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir)

        # z500
        portfolio = 'z500'
        print("Running backtest of {}...".format(portfolio))
        bt_dir = ('666888/ModelProduction/{}/bt_info/{}-{}/{}/'
                  .format(model_prefix, today_str, today_str, portfolio))
        symbols, init_quantities = hf.get_symbols_quantities_from_json(
            bt_dir + '{}_quantity.json'.format(portfolio)
        )
        signal_csv_dir = '666888/ModelProduction/'+model_prefix+'/signals/'
        trigger_json_dir = '666888/production_triggers/{}/'.format(portfolio)
        with py.open('production_triggers/{}/come_from.json'.format(portfolio), 'rb') as f:
            name = f.read()
            name = json.loads(name)
        hdfs_root = '666888/bt/'
        result_dir_name = 'bt-{}-{}-{}-use-{}/'.format(today_str, today_str, portfolio, name)
        output_dir = hdfs_root + result_dir_name

        overwrite_params = {'maxTurnoverPerOrder': 1800000, 'maxExposure': 5000000}
        bt_single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir,
                  max_tasks, **overwrite_params)
        analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir)

    # 800
    for portfolio in trade_portfolio:
        print("Running backtest of {}...".format(portfolio))
        bt_dir = ('666888/ModelProduction/{}/bt_info/{}-{}/{}/'
                  .format(model_prefix, today_str, today_str, portfolio))
        symbols, init_quantities = hf.get_symbols_quantities_from_json(
            bt_dir + '{}_quantity.json'.format(portfolio)
        )
        signal_csv_dir = '666888/ModelProduction/'+model_prefix+'/signals/'
        trigger_json_dir = '666888/production_triggers/{}/'.format(portfolio)
        with py.open('production_triggers/{}/come_from.json'.format(portfolio), 'rb') as f:
            name = f.read()
            name = json.loads(name)
        hdfs_root = '666888/bt/'
        result_dir_name = 'bt-{}-{}-{}-research-use-{}/'.format(today_str, today_str, portfolio, name)
        output_dir = hdfs_root + result_dir_name

        overwrite_params = {'maxTurnoverPerOrder': 1800000, 'maxExposure': 5000000}
        bt_single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir,
                  max_tasks, **overwrite_params)
        analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir)

        if is_bt_production_signals:
            print("Running backtest of {} using production signals...".format(portfolio))
            bt_dir = ('666888/ModelProduction/{}/bt_info/{}-{}/{}/'
                      .format(model_prefix, today_str, today_str, portfolio))
            symbols, init_quantities = hf.get_symbols_quantities_from_json(
                bt_dir + '{}_quantity.json'.format(portfolio))
            signal_csv_dir = '666888/ProductionLogSignals/'+model_prefix+'/'
            trigger_json_dir = '666888/production_triggers/{}/'.format(portfolio)
            with py.open('production_triggers/{}/come_from.json'.format(portfolio), 'rb') as f:
                name = f.read()
                name = json.loads(name)
            hdfs_root = '666888/bt/'
            result_dir_name = 'bt-{}-{}-{}-production-use-{}/'.format(today_str, today_str, portfolio, name)
            output_dir = hdfs_root + result_dir_name
            overwrite_params = {'maxTurnoverPerOrder': 1800000, 'maxExposure': 5000000}
            bt_single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir,
                      max_tasks, **overwrite_params)
            analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir)

    print("End")


if __name__ == '__main__':
    run_bt_small(is_cp_signal2share=True, is_bt_300_500=True, is_bt_production_signals=True)
