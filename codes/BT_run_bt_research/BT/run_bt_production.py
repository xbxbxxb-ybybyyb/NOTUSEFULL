import Utils.HelperFunctions as hf
from BT.bt_single import bt_single
from Analyzer.analyze_result import analyze_result
from xquant.factordata import FactorData
from xquant.pyfile import Pyfile


py = Pyfile()
fd = FactorData()
is_using_spark = False


def main():
    print("Start Run BT Big")
    bt_date = "20200811"
    dir_name = "bt_test"
    trade_portfolio = ["WuKong"]
    executor_str = 'ProductionExecutor2'
    max_tasks = 600
    sdate = bt_date
    edate = bt_date

    for portfolio in trade_portfolio:
        print("Running backtest of {}...".format(portfolio))
        bt_dir = 'BT_SP/CB/bt_info/{}-{}/{}'.format(sdate, edate, portfolio)  # 原始数据
        trigger_json_dir = 'BT_SP/CB/production_triggers/WuKong_{}'.format(bt_date)  # 触发阈值
        hdfs_root = dir_name
        if is_using_spark:
            bt_dir_spark = '011668/' + bt_dir
            trigger_json_dir = '011668/' + trigger_json_dir
            hdfs_root_spark = '011668/' + hdfs_root
        else:
            bt_dir_spark = bt_dir
            hdfs_root_spark = hdfs_root
        symbols, init_quantities = hf.get_symbols_quantities_from_json('{}/{}_quantity.json'.format(bt_dir_spark, portfolio), is_using_spark)
        # for i in range(len(symbols)):
        #     if symbols[i] == "128041.SZ":
        #         symbols, init_quantities = [symbols[i]], [init_quantities[i]]
        #         break
        name = "WuKong"

        signal_csv_dir = "big_cb_stock_20200301_20200413"  # 信号库名
        result_dir_name = 'bt-{}-{}-{}-research-use-{}_{}/'.format(sdate, edate, portfolio, name, signal_csv_dir)
        output_dir_spark = "{}/{}".format(hdfs_root_spark, result_dir_name)
        bt_single(symbols, init_quantities, bt_dir_spark, signal_csv_dir, output_dir_spark, executor_str, trigger_json_dir, max_tasks, is_using_spark)
        output_dir = "{}/{}".format(hdfs_root, result_dir_name)
        analyze_result(portfolio, sdate + "-" + edate, output_dir, result_dir_name, bt_dir, dir_name)

    print("End")


if __name__ == '__main__':
    main()
