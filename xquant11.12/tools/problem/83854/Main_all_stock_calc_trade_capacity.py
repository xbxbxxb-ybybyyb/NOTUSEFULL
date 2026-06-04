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

output_dir = 'output/all_300_500_20170101_20180101_10_all4/'

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
        para["StartDateTime"] = int(StartDateTime)
        para["EndDateTime"] = int(EndDateTime)
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
    output_dir = 'output/all_300_500_20170101_20180101_10_all4/'
    trade_portfolio = '5161101+800'

    today = datetime.datetime.now() - datetime.timedelta(days=1)
    today_str = today.strftime('%Y%m%d')
    # 正常都是1，周一的话，是3，节假日不确定
    predays = 1
    weekday = today.weekday()
    if weekday == 0:
        predays = 3

    # 生成所有tick数据， 下单容量，合并后，拷贝到hdfs
    is_get_trade = False
    is_get_capacity = False
    
    
    
    
    
    
    
    
    
    
    
    # 固定组合数据生成
    is_combine_trade_and_capacity = True
    is_cp_trade2_share = True
    
    
    
   
    
    py = Pyfile()

 
        
    week_before = today - datetime.timedelta(days=predays)
    StartDateTime = "{}{}".format(week_before.strftime("%Y%m%d"), "093015") 
    EndDateTime = "{}{}".format(today.strftime("%Y%m%d"), "145659") 
    print("date from {} to {}".format(StartDateTime, EndDateTime))
    
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
        combine_trade_and_capacity(today_str, today_str, trade_portfolio)
     
    # 将整合好的行情和参数拷贝到共享目录   
    if is_cp_trade2_share:
        temp_path = 'temp_'+ str(uuid.uuid1())
        portfolios = ['5161101+800']
        #portfolios = ['h300', 'z500', trade_portfolio]
        for portfolio in portfolios:
            #  沪深300组合
            print(datetime.datetime.now(), "uploading {} trade and capacity to HDFS".format(portfolio))
            py.upload(temp_path + '/{}-{}/{}/'.format(today_str, today_str, portfolio), 
                      '/app/data/666888/BT_Trade_OrderCapacity/{}-{}/{}/'.format(today_str, today_str, portfolio))
            print(datetime.datetime.now(), "coping {} trade and trigger.json to Shared Directory".format(portfolio))
            py.copyToShare('$21/ModelProduction/20180901_end/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio),
                           temp_path + '/{}-{}/{}/'.format(today_str, today_str, portfolio))
        py.delete(temp_path, recursive=True)
     
 
                
    print("end")
    
    
if __name__ == '__main__':
    main()
