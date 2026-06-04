import Utils_CV.HelperFunctions as hf
from CV_NEW.cv import cv
from analyze_result import analyze_result


def main():
    portfolio = 'WuKong'

    executor_str = 'ProductionExecutor'
    # executor_str = 'SignalExecutorCBTest'
    overwrite_params = {'maxTurnoverPerOrder': 400000, 'maxExposure': 800000}
    # overwrite_params = {'maxTurnoverPerOrder': 2000000, 'maxExposure': 4000000}

    # 日期
    today_str = "20200831"
    sdate_str = "20200701"
    edate_str = '20200831'

    # 路径
    bt_dir = ('666888/WuKong/bt_info/{}-{}_{}/{}/'
              .format(sdate_str, edate_str, today_str, portfolio))
    symbols, init_quantities = hf.get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
#    signal_csv_dir = "big_cb_stock_20200301_20200413_prod_lag0"
#    signal_csv_dir = "big_cb_stock_20200301_20200610_prod_lag0"
#    signal_csv_dir = "big_cb_stock_20200601_20200610_prod_lag0"
    signal_csv_dir = "big_cb_stock_20200701_20200413_prod_lag0"
#    signal_csv_dir = "big_cb_20200701_20200918_prod_lag0"
    signal_csv_dir = "big_cb_20200701_20200918_pure"
    hdfs_root = '666888/production/'
    result_dir_name = ('cv-{}-{}_{}-{}-{}-{}_{}/'
                       .format(sdate_str, edate_str, today_str, portfolio,
                               str(overwrite_params["maxTurnoverPerOrder"] // 10000),
                               str(overwrite_params["maxExposure"] // 10000), signal_csv_dir))
    output_dir = hdfs_root + result_dir_name

    print("Conducting CV for {}...".format(portfolio))
    cv(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, 600, **overwrite_params)
    analyze_result(portfolio, '{}-{}_{}'.format(sdate_str, edate_str, today_str), hdfs_root, result_dir_name, bt_dir)


if __name__ == '__main__':
    main()
