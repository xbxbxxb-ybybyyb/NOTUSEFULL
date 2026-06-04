# @author 012807 @ 20190129
import System.GetXQuantData2 as get_tick_trans
import System.GetTradingDay as trading_day
import datetime as dt
import os
import h5py
import multiprocessing
import pandas as pd
import Analyzer.stock_pools as stock_pool
import tqdm
from multiprocessing import Pool

factor_list = ['factorMAVolumeDistance40', 'factorDistanceBetweenVWAPPrice200', 'factorEmaSlicePressure', 
                      'factorTransPressureVol', 'factorDistanceToAvePrice', 'factorDistanceBetweenVWAPPrice100',
                      'factorOrderPressure', 'factorDistanceBetweenVWAPPrice40', 'factorDistanceBetweenVWAPPrice20', 
                      'factorMAVolumeDistance200', 'factorCrossPriceChangeSpeed', 'factorCrossPriceChangeRatio', 
                      'factorTransPressure', 'factorVolumeMagnification', 'factorMAVolumeDistance100', 'factorAccumSellPower', 
                      'factorAccumBuyPower', 'factorSpeed', 'factorMAVolumeDistance3', 'factorMAVolumeDistance20',
                    
                       "1minLong", "1minShort", "2minLong", "2minShort", "5minLong", "5minShort",
                        "timestamp"
                    ]


config = {

    "stock_list": stock_pool.test_pool,
    "start_date": 20190115,
    "end_date":   20190404,
    "factor_list": factor_list,
    "factor_address": "/app/data/666888/AppleData",
    
    "result_path":    "/app/data/666888/FactorSummary/test_bu",
    "summary_name": "333.csv"
}

NUM_THREADS = 20


def _atom_summary(stock, date, factor_list, address="/app/data/666888/AppleData", is_tick=False):
    # 一个股票，一天， 所有因子的统计
    date = str(date)
    date = date[0:4]+"-"+date[4:6]+"-"+date[6:9]
    summarier = {}
    for factor in factor_list:
        path_factor = os.path.join(address, stock, factor)
        if not os.path.exists(path_factor):
            summarier[factor] = 0
        else:
            try:
                with h5py.File(path_factor, mode='r') as f:
                    # print("factor", factor, len(f[date]["block0_values"].value.ravel().tolist()))
                    
                    summarier[factor] = len(f[date]["block0_values"])
            except:
                summarier[factor] = 0
    startTime = dt.datetime.strptime(date.replace("-", ""), "%Y%m%d")
    endTime = dt.datetime.strptime(date.replace("-", ""), "%Y%m%d")
    if is_tick:
        tickData = get_tick_trans.getXQuantTickData2(stock, startTime, endTime, timeMode=2) # 左闭右闭
        summarier["tick"] = len(tickData[0]["Date"])
    
    summarier["stock"] = stock
    return summarier
    
    
def _one_day_summary(config, date, ver_bose=False):
    factor_address = config["factor_address"]
    stock_list = config["stock_list"]
    factor_list = config["factor_list"]

    daily_sumarray_pd = pd.DataFrame(index=config["stock_list"], columns= config["factor_list"])
    print(date)
    i = 0
    for stock in stock_list:
        if ver_bose:
            print("Checking", date, stock)
        i = i +1
        print(i, len(stock_list), date)
        one_day_one_stock_dict = _atom_summary(stock, date, factor_list)
        for factor in factor_list:
            daily_sumarray_pd.loc[stock, factor] = one_day_one_stock_dict[factor]
            
    save_path = os.path.join(config["result_path"], str(date)+".csv")
    daily_sumarray_pd.to_csv(save_path)
    # return daily_sumarray_pd




def main():
    is_check = True
    is_summary = True
    

    if is_check:
        trading_days = trading_day.getTradingDay(config["start_date"], config["end_date"])
        if not os.path.exists(config["result_path"]):
            os.makedirs(config["result_path"])
            
        multi_thread, total_thread = True, NUM_THREADS
        single_thread= False
    
        if single_thread:    
            for date in trading_days:
                _one_day_summary(config, date)
                

        if multi_thread:
            p1=Pool(total_thread)  #设定开启total_thread个进程
            for date in trading_days:
                p1.apply_async(func=_one_day_summary,args=(config,date,)) #设定异步执行任务

            p1.close()  #关闭进程池
            p1.join()   #阻塞进程池
            print("End Checking")     #打印结束语句
        


    if is_summary:
        trading_days = trading_day.getTradingDay(config["start_date"], config["end_date"])
        total_summary = pd.DataFrame(index=config["stock_list"], columns=trading_days)
        for date in trading_days:
            print(date)
            summary_pd_one_day = pd.read_csv(os.path.join(config["result_path"], str(date)+".csv"), index_col =0)

            for stock in config["stock_list"]:
                try:
                    total_summary.loc[stock, date] = summary_pd_one_day.loc[stock, config["factor_list"][0]]                

                    for factor in config["factor_list"]:
                        # 因子个数不相等，记录为-1
                        if summary_pd_one_day.loc[stock, factor] != summary_pd_one_day.loc[stock, config["factor_list"][0]]:
                            total_summary.loc[stock, date] = -1
                            break
                except:
                    # 抛异常，记录为-2
                    print("Wrong", stock, date)
                    total_summary.loc[stock, date] = -2
        
        print(os.path.join(config["result_path"], config["summary_name"]))               
        total_summary.to_csv(os.path.join(config["result_path"], config["summary_name"]))      
            
        
        
        
if __name__=='__main__':
    main()



