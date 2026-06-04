# -*- coding: utf-8 -*-
"""
Created on 2019/2/11
@author: ZhuHaiGang
"""

from System.StrategyManagement import StrategyManagement
from System.Strategy import Strategy
from System.Func import execute
import time
import json
import sys
import os
import xquant.tensorflow as xt
import xquant
import datetime
from store_data_2_h5_multi import store_data
from BT_SIG.Infer_Signal import infer_signal
from copy_signal2share import copy_signal2share
from BT_SIG.get_trade import get_trade
from BT_SIG.get_order_capacity import get_order_capacity
from combine_trade_and_capacity import combine_trade_and_capacity
from xquant.pyfile import Pyfile
from multiprocessing import Pool
from BT_Single import BT_Single
from analyze_result import analyze_result
import Utils_BT.HelperFunctions as hf
import uuid
import xquant.tensorflow as xt


def DataPrepare(factorSetJsonFile, StartDateTime, EndDateTime, output_dir, stock_list):
    print(factorSetJsonFile, StartDateTime, EndDateTime, output_dir, stock_list)
    def createStrategyManagement(output_dir):
        strategyManagement = StrategyManagement()
        # 输出文件夹路径, 该路径为HDFS中的路径, 且事先必须不存在, here is the default value
        userdir = getUserDir()
        if (len(userdir) > 0):
            # strategyManagement.setDstDir(userdir+'/output/' + 'zhentou_20170624_20180824_remove_5_23')
            strategyManagement.setDstDir("{}/{}".format(userdir, output_dir))
            # strategyManagement.setTmpEnvDir(userdir)
        else:
            strategyManagement.setDstDir(
                '/analysis/xquant/666888/output/' + time.strftime("%Y%m%d%H%M%S", time.localtime()))
            # strategyManagement.setTmpEnvDir('/analysis/xquant/666888/')
        # Func.execute是默认值，可以不用设置, 后期如果要使用其他自定义函数, 则在这设置
        strategyManagement.setFunc(execute)
        # 默认按1天切分任务, 如果要加粗切分粒度, 则在这设置
        strategyManagement.setDaysInterval(1)
        return strategyManagement

    def createStrategy(para):
        # 不用加StrategyManagement参数
        strategy = Strategy()
        strategy.setStrategyName(para["StrategyName"])
        strategy.setTradingUnderlyingCode(para["TradingUnderlyingCode"])
        strategy.setFactorUnderlyingCode(para["FactorUnderlyingCode"])
        strategy.setParaFactor(para["FactorSet"])
        strategy.setParaTag(para["Tag"])
        strategy.setStartDateTime(para["StartDateTime"])
        strategy.setEndDateTime(para["EndDateTime"])
        return strategy    

    
    with open(factorSetJsonFile, 'r') as file:
        para = json.load(file)
        para["StartDateTime"] = int(StartDateTime)
        para["EndDateTime"] = int(EndDateTime)
        para["TradingUnderlyingCode"] = stock_list
        
        
        strategyManagement = createStrategyManagement(output_dir)
        strategy1 = createStrategy(para)
        # 单击版本中是在构造Strategy的init函数中进行register的, 这里必须额外调用registerStrategy方法
        strategyManagement.registerStrategy(strategy1)
        strategyManagement.start()
        dataPath = strategyManagement.getDstDir()
        print("Factors and Tags output: " + dataPath)
        return dataPath
    raise Exception('Factors initialization is failed!!!')


def getUserDir():
    for i in range(1, len(sys.argv)):
        if (str(sys.argv[i]) == "--user" and i < len(sys.argv)):
            return '/analysis/xquant/' + str(sys.argv[i + 1])


