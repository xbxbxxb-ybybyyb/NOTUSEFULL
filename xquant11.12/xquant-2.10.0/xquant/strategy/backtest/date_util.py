# -*- coding: utf-8 -*-
"""
Created on Thu Oct 18 15:45:21 2018
@author: 013150
"""

import datetime
import re
import sys
    

def time_standard(time):
    '''
    将输入日期格式转化成YYYYMMDD统一格式
    **参数**
            time：str或datetime类型的时间
            
    **返回**
            
            YYYYMMDD统一格式的时间
    '''
    if time == None:
        sys.exit()
    if isinstance(time, str):
        if len(re.findall("\d{4}-\d{2}-\d{2}",time))!=0:
            time = re.sub("-","", time)
        elif len(re.findall("\d{8}",time))!=0:
            pass
        else:
            print("请输入正确的str时间格式！YYYY-MM-DD或YYYYMMDD")
            sys.exit()
    elif isinstance(time, datetime.datetime):
        time = time.strftime("%Y%m%d")
    else:
        print("请输入正确的时间格式,str或datetime类型")
        sys.exit()
    
    return time

"""
从回测区间中，根据不同的日期频率选取调仓日
refresh_rate:   int
                Weekly(1)
                Monthly(1,-1)
"""
def get_warehouse_transfer_day(startTime, endTime, refresh_rate):
     from xquant.thirdpartydata.factor import FactorData
     from dateutil.relativedelta import relativedelta
     fa = FactorData(timeout=60*30)

     assert fa.tradingDay(startTime, endTime)!= None, "指定回测区间无股票交易日！"
     tradingDates = fa.tradingDay(startTime,endTime)[::-1]
     tradingDates = [str(day) for day in tradingDates]

     # print(refresh_rate.weekday)
     target_term = []
     if isinstance(refresh_rate, int):
         target_term = tradingDates[::refresh_rate]#调用的handleData的交易日期
     elif isinstance(refresh_rate, Weekly):
         for d in tradingDates:
             if refresh_rate.weekday==datetime.datetime.strptime(str(d), "%Y%m%d").weekday()+1:
                 target_term.append(str(d))
     elif isinstance(refresh_rate, Monthly):
          startTradingDay = datetime.datetime.strptime(startTime[:-2]+"01", "%Y%m%d")#该月第一天
          endTradingDay = startTradingDay+relativedelta(months=1)-datetime.timedelta(1)#该月最后一天
          #对时间区间内，取月交易日
          while startTradingDay<datetime.datetime.strptime(endTime, "%Y%m%d"):
             tradingDatesMonthly = fa.tradingDay(int(startTradingDay.strftime("%Y%m%d")),
                                                 int(endTradingDay.strftime("%Y%m%d")))[::-1]
             first_day = tradingDatesMonthly[refresh_rate.start-1]
             if refresh_rate.end<0:
                 second_day = tradingDatesMonthly[refresh_rate.end]
             else:
                 second_day = tradingDatesMonthly[refresh_rate.end-1]
             if first_day>=int(startTime) and first_day<=int(endTime):
                 target_term.append(str(first_day))#加入该月第一个调仓日
             if second_day>=int(startTime) and second_day<=int(endTime):
                 target_term.append(str(second_day))#加入该月第二个调仓日
             startTradingDay = endTradingDay+datetime.timedelta(1)#下个月第一天
             endTradingDay = startTradingDay+relativedelta(months=1)-datetime.timedelta(1)#下个月最后一天

     target_term = [int(day) for day in target_term]
     return target_term



class Weekly:
    def __init__(self,weekday):
        self.weekday = weekday
        
class Monthly:
    def __init__(self, start, end):
        self.start = start
        self.end = end

if __name__=="__main__":
    print(time_standard("2018-10-19"))
    print(time_standard(datetime.datetime.now()))
    print(get_warehouse_transfer_day("20160101", "20160130", Weekly(1)))
    print(get_warehouse_transfer_day("20160101", "20170130", Monthly(2,-1)))