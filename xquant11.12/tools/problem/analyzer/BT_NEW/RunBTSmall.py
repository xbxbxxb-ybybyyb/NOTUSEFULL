import os
import sys
import json
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
from Utils_BT.HelperFunctions import get_symbols_quantities_from_json
from xquant.xqutils.xqfile import HDFSFile
from BT_NEW.BTSingle import bt_single
from BT_NEW.GetTrigger2Production import get_trigger2production
from analyze_result import analyze_result

hf = HDFSFile()

def run_bt():

    trade_portfolio = ["easy"]
    start_date = "20210104"
    end_date = "20210104"
    cv_start_date = "20201102"
    cv_end_date = "20201231"
    cv_next_date = "20210104"
    csv_param_date = "20200104"
    hs300 = False
    zz500 = False
    executor_str = "SignalExecutorEasy"
    mode = "Spark"
    max_tasks = 600

    if hs300:
        trade_portfolio.append("hs300")
    if zz500:
        trade_portfolio.append("zz500")

    for portfolio in trade_portfolio:
        print(" Running Backtest Of Portfolio: {} ".format(portfolio))

        bt_dir = '{}{}-{}-{}/'.format("cv/Stock/ds-", start_date, end_date, portfolio)
        symbols, init_quantities = get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
        amountSize = 5
        initialAmount = amountSize * 100000000
        if portfolio in ["hs300", "zz500", "cyb", "kcb"]:
            init_quantities = [int(initialAmount * xx / 10000) * 100 for xx in init_quantities]

        optimal_shift = [0. for _ in symbols]

        trigger_json_dir = 'production_triggers/Easy/'
        overwrite_params = {'maxTurnoverPerOrder': 1800000, 'maxExposure': 8000000}
        signal_csv_dir = "Easy_20201001"
        get_trigger2production(cv_start_date, cv_end_date, cv_next_date, csv_param_date, portfolio, signal_csv_dir,
                               executor_str, initialAmount, overwrite_params, False)
        with hf.open('production_triggers/Easy/come_from.json', 'rb') as f:
            name = f.read()
            name = json.loads(name)

        hdfs_root = "cv/Stock/Results"

        result_dir_name = "bt-{}-{}-{}-research-use-{}_{}/".format(start_date, end_date, portfolio, name, signal_csv_dir)
        output_dir = os.path.join(hdfs_root, result_dir_name)

        bt_single(symbols, init_quantities, optimal_shift, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir, mode, max_tasks, **overwrite_params)
        analyze_result(portfolio, "{}-{}".format(start_date, end_date), hdfs_root, result_dir_name, bt_dir)

        #######################################################################
        if portfolio == "EasyTrack":
            bt_signal_csv_dir = signal_csv_dir
            signal_csv_dir = "ProductionEasy0812Signals"
            overwrite_params = {'maxTurnoverPerOrder': 1800000, 'maxExposure': 8000000}
            csv_param_date = end_date
            assert start_date == end_date, " EasyTrack Only Support Single Day Mode "
            get_trigger2production(cv_start_date, cv_end_date, cv_next_date, csv_param_date, portfolio,
                                   bt_signal_csv_dir, executor_str, initialAmount, overwrite_params, True)
            with hf.open('production_triggers/Easy/come_from.json', 'rb') as f:
               name = f.read()
               name = json.loads(name)
            result_dir_name = "bt-{}-{}-{}-production-use-{}_{}/".format(start_date, end_date, portfolio, name, signal_csv_dir)
            output_dir = os.path.join(hdfs_root, result_dir_name)

            bt_single(symbols, init_quantities, optimal_shift, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir, mode, max_tasks, **overwrite_params)
            analyze_result(portfolio, "{}-{}".format(start_date, end_date), hdfs_root, result_dir_name, bt_dir)

    print("End")


if __name__ == '__main__':
    run_bt()
