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

py = Pyfile()

output_dir = 'output/all_300_500_20170101_20180101_10_all_test/'

def createStrategyManagement():
    strategyManagement = StrategyManagement()
    # 输出文件夹路径, 该路径为HDFS中的路径, 且事先必须不存在, here is the default value 
    userdir = getUserDir()
    if(len(userdir)>0):
        # strategyManagement.setDstDir(userdir+'/output/' + 'zhentou_20170624_20180824_remove_5_23')
        strategyManagement.setDstDir("{}/{}".format(userdir, output_dir))
        # strategyManagement.setTmpEnvDir(userdir)
    else:
        strategyManagement.setDstDir('/analysis/xquant/666888/output/' + time.strftime("%Y%m%d%H%M%S", time.localtime()))
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


def DataPrepare(factorSetJsonFile, StartDateTime, EndDateTime):
    with open(factorSetJsonFile, 'r') as file:
        para = json.load(file)
        # para["StartDateTime"] = int(StartDateTime)
        # para["EndDateTime"] = int(EndDateTime)
        strategyManagement = createStrategyManagement()
        strategy1 = createStrategy(para)
        # 单击版本中是在构造Strategy的init函数中进行register的, 这里必须额外调用registerStrategy方法
        strategyManagement.registerStrategy(strategy1)
        strategyManagement.start()
        dataPath = strategyManagement.getDstDir()
        print("Factors and Tags output: " + dataPath)
        return dataPath
    raise  Exception('Factors initialization is failed!!!')

def getUserDir():
    for i in range(1, len(sys.argv)):
        if(str(sys.argv[i])=="--user" and i < len(sys.argv)):
            return '/analysis/xquant/'+str(sys.argv[i+1])



