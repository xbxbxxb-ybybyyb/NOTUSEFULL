import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
import Utils_CV.HelperFunctions as hf
from CV_NEW.cv import cv
from analyze_result import analyze_result
#from modify_result_daily import main as mmm


def main():
    portfolio = 'hs300'
    portfolio = 'zz500'
#    portfolio = 'TEST'
#    portfolio = 'ModelTest20200607'
#    portfolio = 'ModelTest20200617'
#    portfolio = 'ModelTest20200708'
    executor_str = 'SignalExecutorTesting'
    overwrite_params = {'maxTurnoverPerOrder': 1800000, 'maxExposure': 8000000}

    # 日期
    edate_str = "20200430"
    sdate_str = '20200301'

    # 路径
#    bt_dir = '666888/AlgoGenzong2/bt_info/{}-{}/{}/'.format(sdate_str, edate_str, portfolio)
    bt_dir = '666888/AlgoModelCmp/bt_info/{}-{}/{}/'.format(sdate_str, edate_str, portfolio)
    symbols, init_quantities = hf.get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
    initialAmount = 5 * 100000000
#    initialAmount = 3 * 1000000
    init_quantities = [int(initialAmount * xx / 10000) * 100 for xx in init_quantities]
#    print(symbols[0], init_quantities[0])
#    init_quantities = [initialAmount * xx for xx in init_quantities]
#    print(symbols[0], init_quantities[0])

#    signal_csv_dir = "big_20191101_universe_20200414_simple_131"
    signal_csv_dir = "SeparateModelSignals"
    # signal_csv_dir = "SeparateModelTransformerSignals"
#    signal_csv_dir = "Model20200501"
    # signal_csv_dir = "Model20191101_universe_48_simple"
    # signal_csv_dir = "Model20191101_universe_133_20200325_simple_tmp"
    # signal_csv_dir = "Model20191101_93_4"
#    signal_csv_dir = "big_20191101_universe_20200414_simple_131_no_800"
#    signal_csv_dir = "big_20191101_universe_20200414_simple_131_high"
#    signal_csv_dir = "SeparateModelSignals0803"
    signal_csv_dir = "EasyTransformerCPUSignals"
    signal_csv_dir = "SeparateModelSignals"
    hdfs_root = '666888/AlgoModelCmp/bt_results/'
    result_dir_name = ('cv-{}-{}-{}-{}-{}-{}_{}/'
                       .format(sdate_str, edate_str, portfolio, initialAmount,
                               str(overwrite_params["maxTurnoverPerOrder"] // 10000),
                               str(overwrite_params["maxExposure"] // 10000), signal_csv_dir))
    output_dir = hdfs_root + result_dir_name

    print("Conducting CV for {}...".format(portfolio))
    cv(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, 600, **overwrite_params)
    analyze_result(portfolio, '{}-{}'.format(sdate_str, edate_str), hdfs_root, result_dir_name, bt_dir)
#    mmm(portfolio, sdate_str, edate_str, initialAmount, result_dir_name)


if __name__ == '__main__':
    main()
