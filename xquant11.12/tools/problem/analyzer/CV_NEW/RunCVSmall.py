import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
from Utils_CV.HelperFunctions import get_symbols_quantities_from_json, get_optimal_shift_from_json
from CV_NEW.CVSingle import cv
from analyze_result import analyze_result
from xquant.factordata import FactorData


def run_cv():

    trade_portfolio = ["easy"]
    start_date = "20210201"
    end_date = "20210326"
    next_trading_day = "20210329"
    hs300 = False
    zz500 = False
    signal_csv_dir = "Easy_20201001"
    executor_str = "SignalExecutorEasy"
    mode = "Spark"
    max_tasks = 600
    overwrite_params = {'maxTurnoverPerOrder': 1800000, 'maxExposure': 8000000}

    if hs300:
        trade_portfolio.append("hs300")
    if zz500:
        trade_portfolio.append("zz500")

    for portfolio in trade_portfolio:
        print(" Running CV of Portfolio: {} ".format(portfolio))

        bt_dir = "{}{}-{}_{}-{}-{}/".format("cv/Stock/ds-", start_date, end_date, next_trading_day, portfolio, signal_csv_dir)
        symbols, init_quantities = get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
        amountSize = 5
        initialAmount = amountSize * 100000000
        if portfolio in ["hs300", "zz500", "cyb", "kcb"]:
            init_quantities = [int(initialAmount * xx / 10000) * 100 for xx in init_quantities]

        if portfolio == "easy":
            hs300_list = sorted(FactorData().hset("INDEX", "20210222", "HS300")["stock"].tolist())
            for symbol, quantity in zip(symbols, init_quantities):
                if symbol in hs300_list:
                    init_quantities[symbols.index(symbol)] = 0.2 * quantity

        symbols_, optimal_shift = get_optimal_shift_from_json(bt_dir + "{}_optshift.json".format(portfolio))
        optimal_shift = [optimal_shift[symbols_.index(symbol)] for symbol in symbols]

        hdfs_root = "cv/Stock/Results"
        result_dir_name = 'cv-{}-{}_{}-{}-{}-{}-{}-{}-{}/'.format(start_date, end_date, next_trading_day, portfolio,
                                                               signal_csv_dir, executor_str,
                                                               initialAmount,
                                                               str(overwrite_params["maxTurnoverPerOrder"] // 10000),
                                                               str(overwrite_params["maxExposure"] // 10000))
        output_dir = os.path.join(hdfs_root, result_dir_name)

        cv(symbols, init_quantities, optimal_shift, bt_dir, signal_csv_dir, output_dir, executor_str, mode, max_tasks, **overwrite_params)
        analyze_result(portfolio, '{}-{}_{}'.format(start_date, end_date, next_trading_day), hdfs_root, result_dir_name, bt_dir)


if __name__ == "__main__":
    run_cv()