def main():
    import BT.ConfigMultiPortfolio as bt_config 
    config = bt_config.BacktestConfig()
    output_dir = config.factor_pickle_output_dir
    trade_portfolio = config.trade_portfolio
    today_str = config.today_str
    StartDateTime = config.StartDateTime
    EndDateTime = config.EndDateTime
    factor_config = config.factor_config
    py = Pyfile()

    is_calc_factor = False
    is_convert_factor_gen_signal = True
    
    if is_calc_factor:
        if py.exists(output_dir):
            print('delete old pickle factors from {}'.format(output_dir))
            py.delete(output_dir, recursive=True)
        configJsonfile = factor_config
        father_path = os.path.abspath(os.path.realpath(__file__) + os.path.sep + "../")
        paramPath = father_path + "/" + configJsonfile
        print("------Generating tags and factors using Spark------")
        stock_list = [[stock] for stock in config.codes]
        if False:
            stock_list = [["601318.SH"],["000418.SZ"]]
            StartDateTime, EndDateTime = "20190220093015", "20190221145659"
        
        inputDataPath = DataPrepare(paramPath, StartDateTime, EndDateTime, output_dir, stock_list)
        
    if is_convert_factor_gen_signal:
        print("convert factors into h5 files")
        number_stock = len(config.codes)
        STOCKS_PER_THREAD = int(number_stock/3)
        index_stock = 0
        pid = 0
        parallel_list = []
        while index_stock+STOCKS_PER_THREAD < number_stock:
             parallel_list.append(str(index_stock) + "-" +str(index_stock+STOCKS_PER_THREAD) +"-"+str(pid))
             pid = pid + 1
             index_stock = index_stock+STOCKS_PER_THREAD
        
        parallel_list.append(str(index_stock) + "-" +str(number_stock) +"-"+str(pid))

        param1 = {
            "parallel_list": parallel_list
            
           
            # "docker_version": "htsc:latest",
            # "type": "cpu"
        }
        print(parallel_list)
        print("start")
        xt.run_tensorflow("BT/gpu_work_h5_signal.py", json.dumps(param1))
        print("end") 
        
    if False:

        is_cp_signl2share = True
        is_run_single_bt = False
        is_run_month_bt = False
        signal_dates = []
        # signal_dates.append(config.today.strftime("%Y%m%d"))
        model_vers =  os.listdir("/app/data/666888/ModelProduction/2018-10-01/")
        signal_dates = ["20190212","20190213","20190214","20190215"]
        signal_dates = ["20190218","20190219","20190220","20190221"]
        signal_dates = ["20190222","2019025"]

        if is_cp_signl2share:
            upload_date = signal_dates  # empty means all; or e.g. ['20180901']
            symbols = []
            dest_path = '$21/ModelProduction/20181001_end/signals/'
            for mode_v in model_vers:
                src_path = '/app/data/666888/ModelProduction/2018-10-01/{}/ModelSignalDataSet/'.format(mode_v)
                print("coping signal of ", mode_v)
                copy_signal2share(upload_date, symbols, src_path, dest_path)

        if is_run_single_bt:
            executor_str = 'SignalExecutorTesting'
            max_tasks = 100
            Bt500And300 = False
            if Bt500And300:
                # h300
                portfolio = 'h300'
                print("running bt of {}".format(portfolio))
                bt_dir = 'SHARE_21/ModelProduction/20181001_end/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio)
                symbols, init_quantities = hf.get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
                signal_csv_dir = 'SHARE_21/ModelProduction/20181001_end/signals/'
                trigger_json_dir = '666888/production_triggers/{}/'.format(portfolio)
                with py.open('production_triggers/{}/come_from.json'.format(portfolio), 'rb') as f:
                    name = f.read()
                    name = json.loads(name)
                hdfs_root = '666888/bt/'
                result_dir_name = 'bt-{}-{}-{}-use-{}/'.format(today_str, today_str, portfolio, name)
                output_dir = hdfs_root + result_dir_name
                overwrite_params = {'maxTurnoverPerOrder': 2000000, 'maxExposure': 8000000}
                
                BT_Single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir,
                          overwrite_params, max_tasks)
                analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir)

                # z500
                portfolio = 'z500'
                print("running bt of {}".format(portfolio))
                bt_dir = 'SHARE_21/ModelProduction/20181001_end/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio)
                symbols, init_quantities = hf.get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
                signal_csv_dir = 'SHARE_21/ModelProduction/20181001_end/signals/'
                trigger_json_dir = '666888/production_triggers/{}/'.format(portfolio)
                with py.open('production_triggers/{}/come_from.json'.format(portfolio), 'rb') as f:
                    name = f.read()
                    name = json.loads(name)
                hdfs_root = '666888/bt/'
                result_dir_name = 'bt-{}-{}-{}-use-{}/'.format(today_str, today_str, portfolio, name)
                output_dir = hdfs_root + result_dir_name
                overwrite_params = {'maxTurnoverPerOrder': 2000000, 'maxExposure': 8000000}
                BT_Single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir,
                          overwrite_params, max_tasks)
                analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir)

            # 5161101 research
            if True:
                portfolio = "5161101+800"
                # for portfolio in trade_portfolio:
                    # if True:
                print("running bt of {}".format(portfolio))
                bt_dir = 'SHARE_21/ModelProduction/20181001_end/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio)
                symbols, init_quantities = hf.get_symbols_quantities_from_json(
                    bt_dir + '{}_quantity.json'.format(portfolio))
                signal_csv_dir = 'SHARE_21/ModelProduction/20181001_end/signals/'
                trigger_json_dir = '666888/production_triggers/{}/'.format(portfolio)
                with py.open('production_triggers/{}/come_from.json'.format(portfolio), 'rb') as f:
                    name = f.read()
                    name = json.loads(name)
                hdfs_root = '666888/bt/'
                result_dir_name = 'bt-{}-{}-{}-research-use-{}/'.format(today_str, today_str, portfolio, name)
                output_dir = hdfs_root + result_dir_name
                overwrite_params = {'maxTurnoverPerOrder': 2000000, 'maxExposure': 8000000}
                BT_Single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir,
                          overwrite_params, max_tasks)
                analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir)
                if False:
                    # 5161101 production
                    print("running bt of {}".format(portfolio))
                    bt_dir = 'SHARE_21/ModelProduction/20181001_end/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio)
                    symbols, init_quantities = hf.get_symbols_quantities_from_json(
                        bt_dir + '{}_quantity.json'.format(portfolio))
                    signal_csv_dir = 'SHARE_21/ProductionLogSignals/20181001_end/'
                    trigger_json_dir = '666888/production_triggers/{}/'.format(portfolio)
                    with py.open('production_triggers/{}/come_from.json'.format(portfolio), 'rb') as f:
                        name = f.read()
                        name = json.loads(name)
                    hdfs_root = '666888/bt/'
                    result_dir_name = 'bt-{}-{}-{}-production-use-{}/'.format(today_str, today_str, portfolio, name)
                    output_dir = hdfs_root + result_dir_name
                    overwrite_params = {'maxTurnoverPerOrder': 2000000, 'maxExposure': 8000000}
                    BT_Single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir,
                              overwrite_params, max_tasks)
                    analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir)

                if is_run_month_bt:
                    portfolio = trade_portfolio[0]
                    print("running bt of {}".format(portfolio))
                    bt_dir = 'SHARE_21/ModelProduction/20181001_end/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio)
                    symbols, init_quantities = hf.get_symbols_quantities_from_json(
                        bt_dir + '{}_quantity.json'.format(portfolio))
                    signal_csv_dir = 'SHARE_21/ModelProduction/20181001_end/signals/'
                    trigger_json_dir = '666888/production_triggers_month/{}/'.format(portfolio)
                    with py.open('production_triggers_month/{}/come_from.json'.format(portfolio), 'rb') as f:
                        name = f.read()
                        name = json.loads(name)
                    hdfs_root = '666888/bt/'
                    result_dir_name = 'bt-{}-{}-{}-month-research-use-{}/'.format(today_str, today_str, portfolio, name)
                    output_dir = hdfs_root + result_dir_name
                    overwrite_params = {'maxTurnoverPerOrder': 2000000, 'maxExposure': 8000000}
                    BT_Single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir,
                              overwrite_params, max_tasks)
                    analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir)

                    # 5161101 production
                    print("running bt of {}".format(portfolio))
                    bt_dir = 'SHARE_21/ModelProduction/20181001_end/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio)
                    symbols, init_quantities = hf.get_symbols_quantities_from_json(
                        bt_dir + '{}_quantity.json'.format(portfolio))
                    signal_csv_dir = 'SHARE_21/ProductionLogSignals/20181001_end/'
                    trigger_json_dir = '666888/production_triggers_month/{}/'.format(portfolio)
                    with py.open('production_triggers_month/{}/come_from.json'.format(portfolio), 'rb') as f:
                        name = f.read()
                        name = json.loads(name)
                    hdfs_root = '666888/bt/'
                    result_dir_name = 'bt-{}-{}-{}-month-production-use-{}/'.format(today_str, today_str, portfolio, name)
                    output_dir = hdfs_root + result_dir_name
                    overwrite_params = {'maxTurnoverPerOrder': 2000000, 'maxExposure': 8000000}
                    BT_Single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir,
                              overwrite_params, max_tasks)
                    analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir)

        print("end")


if __name__ == '__main__':
    main()
