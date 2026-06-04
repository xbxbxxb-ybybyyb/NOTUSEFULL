from ModelSystem.getAveTickVol import getVolMeanRaw
import numpy as np
import json
import datetime as dt    
import re     
import os  
from xquant.pyfile import Pyfile
 
def getMaxVolumePerOrder(symbol, date_timestamp, day_num): 
    pre_date = dt.datetime.fromtimestamp(date_timestamp - 24 * 3600).date().strftime('%Y%m%d')      
    return getVolMeanRaw(symbol, int(pre_date), day_num)
    
def get_params(absolutePath, combine_5161001, param_name):

    py = Pyfile()
    print (param_name)
    params = {}
    day_num = 20
    cur_date = dt.datetime(2018, 12, 13, 9, 30, 0).timestamp() 
    stock_dirs = py.listdir(combine_5161001)
    for st_dir in stock_dirs: 
        if not st_dir[:6].isdigit():
            continue
        stock_code = st_dir[:9]
        
        params[stock_code] = {}
        order_capacity = getMaxVolumePerOrder(stock_code, cur_date, day_num)  
        params[stock_code].update({"Datetime": dt.datetime.fromtimestamp(cur_date).date().strftime('%Y%m%d')})
        params[stock_code].update({"OrderCapacity": order_capacity}) 

        with py.open(combine_5161001 + "/" + stock_code + ".json", "rb") as f:
            triggers = f.read()
            triggers = json.loads(triggers) 
        if triggers['longTriggerRatio'] == 999999:
            params[stock_code].update({"OrderCapacity": 1.0})   
        params[stock_code].update({"TriggerRatio": triggers})
            
    with py.open(absolutePath + param_name, "wb") as f:
        json.dump(params, f)
        
        
def main():
    absolutePath = "TEST/BT_Trade_OrderCapacity/"
    combine_5161001 = "production_triggers/5161001"  
    param_name = "5161001_1214.json" 
    get_params(absolutePath, combine_5161001, param_name)
 
if __name__ == '__main__':
    main()