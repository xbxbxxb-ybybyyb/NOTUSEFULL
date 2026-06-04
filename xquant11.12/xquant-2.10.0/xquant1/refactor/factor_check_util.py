# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 14:17:57 2018
@author: Administrator
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')

#%%（7）分层因子测试
"""
对某个单因子进行分层测试
factor_data: 各个股票在各个交易段，在因子上的暴露值。df，行为日期，列为股票代码
close_data: 各个股票在各个交易段，的收盘价。df,行为日期，列为股票代码
n: 分层测试的层数
返回：分层的每层涨跌幅总和，每层的集合中的股票数目
"""
def factor_layer_period_ratio(factor_data, close_data, n = 5):
    date_list=list(factor_data.index)
    group_col = ["layer"+str(nn) for nn in range(1,n+1)]
    
    group_return_sum=pd.DataFrame(index=date_list[:-1], columns=group_col)#返回分层的收益率总和,最后一期没有收益率
    group_return_weight = pd.DataFrame(index=date_list[:-1],columns=group_col)#返回为每个分层收益率贡献的股票个数
    
    #对日期循环
    for t in range(0, np.size(date_list)-1):
        #（1）对当期的股票集合按因子暴露值高低排序
        tmp_factordata = factor_data.iloc[t,:]
        factor_daydata = tmp_factordata.sort_values(ascending=False)
        valid_code = factor_daydata.index#有效的股票序列
        tmp_size=len(valid_code)

        #（2）将各个股票的收益率存到dataframe中的一列       
        tmp_closedata = close_data.iloc[t:t+2,:]#当期和下一期收盘价，用于计算收益率
        return_daydata = (tmp_closedata.iloc[1,:]-tmp_closedata.iloc[0,:])/tmp_closedata.iloc[0,:]#当期涨跌幅
        
        #（3）计算每层的股票总收益率和总股票数
        group_size=int(tmp_size/n)#每一层的个数
        for i in range(0,n-1):
            tmp_stocklist=valid_code[group_size*i:group_size*(i+1)]#取出第N层对应的股票代码
            group_return_sum.loc[date_list[t], group_col[i]] = np.sum(return_daydata.loc[tmp_stocklist])#求每一层的总收益率
            group_return_weight.loc[date_list[t], group_col[i]] = group_size
        #最后一层的收益单独计算
        left_stocklist=valid_code[group_size*(n-1):]
        group_return_weight.loc[date_list[t],group_col[n-1]] = len(list(left_stocklist))        
        group_return_sum.ix[date_list[t+1],group_col[n-1]] = np.sum(return_daydata.loc[left_stocklist])#剩下的股票归入最后一层

    return group_return_sum, group_return_weight

"""
考虑行业中性的分层，即对每个行业划分成若干等分，再累加所有行业第一个分层的累计收益率
partition_dictionnary：股票的细分类别/行业
"""
def factor_neutral_test(factor_data, close_data, parts_dic, n = 5):
    date_list=list(factor_data.index)
    group_col=list(range(1,n+1))
    group_return_sum=pd.DataFrame(np.zeros((len(date_list),len(group_col))),index=date_list[:],columns=group_col)
    group_return_weight = pd.DataFrame(np.zeros((len(date_list),len(group_col))),index=date_list[:],columns=group_col)
    all_code_list = list(close_data.columns)
    
    for partition in parts_dic.keys():
        part_code_list = parts_dic[partition]#某细分类别的股票代码
        part_code_list = np.intersect1d(all_code_list, part_code_list)#过滤不在close_data中包含的股票代码
        part_factor_data = factor_data.ix[:,part_code_list]
        part_close_data = close_data.ix[:,part_code_list]
        group_sum, group_weight = factor_layer_period_ratio(part_factor_data,part_close_data)
        group_return_sum = group_return_sum.add(group_sum)
        group_return_weight = group_return_weight.add(group_weight)
    return group_return_sum,group_return_weight


"""
累计收益率
"""
def factor_group_netvalue(group_return):
    tmp_group_return=group_return+1
    group_netvalue=tmp_group_return.cumprod()#累乘，类似复利计算
#    group_netvalue=tmp_group_return.cumsum()
    return group_netvalue
    

