import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
import json
import Utils_BT.HelperFunctions as hf
from BT_NEW.bt_single import bt_single
from BT_NEW.copy_signals_to_share import copy_signals_to_share
from xquant.pyfile import Pyfile
from analyze_result import analyze_result
from modify_result_daily import main as mmm


def run_bt_big():
    executor_str = 'SignalExecutorTesting'
    portfolio = "hs300"
#    portfolio = "zz500"
#    portfolio = "TEST"

    edate_str = "20200831"
    sdate_str = '20200501'

    max_tasks = 600
    py = Pyfile()

    print("Running backtest of {}...".format(portfolio))
#    bt_dir = '666888/AlgoGenzong2/bt_info/{}-{}/{}/'.format(sdate_str, edate_str, portfolio)
    bt_dir = '666888/AlgoModelCmp/bt_info/{}-{}/{}/'.format(sdate_str, edate_str, portfolio)
    symbols, init_quantities = hf.get_symbols_quantities_from_json(
        bt_dir + '{}_quantity.json'.format(portfolio)
    )
    # initialAmount = 3 * 100000000
    initialAmount = 5 * 100000000
    # initialAmount = 10 * 100000000
    # initialAmount = 15 * 100000000
    init_quantities = [int(initialAmount * xx / 10000) * 100 for xx in init_quantities]
#    print(symbols[0], init_quantities[0])
#    initialAmount = 3 * 1000000
#    init_quantities = [initialAmount * xx for xx in init_quantities]

    # signal_csv_dir = "Model20190301"
#    signal_csv_dir = "Model20191101"
    # signal_csv_dir = "SeparateModelSignals"
    # signal_csv_dir = "SeparateModelTransformerSignals"
    # signal_csv_dir = "Model20191101_48_ray"
    # signal_csv_dir = "Model20191101_93_4"
    # signal_csv_dir = "Model20191101_universe_48_simple"
    # signal_csv_dir = "Model20191101_universe_133_20200325_simple"
    signal_csv_dir = "big_20191101_universe_20200414_simple_131"
#    signal_csv_dir = "big_20191101_universe_20200414_simple_131_no_800"
#    signal_csv_dir = "big_20191101_universe_20200414_simple_131_high"
    signal_csv_dir = "EasyTransformerCPUSignals"
    trigger_json_dir = '666888/AlgoModelCmpTriggers/{}/{}/{}/'.format(signal_csv_dir, portfolio, initialAmount)
    with py.open('AlgoModelCmpTriggers/{}/{}/{}/come_from.json'.format(signal_csv_dir, portfolio, initialAmount), 'rb') as f:
        name = f.read()
        name = json.loads(name)

    hdfs_root = '666888/AlgoModelCmp/bt_results/'
    result_dir_name = 'bt-{}-{}-{}-{}/'.format(sdate_str, edate_str, portfolio, name)
    output_dir = hdfs_root + result_dir_name
    overwrite_params = {'maxTurnoverPerOrder': 1800000, 'maxExposure': 8000000}

    bt_single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir,
              max_tasks, **overwrite_params)
    analyze_result(portfolio, '{}-{}'.format(sdate_str, edate_str), hdfs_root, result_dir_name, bt_dir)
    mmm(portfolio, sdate_str, edate_str, initialAmount, result_dir_name)

    print("End")


if __name__ == '__main__':
    run_bt_big()
