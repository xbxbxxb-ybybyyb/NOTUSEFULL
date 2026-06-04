import json
import Utils_CV.HelperFunctions as hf
from CV_NEW.cv import cv
from analyze_result import analyze_result


def main():
    portfolio = 'WuKong'

    executor_str = 'ProductionExecutor'
    # executor_str = 'SignalExecutorCBTest'
#    overwrite_params = {'maxTurnoverPerOrder': 1000000, 'maxExposure': 2000000}
    overwrite_params = {'maxTurnoverPerOrder': 500000, 'maxExposure': 1000000}
    overwrite_params = {'maxTurnoverPerOrder': 300000, 'maxExposure': 600000}
    overwrite_params = {'maxTurnoverPerOrder': 200000, 'maxExposure': 400000}
    overwrite_params = {'maxTurnoverPerOrder': 100000, 'maxExposure': 200000}

    # 日期
    today_str = "20201104"
    sdate_str = "20200825"
    edate_str = '20201102'

#    with open("/data/user/011668/bt_params/params/{}.json".format(today_str), "r") as f:
#        risk_params = json.load(f)

    # 路径
    bt_dir = ('666888/WuKong/bt_info/{}-{}_{}/{}/'
              .format(sdate_str, edate_str, today_str, portfolio))
    symbols, init_quantities = hf.get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
    signal_csv_dir = "big_cb_stock_20200701_20200413_prod_lag0"
    hdfs_root = '666888/WuKong/bt_results/'
    result_dir_name = ('cv-{}-{}_{}-{}-{}-{}_{}/'
                       .format(sdate_str, edate_str, today_str, portfolio,
                               str(overwrite_params["maxTurnoverPerOrder"] // 10000),
                               str(overwrite_params["maxExposure"] // 10000), signal_csv_dir))
    output_dir = hdfs_root + result_dir_name

    print("Conducting CV for {}...".format(portfolio))
#    cv(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, risk_params, 600, **overwrite_params)
    cv(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, None, 600, **overwrite_params)
    analyze_result(portfolio, '{}-{}_{}'.format(sdate_str, edate_str, today_str), hdfs_root, result_dir_name, bt_dir)


if __name__ == '__main__':
    main()