"""
因子分层测试，绘制每个层的股票收益率。
factor_data: 各个股票在各个交易段，在因子上的暴露值。df，行为日期，列为股票代码
stockClose: 各个股票在各个交易段，的收盘价。df,行为日期，列为股票代码
bench_rario：大盘指数每期的收益率。df,行为日期，列为指数代码。
"""   
def factor_layer_test(factor_data, stockClose, index_rario, n_layer=5):

    #每组的区间每期收益率及每期累计收益率
    group_return_sum, group_return_weight = factor_layer_period_ratio(factor_data, stockClose, n_layer)
    group_return = group_return_sum/group_return_weight#涨跌幅总和 / 集合中的股票数
    
    group_return = pd.concat([group_return, index_rario],axis=1)#大盘指数收益 
    group_netvalue = factor_group_netvalue(group_return)
    
    print('$statistic-log,module=refactor,platform=XQUANT-Cloud')
    return group_netvalue

"""
绘制分层测试的收益率
输入：
    group_return：array，行为时间，列为因子各层和benchmark
    title: 图的表头
    filename： 保存的图片名
返回：
    分层收益曲线，横坐标为时间，纵坐标收益。因子的每一层一条曲线。
"""
def plot_layer(group_return, title, filename):
    from matplotlib import pyplot as plt
    import xquant1.pydraw as dr
    import matplotlib.dates as mdate
    
    plt.rcParams['savefig.dpi'] = 100#savefig显示的图片分辨率
    plt.rcParams['figure.dpi'] = 50 #show显示的图片分辨率
    plt.rcParams['figure.figsize'] = (15.0, 8.0) # 设置figure_size尺寸

    ax = plt.subplot(1,1,1)

    plt.xlabel(u"date")
    plt.ylabel(u"ratio")
    plt.title(title)
    dateList = [str(t) for t in group_return.index]
    
    for colname in group_return:
        x = list(range(len(group_return.index)))
        y = list(group_return[colname])
        plt.plot(x,y,label = colname)
        
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width , box.height])
        ax.legend(loc='center left', bbox_to_anchor=(0.05, 0.9), ncol=3)
        ax.xaxis.set_major_formatter(mdate.DateFormatter('%Y-%m-%d'))
        plt.xticks(range(79), dateList, rotation = 90)#横坐标显示为时间
        
    plt.savefig(filename)
    dr.showfig(filename)
    print('$statistic-log,module=refactor,platform=XQUANT-Cloud')
    

   
#%%  

"""
多空收益率
"""
def long_short_return(group_return, N=5):
    tmp_group_return=group_return+1
    cum_return=tmp_group_return.cumprod()
    long_short_return=pd.DataFrame()
    #判断第一层收益率是否大于最后一层
    if cum_return.iloc[-1,0]>cum_return.iloc[-1,N-1]:
        period_return=group_return[1]-group_return[N]
        tmp_period_return=period_return+1
        cum_return=tmp_period_return.cumprod()-1
    else:
        period_return=group_return[N]-group_return[1]
        tmp_period_return=period_return+1
        cum_return=tmp_period_return.cumprod()-1
    long_short_return['PERIOD_RETURN']=period_return
    long_short_return['CUM_RETURN']=cum_return                 
    return long_short_return
          

def factor_IC(factor_data,close_data):
    
    date_list = list(factor_data.index)
    code_list = list(factor_data.columns)
    # 计算每期收益率
    rtn = close_data/close_data.shift(1) - 1
    # 按照因子数据的日期和股票池，提取收益数据 
    rtn = rtn.ix[date_list,code_list]        

    # 计算 IC = corr(当期因子值，下期收益率)
    ic_list = factor_data.corrwith(rtn.shift(-1),drop=True,axis=1)
    ic_mean = ic_list.mean()
    ic_std = ic_list.std()
    ir = ic_mean / ic_std
    ic_abs005 = len(ic_list[ic_list.abs() > 0.05]) / float(len(ic_list))
    ic_abs01 = len(ic_list[ic_list.abs() > 0.1]) / float(len(ic_list))
    
    result = {'FACTOR_IC':ic_mean, 'FACTOR_IC_STD':ic_std, 'FACTOR_IR':ir, 'FACTOR_IC_COMP1': ic_abs005, 'FACTOR_IC_COMP2':ic_abs01}
    IC_result=pd.Series(result)
    return IC_result