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

trade_portfolio = '5161101+800'

today = datetime.datetime.now()
today_str = today.strftime('%Y%m%d')

is_combine_trade_and_capacity = True
is_cp_trade2_share = True
is_run_single_bt = True
is_run_trade_portfolio = True


# 将行情和参数整合
if is_combine_trade_and_capacity:
    combine_trade_and_capacity(today_str, today_str, trade_portfolio, is_run_trade_portfolio)
 
# 将整合好的行情和参数拷贝到共享目录   
if is_cp_trade2_share:
    temp_path = 'temp_'+ str(uuid.uuid1())
    if is_run_trade_portfolio:
        portfolios = ['h300', 'z500', trade_portfolio]
     else:
        portfolios =  ['h300', 'z500']
    for portfolio in portfolios:
        #  沪深300组合
        print(datetime.datetime.now(), "uploading {} trade and capacity to HDFS".format(portfolio))
        py.upload(temp_path + '/{}-{}/{}/'.format(today_str, today_str, portfolio), 
                  '/app/data/666888/BT_Trade_OrderCapacity/{}-{}/{}/'.format(today_str, today_str, portfolio))
        print(datetime.datetime.now(), "coping {} trade and trigger.json to Shared Directory".format(portfolio))
        py.copyToShare('$21/ModelProduction/20180901_end/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio),
                       temp_path + '/{}-{}/{}/'.format(today_str, today_str, portfolio))
    py.delete(temp_path, recursive=True)



if is_run_single_bt:
    executor_str = 'SignalExecutorTesting'
    max_tasks = 400
    # h300
    portfolio = 'h300'
    print("running bt of {}".format(portfolio))
    bt_dir = 'SHARE_21/ModelProduction/20180901_end/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio)
    symbols, init_quantities = hf.get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
    signal_csv_dir = 'SHARE_21/ModelProduction/20180901_end/signals/'
    trigger_json_dir = '666888/production_triggers/{}/'.format(portfolio)
    with py.open('production_triggers/{}/come_from.json'.format(portfolio), 'rb') as f:
        name = f.read()
        name = json.loads(name)
    hdfs_root = '666888/bt/'
    result_dir_name = 'bt-{}-{}-{}-use-{}/'.format(today_str, today_str, portfolio, name)
    output_dir = hdfs_root + result_dir_name
    overwrite_params = {'maxTurnoverPerOrder': 2000000, 'maxExposure': 8000000}
    BT_Single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir, overwrite_params, max_tasks)
    analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir)

    # z500 
    portfolio = 'z500'
    print("running bt of {}".format(portfolio))
    bt_dir = 'SHARE_21/ModelProduction/20180901_end/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio)
    symbols, init_quantities = hf.get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
    signal_csv_dir = 'SHARE_21/ModelProduction/20180901_end/signals/'
    trigger_json_dir = '666888/production_triggers/{}/'.format(portfolio)
    with py.open('production_triggers/{}/come_from.json'.format(portfolio), 'rb') as f:
        name = f.read()
        name = json.loads(name)
    hdfs_root = '666888/bt/'
    result_dir_name = 'bt-{}-{}-{}-use-{}/'.format(today_str, today_str, portfolio, name)
    output_dir = hdfs_root + result_dir_name
    overwrite_params = {'maxTurnoverPerOrder': 2000000, 'maxExposure': 8000000}
    BT_Single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir, overwrite_params, max_tasks)       
    analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir)
            
    # 5161101 research


    portfolio = trade_portfolio

    if is_run_trade_portfolio:
        # portfolio = '5161101+300'
        print("running bt of {}".format(portfolio))
        bt_dir = 'SHARE_21/ModelProduction/20180901_end/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio)
        symbols, init_quantities = hf.get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
        signal_csv_dir = 'SHARE_21/ModelProduction/20180901_end/signals/'
        trigger_json_dir = '666888/production_triggers/{}/'.format('5161101+800')
        with py.open('production_triggers/{}/come_from.json'.format('5161101+800'), 'rb') as f:
            name = f.read()
            name = json.loads(name)
        hdfs_root = '666888/bt/'
        result_dir_name = 'bt-{}-{}-{}-research-use-{}/'.format(today_str, today_str, portfolio, name)
        output_dir = hdfs_root + result_dir_name
        overwrite_params = {'maxTurnoverPerOrder': 2000000, 'maxExposure': 8000000}
        BT_Single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir, overwrite_params, max_tasks)
        analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir)
        
        # 5161101 production
        # portfolio = '5161101+300'
        print("running bt of {}".format(portfolio))
        bt_dir = 'SHARE_21/ModelProduction/20180901_end/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio)
        symbols, init_quantities = hf.get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
        signal_csv_dir = 'SHARE_21/ProductionLogSignals/20180901_end/'
        trigger_json_dir = '666888/production_triggers/{}/'.format('5161101+800')
        with py.open('production_triggers/{}/come_from.json'.format('5161101+800'), 'rb') as f:
            name = f.read()
            name = json.loads(name)
        hdfs_root = '666888/bt/'
        result_dir_name = 'bt-{}-{}-{}-production-use-{}/'.format(today_str, today_str, portfolio, name)
        output_dir = hdfs_root + result_dir_name
        overwrite_params = {'maxTurnoverPerOrder': 2000000, 'maxExposure': 8000000}
        BT_Single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir, overwrite_params, max_tasks)
        analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir)
                
                    
        print("end")