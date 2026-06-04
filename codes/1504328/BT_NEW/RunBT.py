import os
import sys
import json
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
from Utils_BT.HelperFunctions import get_symbols_quantities_from_json
from xquant.xqutils.xqfile import HDFSFile
from BT_NEW.BTSingle import bt_single
from BT_NEW.GetTrigger2Production import get_trigger2production
from analyze_result import analyze_result
from DataIO.DataConfig import DataConfig

hf = HDFSFile()

def run_bt(freq):

    trade_portfolio = ["Stock1S-{}".format(freq)]
    start_date = "20210401"
    end_date = "20210731"
    cv_start_date = "20210301"
    cv_end_date = "20210331"
    cv_next_date = "20210401"
    signal_library = "BigEasy{}Signals".format(freq)
    executor_str = "SignalExecutorEasy"
    data_config = DataConfig()
    data_config.set_tick_hbase_library("Stock{}SL2PDataLib".format(freq))
    use_l2p = True
    mode = "Spark"
    max_tasks = 600

    for portfolio in trade_portfolio:
        print(" Running BackTest Of Portfolio: {} ".format(portfolio))

        bt_dir = '{}{}-{}-{}/'.format("cv/Stock/ds-", start_date, end_date, portfolio)
        symbols, init_quantities = get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
        optimal_shift = [0. for _ in symbols]

        trigger_json_dir = 'production_triggers/EverestSep/'
        overwrite_params = {'maxTurnoverPerOrder': 1800000, 'maxExposure': 8000000, "openWithdrawSeconds": 0.8}

        # get_trigger2production(cv_start_date, cv_end_date, cv_next_date, portfolio, signal_library,
        #                        executor_str, initialAmount, overwrite_params, is_use_csv=False)
        # with hf.open('production_triggers/Easy/come_from.json', 'rb') as f:
        #     name = f.read()
        #     name = json.loads(name)
        name = "BigEasy20210201_1S_Group"

        hdfs_root = "cv/Stock/Results"

        result_dir_name = "bt-{}-{}-{}-research-use-{}_{}/".format(start_date, end_date, portfolio, name, signal_library)
        output_dir = os.path.join(hdfs_root, result_dir_name)

        # init_quantities = [i * 1000 for i in init_quantities]
        # init_quantities = [1000]
        # symbols = ["000001.SZ"]
        # optimal_shift = [0]
        bt_single(symbols, init_quantities, optimal_shift, start_date, end_date, signal_library, bt_dir, output_dir,
                  executor_str, data_config, use_l2p, trigger_json_dir, mode, max_tasks, **overwrite_params)
        analyze_result(portfolio, "{}-{}".format(start_date, end_date), hdfs_root, result_dir_name, bt_dir)

    print("End")


if __name__ == '__main__':
    for freq in ["1"]:
        run_bt(freq)
