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
from xquant.pyfile.ftp import pyfileFTP
import pandas as pd

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

    # 生成所有tick数据， 下单容量，合并后，拷贝到hdfs
    is_get_trade = True
    is_get_capacity = True
    
    # 固定组合数据生成
    is_combine_trade_and_capacity = True
    is_cp_trade2_share = True
    
   
    
    signal_dates = []  # empty means all; or e.g. ['20180901']
    signal_dates.append(config.today.strftime("%Y%m%d"))
    
    #  获取行情用户撮合       
    if is_get_trade:
        outTradeDataPath = "/app/data/666888/TradeData/" 
        get_trade(outTradeDataPath, signal_dates, stock_list=config.codes)
       
    #  获取回测参数配置 
    if is_get_capacity:
        signal_dates.sort()
        get_order_capacity(signal_dates, stock_list=config.codes)
        
        
        
    # 将行情和参数整合
    if is_combine_trade_and_capacity:
        for portfolio in trade_portfolio:
            import combine_trade_and_capacity as prepare_tick_capacity
            print("combining {}'s trade and capacity".format("zz500 and hs300"))

            prepare_tick_capacity.combine(prepare_tick_capacity.target_code_500, 
                                          prepare_tick_capacity.volume_500, 
                                          today_str, today_str, 'z500')
            prepare_tick_capacity.combine(prepare_tick_capacity.target_code_300, 
                                          prepare_tick_capacity.volume_300, 
                                          today_str, today_str, 'h300')
                                        
            print("combining {}'s trade and capacity".format(portfolio))                             
            ftp = pyfileFTP()
            file_name = "{}_{}.xlsx".format(today_str, portfolio)
            ftp.downloadFile("666888/"+file_name, "/app/data/666888/ftp_uploads/"+file_name)
            df = pd.read_excel("/app/data/666888/ftp_uploads/"+file_name)
            print(df)
            codes = list([_code for _code in df.iloc[:, 0]] )
            volumes = list([int(_code) for _code in df.iloc[:, 3]] )
            prepare_tick_capacity.combine(codes, volumes, today_str, today_str, portfolio)  
            
        #combine_trade_and_capacity(today_str, today_str, trade_portfolio)
     
    # 将整合好的行情和参数拷贝到共享目录   
    if is_cp_trade2_share:
        temp_path = 'temp_'+ str(uuid.uuid1())
        portfolios = ['h300', 'z500']
        portfolios.extend(trade_portfolio)
        
        for portfolio in portfolios:
            print(datetime.datetime.now(), "uploading {} trade and capacity to HDFS".format(portfolio))
            py.upload(temp_path + '/{}-{}/{}/'.format(today_str, today_str, portfolio), 
                      '/app/data/666888/BT_Trade_OrderCapacity/{}-{}/{}/'.format(today_str, today_str, portfolio))
            print(datetime.datetime.now(), "coping {} trade and trigger.json to Shared Directory".format(portfolio))
            py.copyToShare('$21/ModelProduction/20181001_end/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio),
                           temp_path + '/{}-{}/{}/'.format(today_str, today_str, portfolio))
        py.delete(temp_path, recursive=True)
     
 
                
    print("end")
    
    
if __name__ == '__main__':
    main()
