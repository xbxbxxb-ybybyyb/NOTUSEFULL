import os
import pandas as pd
import time
from xquant.factordata import FactorData
from link import LinkMessage
import datetime
import time
lm = LinkMessage()
fd = FactorData()

def read_h5(file_path, parse_date, threshhold):

    file_name = file_path.strip().split("/")[-1]
    print(file_path)
    with pd.HDFStore(file_path,'r') as h5:
        factors = ['adjfactor', 'amt', 'close', 'free_float_shares', 'high', 'low', 'mkt_cap_ard', 'open', 'pct_chg', 'pre_close', 'total_shares', 'turn', 'volume', 'vwap']
        for key in factors:
            print(key)
            df = h5[key].loc[pd.Timestamp(parse_date)]
            all_shape = df.shape[0]
            if all_shape == 0:
               lm.sendMessage("[ERROR][金工-数据校验] {} 文件 {} 字段每日更新异常".format(file_name, key))
               raise Exception()
            not_null_shape = df[~df.isnull()].dropna().shape[0]
            percent = not_null_shape/all_shape
            print(not_null_shape, all_shape)
            if percent<=threshhold:
                lm.sendMessage("[ERROR][金工-数据校验] {} 文件 {} 字段每日更新异常,缺失值比例{}".format(file_name, key,percent))
                raise Exception()
                
def check_daily(file_type, parse_date, threshhold):
    file_trans = {'MD_ori':"/data/group/800080/warehouse/prod/MD/CHINA_STOCK/DAILY/WIND/MD_CHINA_STOCK_DAILY_WIND.h5"}
    file_path = file_trans[file_type]
    flag_path = "/data/group/800080/warehouse/prod/LOCAL_DATA/FLAG/{}".format(parse_date)
    while not os.path.exists(os.path.join(flag_path, parse_date+"_"+file_type+".success")):
        print("wait for MD_ori success")
        time.sleep(60)
    read_h5(file_path, parse_date, threshhold)
    with open(os.path.join(flag_path,  "{}_MD.success".format(parse_date)),'w') as file:
        pass 


if __name__ == "__main__":
    cur_date = datetime.datetime.now().strftime("%Y%m%d")
    parse_date = fd.tradingday(cur_date, -1)[0]
    parse_date = "20250220"
    threshhold = 0.1
#    file_path = '/data/user/999999/bak_h5_file/800002/MD_CHINA_STOCK_DAILY_WIND.h5'
    check_daily('MD_ori', parse_date, threshhold)
#    read_h5(file_path, parse_date, threshhold)
