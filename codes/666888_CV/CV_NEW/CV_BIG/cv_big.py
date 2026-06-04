import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
import datetime as dt
import Utils_CV.HelperFunctions as hf
from CV_NEW.cv import cv
from analyze_result import analyze_result


def main():
    # portfolio = 'big_All'
    portfolio = 'big'
    # portfolio = 'New_All'
    executor_str = 'SignalExecutorTesting'
    model_ver_str = "20190101_48_end"
    overwrite_params = {'maxTurnoverPerOrder': 1800000, 'maxExposure': 8000000}

    # 日期
    today_str = "20200205"
    edate_str = "20200123"
    sdate_str = '20191111'

    # 路径
    bt_dir = ('666888/ModelProduction/{}/bt_info/{}-{}_{}/{}/'
              .format(model_ver_str, sdate_str, edate_str, today_str, portfolio))
    symbols, init_quantities = hf.get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
    # signal_csv_dir = '666888/ModelProduction/{}/universe/'.format(model_ver_str)
    signal_csv_dir = "Model20190101_48"
    # signal_csv_dir = "Model20191101_48"
    hdfs_root = '666888/production/'
    result_dir_name = ('cv-{}-{}_{}-{}-{}-{}/'
                       .format(sdate_str, edate_str, today_str, portfolio,
                               str(overwrite_params["maxTurnoverPerOrder"] // 10000),
                               str(overwrite_params["maxExposure"] // 10000)))
    output_dir = hdfs_root + result_dir_name

    print("Conducting CV for {}...".format(portfolio))
    # cv(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, max_tasks, **overwrite_params)
    cv(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, len(symbols), **overwrite_params)
    analyze_result(portfolio, '{}-{}_{}'.format(sdate_str, edate_str, today_str), hdfs_root, result_dir_name, bt_dir)


if __name__ == '__main__':
    main()
