# -*- coding: utf-8 -*-
"""
Created on Wed Aug 15 10:15:50 2018
@author: 013150
"""

import xquant1.quant as xq
import numpy as np
import pandas as pd
from .data_util import factor_major_transfer

#%% (1)股票列表获取
def get_stockList(endTime):
    stockInfo = xq.hset(xq.PlateType.MARKET, endTime, xq.MarketType.ALLA)#A股股票
    stockList = xq.stockFilter(stockInfo[0], endTime, xq.StockFilterType.STSPEND)#去除ST和当日停牌
    return stockList
    
#%% （2）1.因子值获取，以月为截面期;2.标签获取，超额收益
"""
根据股票列表，获取70个因子
输入：stockList股票列表，startTime获取开始时间，endTime获取结束时间
输出：{key：factor，value：df,行为日期，列为code}
"""
def get_factors(stockList, startTime=20110131, endTime=20170731):
    #查询时间
    tradingDate = xq.tradingDay(startTime, endTime, frequencyType=xq.FrequencyType.MONTH, dayType=xq.DayType.LASTDAY)
    #估值类因子
    valuationFactors = [xq.Factors.pe_ttm, xq.Factors.s_val_pb_new, xq.Factors.ps_ttm, xq.Factors.pcf_ncf_ttm, xq.Factors.pcf_ocf_ttm]
    #财务质量
    finanQlyFactors = [xq.Factors.roe_ttm, xq.Factors.roa_ttm, xq.Factors.grossmargin_ttm, xq.Factors.assetsturn]
    #杠杆
    levelFactors = [xq.Factors.debttoequity, xq.Factors.cashratio, xq.Factors.current]
    ##市值取对数
    #所有因子
    factorsList = valuationFactors+finanQlyFactors+levelFactors
    
    """
    参数1：查询的股票列表
    参数2：查询的因子列表
    参数3：查询的日期列表
    """
    data = xq.hfactor(stockList, factorsList, tradingDate)
    
    dat_dic = {}#{key：code，value：df,行为日期，列为factor}
    for code in stockList:
        dat_dic[code] = pd.DataFrame(index = tradingDate)
    
    for fidx,factor in enumerate(factorsList):
        factor = data[0][fidx][0]#factorList和codeList和传入的顺序不同，重新获取Factor名称
        code_list = data[2]#重新获得code列表
        data_list = data[0][fidx][1]
        for cidx,code in enumerate(code_list):
            tmp = []
            for dat in data_list[cidx]:
                if dat==None:
                    tmp.append(np.nan)
                else:
                    tmp.append(dat)
            
            dat_dic[code].loc[:,factor] = tmp#因子值获取为空bug
    
    dat_dic1 = factor_major_transfer(dat_dic)#{key：factor，value：df,行为日期，列为code}
    return dat_dic1

"""
获得指定时间段内，股票列票中的收盘价。
return： stockClose，
"""
def getCloseData(stockList, startTime = 20110131, endTime = 20170731):
    tradingDate = xq.tradingDay(startTime, endTime, frequencyType=xq.FrequencyType.MONTH, dayType=xq.DayType.LASTDAY)
    data = xq.hfactor(stockList, [xq.Factors.close], tradingDate)
    
    stockClose = pd.DataFrame(index = tradingDate)
    code_list = data[2]
    data_list = data[0][0][1]
    for cidx,code in enumerate(code_list):
        stockClose.loc[:, code] = data_list[cidx]
        
    return stockClose