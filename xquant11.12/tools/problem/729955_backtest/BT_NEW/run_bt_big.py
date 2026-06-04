import json
import Utils_BT.HelperFunctions as hf
from BT_NEW.bt_single import bt_single
from xquant.pyfile import Pyfile
from analyze_result import analyze_result
from xquant.factordata import FactorData

py = Pyfile()
fd = FactorData()


def run_bt_big():
    trade_portfolio = ["WuKong"]
    executor_str = 'ProductionExecutor'
    max_tasks = 600
    sdate = "20200901"
    edate = "20200930"

    for portfolio in trade_portfolio:
        print("Running backtest of {}...".format(portfolio))
        bt_dir = ('666888/WuKong/bt_info/{}-{}_20200831/{}/'
                  .format(sdate, edate, portfolio))
        symbols, init_quantities = hf.get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))

        name = "WuKong"
        hdfs_root = '666888/bt/'

        signal_csv_dir = "big_cb_20200701_20200918_pure"
#        signal_csv_dir = 'big_cb_20200701_20200918_prod_lag0'
#        signal_csv_dir = 'big_cb_stock_20200701_20200413_prod_lag0'

        trigger_json_dir = '666888/production_triggers/{}/'.format(signal_csv_dir)
        result_dir_name = 'bt-{}-{}-{}-research-use-{}_{}/'.format(sdate, edate, portfolio, name, signal_csv_dir)
        output_dir = hdfs_root + result_dir_name
        overwrite_params = {'maxTurnoverPerOrder': 400000, 'maxExposure': 800000}
#        overwrite_params = {'maxTurnoverPerOrder': 1000000, 'maxExposure': 2000000}

        bt_single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir,
                  max_tasks, **overwrite_params)
        analyze_result(portfolio, sdate + "-" + edate, hdfs_root, result_dir_name, bt_dir)

#        signal_csv_dir = "WuKongProductionSignals"
#        result_dir_name = 'bt-{}-{}-{}-production-use-{}_{}/'.format(sdate, edate, portfolio, name, signal_csv_dir)
#        output_dir = hdfs_root + result_dir_name
#        overwrite_params = {'maxTurnoverPerOrder': 500000, 'maxExposure': 1000000}
##        overwrite_params = {'maxTurnoverPerOrder': 1000000, 'maxExposure': 2000000}

#        bt_single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir,
#                  max_tasks, **overwrite_params)
#        analyze_result(portfolio, sdate + "-" + edate, hdfs_root, result_dir_name, bt_dir)

    print("End")


if __name__ == '__main__':
    run_bt_big()
