# -*- coding: utf-8 -*-
"""
Created on Sat Jul 28 14:59:47 2018
@author: Administrator
"""
import pandas as pd
import numpy as np
import random
from xquant1.refactor.dataset import get_stockList, get_factors, getCloseData
from xquant1.refactor.data2label import get_ratio
from xquant1.refactor.data_util import factors_clean,stock_major_transfer,time_major_transfer,data_split
from model.Variational_AutoEncoder import VAE_train
from xquant1.refactor.factor_check_util import factor_layer_test, plot_layer

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
        valid_codes.append(list(tmp_sr[tmp_sr==1].index)+list(tmp_sr[tmp_sr==0].index))
        
    startTime = Y_data.index[0]
    endTime = Y_data.index[-1]
    return valid_codes, startTime, endTime

"""
根据valid_codes提取有效（显著涨跌的）样本
参数：
    dat_dic_time_major:因子数据，{key: time, value:df，行为code，列为factor，值为因子暴露值}
    Y_data_lab: df， 行为日期，列为股票代码，值为1，0，-1.表示该股票收益为市场前30%，后30%，和其他
    valid_codes: list，对应每个投资期，有一组显著涨跌的股票集合（标签为1，0的股票代码集合）
返回：
   X_data:样本的X因子值,list,每行对应该期、有效股票集合的因子值
   Y_data:样本的Y值，list，每期对应该期、有效股票集合的标签值
"""   
def data_filter(dat_dic_time_major, Y_data_lab, valid_codes):
    X_data = []
    Y_data = []
    for tidx,time in enumerate(dat_dic_time_major.keys()):
        filter_list = valid_codes[tidx]
        X_data.append(dat_dic_time_major[time].loc[filter_list, :].values)
        Y_data.append(Y_data_lab.loc[time, filter_list].values)
    return X_data, Y_data
    

#%% 主程序
startTime=20110131
endTime=20180731
#(1)股票列表获取
stockList = get_stockList(20170428)[0]
random.shuffle(stockList)
stockList = stockList[:100]

#（2）1.因子值获取，以月为截面期;2.数据清洗
print("start fetch factor data...")
dat_dic_factor_marjor = get_factors(stockList, startTime, endTime)#{key：factor，value：df,行为日期，列为code}
dat_dic_factor_marjor = factors_clean(dat_dic_factor_marjor)

dat_dic_stock_major = stock_major_transfer(dat_dic_factor_marjor)#{key：factor，value：df,行为日期，列为code}
stockListValid = list(dat_dic_stock_major.keys())#2.获得clean的stockList

#（3)1.收盘价获取，标签获取，2.收益率及标签
#1.收盘价及指数，计算收益率
print("start fetch close data...")
stockClose = getCloseData(stockListValid, startTime, endTime)
indexClose = getCloseData(["000300.SH"], startTime, endTime)
stock_ratio, index_ratio = get_ratio(stockClose, indexClose)

# (4)收盘价标签转换，并挑选显著性样本
Y_data_lab = y_transfer(stock_ratio)
valid_codes, startTime, endTime = get_valid_codeList(Y_data_lab)
dat_dic_time_major = time_major_transfer(dat_dic_stock_major)
X_data, Y_data = data_filter(dat_dic_time_major, Y_data_lab, valid_codes)


#(5)划分测试集
time_test = 12#最近几个月作为测试
X_train, X_test = np.concatenate(X_data[:-time_test]), np.concatenate(X_data[-time_test:])
y_train, y_test = np.concatenate(Y_data[:-time_test]), np.concatenate(Y_data[-time_test:])#最后一年的数据做预测
X_train, X_vali, y_train, y_vali = data_split(X_train, y_train, test_size = 0.1)

#(6)搭建模型
vae_model, encoder_model = VAE_train(X_train, X_vali, [16,8,2], [8,16], epoches = 2000)

#(7)测试模型     
X_predict = vae_model.predict(X_test)
X_refactor = encoder_model.predict(X_test)
from sklearn.metrics import mean_squared_error
print("test mse error:",end="")
print(mean_squared_error(X_predict, X_test))

#%% (8)衍生因子生成 
def get_refacor(model, dat_dic_time_major, timeList, stockListValid, refactorDim):
    refactor_data = np.zeros((len(timeList),len(stockListValid), refactorDim))#存放衍生因子，三维（时间，代码，衍生因子维度）
    
    for tidx,time in enumerate(timeList):
        mt = dat_dic_time_major[time].as_matrix()
        refactor_data[tidx, :, :] = model.predict(mt)#用AE模型预测因子值
    return refactor_data

stockListValid = list(dat_dic_time_major[startTime].index)
timeList = list(dat_dic_time_major.keys())[-12:]
refactorDim = X_refactor.shape[1]
refactor_data = get_refacor(encoder_model, dat_dic_time_major, timeList, stockListValid, refactorDim)

#%% （9）分层测试
refactor_loc = 1
test_factor_data = pd.DataFrame(refactor_data[:,:,refactor_loc], index = timeList, columns = stockListValid)
group_netvalue = factor_layer_test(test_factor_data, stockClose.loc[timeList,:], index_ratio.loc[timeList,:], n_layer=7)
group_return = plot_layer(group_netvalue.iloc[:,:], "Net value of stratified factor","a.png")