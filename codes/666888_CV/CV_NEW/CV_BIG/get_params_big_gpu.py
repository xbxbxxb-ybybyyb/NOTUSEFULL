from ModelSystem.getAveTickVol import getVolMeanRaw
import numpy as np
import json
import datetime as dt
import re
import os
def getMaxVolumePerOrder(symbol, date_timestamp, day_num):
    pre_date = dt.datetime.fromtimestamp(date_timestamp - 24 * 3600).date().strftime('%Y%m%d')
    return getVolMeanRaw(symbol, int(pre_date), day_num)
    
def main():
    absolutePath = "/data/user/666888/cvtriggers2020/big_test/"
    if not os.path.exists(absolutePath):
        os.makedirs(absolutePath)
    # TODO
    combine_5161001 = "/data/user/666888/BT_Results/sources/20191111-20200123_20200205/cv-20191111-20200123_20200205-big-180-800/"
    # TODO
    param_name = "big_0207.json"
    # param_name = "new_0117.json"
    print (param_name)
    params = {}
    day_num = 20
    # TODO
    cur_date = dt.datetime(2020, 2, 7, 9, 30, 0).timestamp()
    stock_dirs = os.listdir(combine_5161001)
    # TODO
    pre_param_name = "big_0202.json"
    # pre_param_name = "new_0112.json"
    if os.path.exists(absolutePath + pre_param_name):
        with open(absolutePath + pre_param_name, "r") as f:
            params = json.load(f)
    else:
        params = {}
    # params = {}
    stock_dirs.extend(list(params.keys()))
    stock_dirs = list(set(stock_dirs))
    stock_dirs.sort()
    for st_dir in stock_dirs:
        stock_code = st_dir
        if os.path.exists(combine_5161001 + "/" + stock_code + "/triggerRatio.json") or (not stock_code in params):
            params[stock_code] = {}
            with open(combine_5161001 + "/" + stock_code + "/triggerRatio.json", "r") as f:
                triggers = json.load(f)
            params[stock_code].update({"TriggerRatio": triggers})
            
        order_capacity = getMaxVolumePerOrder(stock_code, cur_date, day_num)
        params[stock_code].update({"Datetime": dt.datetime.fromtimestamp(cur_date).date().strftime('%Y%m%d')})
        params[stock_code].update({"OrderCapacity": order_capacity})
        
        if params[stock_code]["TriggerRatio"]['longTriggerRatio'] == 999999:
            params[stock_code].update({"OrderCapacity": 1.0})
        
        if 300000 <= int(stock_code[0: 6]) <= 399999:
            params[stock_code].update({"Holo": "true"})
        else:
            params[stock_code].update({"Holo": "false"})
    with open(absolutePath + param_name, "w") as f:
        json.dump(params, f)


if __name__ == "__main__":
    main()   
