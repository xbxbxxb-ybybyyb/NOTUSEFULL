# -*- coding: utf-8 -*-
"""
Created on Wed Aug 15 11:20:05 2018
@author: 013150
"""
import pandas as pd
import numpy as np


"""
获取各个股票相对与沪深300的超额收益
stockClose: 某一段时间，某些股票的收盘价。df,行为日期，列为股票代码。值为收盘价。
indexClose： 某一段时间，某个指数的收盘价。sr，行为日期，列为指数代码，值为收盘价
"""    
def get_ratio(stockClose, indexClose):
    #每一期的收益率
    stockClose_next = stockClose.shift(-1)#数据按行上移
    stock_ratio = stockClose_next.sub(stockClose).div(stockClose)
    #指数收益
    indexClose_next = indexClose.shift(-1)
    index_ratio = indexClose_next.sub(indexClose).div(indexClose)
    #超额收益
#    stock_ratio = stock_ratio.sub(index_ratio.iloc[:,0], axis=0)
    
    return stock_ratio, index_ratio


"""
对模型预测值y的形式做变换,前
参数：
    Y_data, 参与变换的y值，df:行为日期，列为股票代码
    flag：1，Y_data表示收益率，将其表示{-1，0,1}，表示股票收益为市场前30%，中40%,后30%
输出：变换后的Y_data
"""
def y_transfer(Y_data, flag = 1):
    if flag==1:
        #Y_data换为收益率，转化为涨跌幅标签
        for didx,date in enumerate(Y_data.index):
            Y_data = Y_data.sort_values(by=date, axis=1, ascending=True)
            layer1 = int(len(Y_data.columns)*0.3)
            layer2 = int(len(Y_data.columns)*0.7)
            Y_data.loc[date, 0:layer1] = 1
            Y_data.loc[date, layer1:layer2] = -1
            Y_data.loc[date, layer2:] = 0

        return Y_data

#%% 根据收益率选择候选股票集合
"""
在y_transfer筛选股票后，根据y的值选择每期参与换仓的股票，每月换仓，记录每月收益前30%和后30%的的股票代码集合
参数:
    Y_data:df，行为日期，列为股票代码，值为1，0，-1.表示该股票收益为市场前30%，后30%，和其他
    flag = 1, Y_data表示涨跌幅{-1,0,1}
返回:
    list，对应每个投资期，有一组显著涨跌的股票集合（标签为1，0的股票代码集合）
"""
def get_valid_codeList(Y_data, flag = 1):
    valid_codes = []#每月换仓，记录每月收益前30%和后30%的的股票代码集合
    for didx, date in enumerate(Y_data.index):
        tmp_sr = Y_data.iloc[didx,:]
        valid_codes.append(list(tmp_sr[tmp_sr==1])+list(tmp_sr[tmp_sr==1]))
        
    startTime = Y_data.index[0]
    endTime = Y_data.index[-1]
    return valid_codes, startTime, endTime


"""
根据valid_codes提取有效（显著涨跌的）样本，每一期，每个
X_dic:因子数据，{key: code, value:df，行为日期，列为因子，值为因子暴露值}
Y_data: 行为日期，列为股票代码，值为1，0，-1.表示该股票收益为市场前30%，后30%，和其他
valid_codes:
"""   
def data_filter(X_dic, Y_df, valid_codes, startTime, endTime):
    X_data = []
    X_code_list = []
    X_date_list = []
    Y_data = []
#    index_start_iloc = Y_df.index[startTime]
    index_start_iloc = 0
    for cidx, code_list in enumerate(valid_codes):
        index_iloc = index_start_iloc+cidx
        for code in code_list:
            df = X_dic[code]
            X_data.append(list(df.iloc[index_iloc,:]))
            X_code_list.append(code)
            X_date_list.append(index_iloc)
            Y_data.append(Y_df.iloc[index_iloc, :].loc[code])
    return np.array(X_data), np.array(Y_data)