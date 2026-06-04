#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/3/20 9:09
# 获取股票过去一段时间的活跃度指标和平均成交额
import os
import json
from DataIO.Utils import get_trading_day
from xquant.xqutils.helper import multicore_init
ORDER_CAPACITY_PATH = "/data/user/015629/OrderCapacity/"


def load_high_vol_params(code, date_list):
    file_name = os.path.join(ORDER_CAPACITY_PATH, "{}/HighVol.json".format(code))
    try:
        with open(file_name, "rb") as f:
            data = f.read()
            data = json.loads(data).get("HighVol")
        high_vol_dict = {date: data.get(date) for date in date_list}
    except:
        high_vol_dict = dict()
    return high_vol_dict

def get_high_vol(code_list, start_date, end_date):
    """"""
    date_list = get_trading_day(start_date, end_date)

    high_vol_dict = dict()

    for code in code_list:
        code_high_vol = load_high_vol_params(code, date_list)
        high_vol_dict.update({code: code_high_vol})

    return high_vol_dict

def get_high_vol_speed(code_list, start_date, end_date, process_num=20):
    import multiprocessing as mp

    process_num = min(len(code_list), process_num)
    assert multicore_init() == True
    pool = mp.Pool(processes=process_num)

    para_split = []

    for ii in range(process_num):
        para_split.append([])

    count = 0
    for ii in range(len(code_list)):
        para_split[count].append(code_list[ii])
        count = count + 1
        if count >= process_num:
            count = 0

    multiProcessResult = []
    for ii in range(para_split.__len__()):
        result = pool.apply_async(get_high_vol, (para_split[ii], start_date, end_date, ))
        multiProcessResult.append(result)
    pool.close()
    pool.join()

    high_vol_dict = {}
    for result in multiProcessResult:
        high_vol_dict.update(result.get())

    return high_vol_dict


if __name__=="__main__":
    code_list = ["000001.SZ", "000725.SZ"]
    start_date = "20210101"
    end_date = "20210301"
    high_vol = get_high_vol(code_list, start_date, end_date)
    # high_vol = get_high_vol_speed(code_list, start_date, end_date)
    print(high_vol)








