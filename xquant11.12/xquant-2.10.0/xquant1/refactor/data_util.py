# -*- coding: utf-8 -*-
"""
Created on Wed Aug 15 10:27:01 2018

@author: 013150
"""

import numpy as np
import pandas as pd

    
#%%(3)特征预处理
"""
去极值,
falg==Median：根据中位数去极值
【中位数去极值：设第T期某因子在所有个股上的暴露度序列为Di，Dm为该序列中位数，Dm1为序列 |Di—Dm|的中位数，则将序列Di中所有大于Dm+5Dm1的数重设为Dm+5Dm1，将序列Di中所有小于Dm—5Dm1的数重设为Dm—5Dm1；】
"""
def dropExtreme(Di, flag = "Median"):
    if flag=="Median":
        Dm = np.median(Di[~np.isnan(Di)])#序列中位数
        Di1 = np.abs(Di-Dm)
        Dm1 = np.median(Di1[~np.isnan(Di1)])
        
        Di2 = []
        for di in Di:
            if di>Dm+5*Dm1:
                di = Dm+5*Dm1
            elif di<Dm-5*Dm1:
                di = Dm-5*Dm1
            Di2.append(di)
        return Di2
        
"""
缺失值处理：得到新的因子暴露度序列后，将因子暴露度缺失的地方设为中信一级行业相同个股的平均值；
"""
def filling(Di, industry_median):
    Di1 = []
    for i in Di:
        if np.isnan(i):
            i = industry_median
        Di1.append(i)
    return Di1
        
"""

"""
def standardization(data):
    mean = np.mean(data)
    std = np.std(data)
    data = (data - mean) / std
    return data

"""
对dat_dic中的因子数据做清洗，两层循环，第一层对因子，第二层对code。
清洗步骤：（1）中位数去极值；（2）用中位数替换nan值，（3）标准正态；（4）对因子nan值超过0.75，code的nan值超过0.5的数据丢弃。
dat_dic:{key：factor，value：df,行为日期，列为code}
"""    
def factors_clean(dat_dic):
    new_dat_dic = {}
    invalid_codeset = set()
    for k,v in dat_dic.items():
        print(k)
        data_mat = v.as_matrix()
        if len(data_mat[np.isnan(data_mat)])/data_mat.size>0.75:
            print("factor clean: remove factor "+k+" , more than 75% nan value.")
            continue#因子值缺失太多，整个因子数据删除
        else:
            for j in range(data_mat.shape[1]):
                tmp = data_mat[:,j]
                if len(tmp[np.isnan(tmp)])/float(len(tmp))>0.75:#某个code的Nan值超过一定比例，整个code数据丢弃
                    invalid_codeset.add(v.columns[j])
                    print("factor clean: remove code "+v.columns[j]+" , more than 75% nan value.")
                    continue
                data_mat[:,j] = dropExtreme(tmp)#中位数去极值
                md = np.median(tmp[~np.isnan(tmp)])
                data_mat[:,j] = filling(data_mat[:,j], md)#用中位数替换缺失值
                data_mat[:,j] = standardization(data_mat[:,j])#标准正态
            new_dat_dic[k] = pd.DataFrame(data_mat, index=v.index, columns=v.columns)
    
    for k,v in new_dat_dic.items():
        new_dat_dic[k] = v.drop(invalid_codeset, axis=1)
    
    return new_dat_dic

"""
如果收盘价为None，用上一交易日的股价替换。
dat_dic:{key：factor，value：df,行为日期，列为code}
"""    
def close_clean(close_data):
    data_mat = close_data.as_matrix()
    for j in range(data_mat.shape[1]):
        for i in range(data_mat.shape[0]):
            if np.isnan(data_mat[i,j]) and i > 0:
                data_mat[i,j] = data_mat[i-1,j]
    close_data = pd.DataFrame(data_mat, index=close_data.index, columns=close_data.columns)
    return close_data
            
        
#%%(4)划分测试集

"""
划分训练集和测试集
test_size：测试集的比例
category_label：Y_data标签是否是分类标签，如果是，划分训练集时按类别比例划分。
"""
def data_split(X_data, Y_data, test_size, category_label=False):
    
    from sklearn.model_selection import train_test_split
    if category_label == True:
        X_train, X_test, y_train, y_test = train_test_split(
            X_data, Y_data, test_size = test_size)
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X_data, Y_data, test_size = test_size, stratify = Y_data)
    
    return X_train, X_test, y_train, y_test

#%% 辅助函数
"""
输入：{key：因子， value：df,行为日期，列为code}
输出：{key：code，value：df,行为日期，列为因子}
"""
def stock_major_transfer(dat_dic):
    new_dat_dic = {}
    factor_list = list(dat_dic.keys())
    code_list = list(dat_dic[factor_list[0]].columns)
    
    for code in code_list:
        new_dat_dic[code] = pd.DataFrame(index = dat_dic[factor_list[0]].index)
        for factor in factor_list:
            new_dat_dic[code][factor] = dat_dic[factor][code]
    
    return new_dat_dic

"""
输入：{key：code， value：df,行为日期，列为factor}
输出：{key：factor，value：df,行为日期，列为code}
"""
def factor_major_transfer(dat_dic):
    new_dat_dic = {}
    code_list = list(dat_dic.keys())
    factor_list = list(dat_dic[code_list[0]].columns)
    
    for factor in factor_list:
        new_dat_dic[factor] = pd.DataFrame(index = dat_dic[code_list[0]].index)
        for code in code_list:    
            new_dat_dic[factor][code] = dat_dic[code][factor]
    
    return new_dat_dic

    
"""
输入：{key：code， value：df,行为日期，列为factor}
输出：{key：time，value：df,行为code，列为factor}
"""
def time_major_transfer(dat_dic):
    new_dat_dic = {}
    code_list = list(dat_dic.keys())
    time_list = list(dat_dic[code_list[0]].index)
    factor_list = list(dat_dic[code_list[0]].columns)
    
    for time in time_list:
        new_dat_dic[time] = pd.DataFrame(index = code_list, columns = factor_list)
        for code in code_list:
            for factor in factor_list:
                new_dat_dic[time].loc[code, factor] = dat_dic[code].loc[time, factor]
    
    return new_dat_dic