def main():
    output_dir = 'output/all_300_500_20170101_20180101_10_all_test/'
    today = datetime.datetime.now()

    #today = datetime.datetime.now() - datetime.timedelta(days=1)
    today_str = today.strftime('%Y%m%d')
    # 正常都是1，周一的话，是3，节假日不确定
    predays = 1
    weekday = today.weekday()
    if weekday == 0:
        predays = 3



    # 生成tick， 下单容量，合并后，拷贝到hdfs
    is_get_trade = False
    is_get_capacity = False
    is_combine_trade_and_capacity = False
    is_cp_trade2_share = False
    
    
    
    
    
    is_calc_factor = True
    is_convert_factor = False
    is_gen_signal = False
    is_cp_signl2share = False
    is_run_CV = False
    is_run_single_bt = False
    is_log2signal = False
    is_reproduce_trade = False
    
    py = Pyfile()
    #####################################################
    # 计算开始结束的日期   
    # today = datetime.datetime.now()
    # today = datetime.datetime.now() - datetime.timedelta(days=1)
    # today_str = today.strftime('%Y%m%d')
    # weekday = today.weekday()
    # predays = 1
    # if weekday ==0:
        # predays = 3
        
     
        
        
    week_before = today - datetime.timedelta(days=predays)
    StartDateTime = "{}{}".format(week_before.strftime("%Y%m%d"), "093015") 
    EndDateTime = "{}{}".format(today.strftime("%Y%m%d"), "145659") 
    print("date from {} to {}".format(StartDateTime, EndDateTime))
    #############################################################################
    # 计算因子
    if is_calc_factor:
        if py.exists(output_dir):
            print('delete old pickle factors')
            py.delete(output_dir,recursive =True)
        configJsonfile = "AlgoConfig_test.py" 
        # configJsonfile = "AlgoConfig_test.py"   
        father_path=os.path.abspath(os.path.realpath(__file__)+os.path.sep+"../")
        paramPath = father_path +"/" + configJsonfile
        print("start generating tags and factors using Spark")
        inputDataPath = DataPrepare(paramPath, StartDateTime, EndDateTime)
    
    
    #########################################################################
    
    factorAddress = "/app/data/666888/AppleData"

    if is_convert_factor:
        print("convert factors into h5 files")
        # codes = py.listdir(output_dir)
        # codes = codes[2100:]
        # store_data(code=codes, absolutePath=factorAddress, factorAddress=output_dir)
        
        param1 = {
                    "parallel_list": [     
                                     
                            "0-200-0",
                            "200-400-1",
                            '400-600-2',
                            '600-800-3',
                            '800-1000-4',
                            '1000-1200-5',
                            '1200-1400-6',
                            # '1400-1600',
                            # '1600-1800',
                            # '1800-2000',
                            # '2000-2200'
                            ]
                                                                                                         
        }  

        param2 = {
                    "parallel_list": [     
                                     
                            "0-300-0",
                            "300-600-1",
                            '600-900-2',
                            '900-1200-3',
                            '1200-1500-4',
                            '1500-1800-5',
                            '1800-2100-6',
                            '2100-2400-7',
                            '2400-2700-8',
                            '2700-3000-9',
                            '3000-3300-10',
                            '3300-3468-11'
                            ]
                                                                                                         
        }  


        print("start")
        xt.run_tensorflow("gpu_work.py", json.dumps(param2))
        print("end")
    
    # model_vers = ["20181210"]
    model_vers =  ["20181201","20181208","20181209","20181210", "20181203"]
    #################################################################
    # 用历史行情计算的因子产生当日预测值
    if is_gen_signal:
        
        # import xquant.tensorflow as xt

        # xt.run_tensorflow("gpu_work.py")
        tagNames = [["1minLong", "1minShort"], ["2minLong", "2minShort"], ["5minLong", "5minShort"]]
        factorName = ['factorMAVolumeDistance40', 'factorDistanceBetweenVWAPPrice200', 'factorEmaSlicePressure', 
                      'factorTransPressureVol', 'factorDistanceToAvePrice', 'factorDistanceBetweenVWAPPrice100',
                      'factorOrderPressure', 'factorDistanceBetweenVWAPPrice40', 'factorDistanceBetweenVWAPPrice20', 
                      'factorMAVolumeDistance200', 'factorCrossPriceChangeSpeed', 'factorCrossPriceChangeRatio', 
                      'factorTransPressure', 'factorVolumeMagnification', 'factorMAVolumeDistance100', 'factorAccumSellPower', 
                      'factorAccumBuyPower', 'factorSpeed', 'factorMAVolumeDistance3', 'factorMAVolumeDistance20']
        test_start_date = today.strftime("%Y-%m-%d")
        # test_start_date = '2018-12-13'
        test_end_date = test_start_date
        
        #############################################
        # 5个不同版本的模型,分别在不同的目录
        
        for model_v in model_vers:
            modelPath = "/app/data/666888/ModelProduction/2018-09-01/{}/ModelSaved".format(model_v)
            # rstPath =  "/app/data/666888/Apple1.0Result/{}".format(model_v)
            rstPath =  "/app/data/666888/ModelProduction/2018-09-01/{}".format(model_v)
            code = os.listdir(modelPath)
            code.sort()
            # if len(code) < 40:
                # infer_signal(modelPath=modelPath, 
                         # absolutePath=rstPath,
                         # factorAddress=factorAddress, 
                         # tagNames=tagNames, factorName=factorName, 
                         # test_start_date=test_start_date, test_end_date=test_end_date, code=code)
            # else:
            processNum = 12
            baseNum = len(code) // processNum
            remains = len(code) % processNum
            pool = Pool(processes=processNum)
            idx = 0
            
            for index in range(processNum):
                if index < remains:
                    edx = idx + baseNum + 1
                else:
                    edx = idx + baseNum
                pool.apply_async(infer_signal, (modelPath, rstPath, factorAddress, tagNames, factorName, test_start_date, test_end_date, code[idx: edx], index))
                idx = edx
            pool.close()
            pool.join()
    
    signal_dates = []  # empty means all; or e.g. ['20180901']
    signal_dates.append(today.strftime("%Y%m%d"))
    
    
    #  获取行情用户撮合       
    if is_get_trade:
        outTradeDataPath = "/app/data/666888/TradeData/" 
        get_trade(outTradeDataPath, signal_dates)
       
    #  获取回测参数配置 
    if is_get_capacity:
        get_order_capacity(signal_dates)
        
    # 将行情和参数整合
    if is_combine_trade_and_capacity:
        combine_trade_and_capacity(today_str, today_str)
     
    # 将整合好的行情和参数拷贝到共享目录   
    if is_cp_trade2_share:
        temp_path = 'temp_'+ str(uuid.uuid1())
        # portfolios = ['5161101']
        portfolios = ['h300', 'z500', '5161101']
        for portfolio in portfolios:
            #  沪深300组合
            print(datetime.datetime.now(), "uploading {} signal to HDFS".format(portfolio))
            py.upload(temp_path + '/{}-{}/{}/'.format(today_str, today_str, portfolio), 
                      '/app/data/666888/BT_Trade_OrderCapacity/{}-{}/{}/'.format(today_str, today_str, portfolio))
            print(datetime.datetime.now(), "coping {} trade and trigger.json to Shared Directory".format(portfolio))
            py.copyToShare('$21/ModelProduction/20180901_end/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio),
                           temp_path + '/{}-{}/{}/'.format(today_str, today_str, portfolio))
        py.delete(temp_path, recursive=True)
     
    if is_cp_signl2share: 
        upload_date = signal_dates  # empty means all; or e.g. ['20180901']
        symbols = []
        dest_path = '$21/ModelProduction/20180901_end/signals/'
        for mode_v in model_vers:
            src_path = '/app/data/666888/ModelProduction/2018-09-01/{}/ModelSignalDataSet/'.format(mode_v)
            print("coping signal of ", mode_v)
            copy_signal2share(upload_date, symbols, src_path, dest_path) 
        
         
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
        portfolio = '5161101'
        print("running bt of {}".format(portfolio))
        bt_dir = 'SHARE_21/ModelProduction/20180901_end/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio)
        symbols, init_quantities = hf.get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
        signal_csv_dir = 'SHARE_21/ModelProduction/20180901_end/signals/'
        trigger_json_dir = '666888/production_triggers/{}/'.format(portfolio)
        with py.open('production_triggers/{}/come_from.json'.format(portfolio), 'rb') as f:
            name = f.read()
            name = json.loads(name)
        hdfs_root = '666888/bt/'
        result_dir_name = 'bt-{}-{}-{}-research-use-{}/'.format(today_str, today_str, portfolio, name)
        output_dir = hdfs_root + result_dir_name
        overwrite_params = {'maxTurnoverPerOrder': 2000000, 'maxExposure': 8000000}
        BT_Single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir, overwrite_params, max_tasks)
        analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir)
        
        # 5161101 production
        portfolio = '5161101'
        print("running bt of {}".format(portfolio))
        bt_dir = 'SHARE_21/ModelProduction/20180901_end/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio)
        symbols, init_quantities = hf.get_symbols_quantities_from_json(bt_dir + '{}_quantity.json'.format(portfolio))
        signal_csv_dir = 'SHARE_21/ProductionLogSignals/20180901_end/'
        trigger_json_dir = '666888/production_triggers/{}/'.format(portfolio)
        with py.open('production_triggers/{}/come_from.json'.format(portfolio), 'rb') as f:
            name = f.read()
            name = json.loads(name)
        hdfs_root = '666888/bt/'
        result_dir_name = 'bt-{}-{}-{}-production-use-{}/'.format(today_str, today_str, portfolio, name)
        output_dir = hdfs_root + result_dir_name
        overwrite_params = {'maxTurnoverPerOrder': 2000000, 'maxExposure': 8000000}
        BT_Single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir, overwrite_params, max_tasks)
        analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir)
                
                
    print("end")
    
    
if __name__ == '__main__':
    main()
