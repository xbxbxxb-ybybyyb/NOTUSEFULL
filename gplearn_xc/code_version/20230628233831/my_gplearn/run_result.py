import pandas as pd
import numpy as np
import os
import copy
import time as mytime
from scipy import stats
import copy
import re
import shutil
import random
from tqdm import tqdm


import my_fun as mf
BASE_DIR = r'D:/Work/遗传算法测试'


def _create_signal_by_percentile(x,up = 80,down = 20,period = 60):#根据分位数生成买卖信号
    """ 
    根据分位数生成买卖信号
    x: np.array,shapes:[n] 
    up:分位数阈值上限,0-100
    down:分位数阈值下限,0-100
    period:分位数计算周期，不包括当前值
    """
    signal = np.ones_like(x) * 0
    for i in range(period,len(x)):
        p = stats.percentileofscore(x[i - period : i],x[i])
        if p > up:
            signal[i] = 1
        elif p < down:
            signal[i] = -1
        else:
            signal[i] = 0
            
    return signal

def base_score(signal,close,fee = 0.003,trade_delay = 1):
    
    """ 
    策略回测打分
    signal: 每日信号,np.array,shapes:[n] 
    close:每日收盘价,np.array,shapes:[n] 
    fee:手续费，双边
    trade_delay:交易延迟天数，默认为1，当天计算信号，第二天以收盘价成交
    """
    
    n = len(signal)
    pos_array = np.ones_like(signal) * 0
    r_array = np.ones_like(signal)
    trade_array = np.ones_like(signal) * 0  
    
    last_high = -np.inf
    max_lose = 0
    lose_index = [0,0]
    
    trade_record = [[],[]]
    hold_record = [[],[]]
    for i in range(trade_delay,n):
        pos_array[i] = signal[i - trade_delay]
        trade = abs(pos_array[i] - pos_array[i - 1])
        r_array[i] = (close[i] / close[i - 1] - 1) * pos_array[i - 1]
        r_array[i] = (1 + r_array[i] - (trade * fee * 0.5)) * r_array[i - 1]
        
        trade_array[i] = trade
        if i < n - trade_delay:
            
            if pos_array[i] != 0 and pos_array[i - 1] == 0:#新开仓
                last_open_index = i
                last_direction = pos_array[i]
            elif pos_array[i] != pos_array[i - 1]:#平仓或反手
                if last_direction == 1:
                    trade_record[0].append(close[i] / close[last_open_index] - 1 - fee)
                    hold_record[0].append(i - last_open_index)
                else:
                    trade_record[1].append(-(close[i] / close[last_open_index] - 1) - fee)
                    hold_record[1].append(i - last_open_index)
                if pos_array[i] != 0:
                    last_open_index = i
                    last_direction = pos_array[i]
                
                    
            
        if r_array[i] > last_high:
            last_high = r_array[i]
            lose_index[0] = i
        temp_r = r_array[i] / last_high - 1
        if temp_r < max_lose:
            max_lose = temp_r
            lose_index[1] = i
    
    
    r_annual = (r_array[-1] / r_array[0]) ** (252 / n) - 1
    if abs(max_lose) < 0.001:
        r_l = 100
    else:
        r_l = -r_annual / max_lose
    score_list = [r_l]
    # score_list = [r_annual,max_lose,r_l]
    
    trade_n = np.sum(trade_array) / (n / 252)
    score_list.append(trade_n)
    win_n = len(trade_record[0])
    lose_n = len(trade_record[1])
    if win_n + lose_n == 0:
        win_ratio = 0
    else:
        win_ratio = win_n / (win_n + lose_n)
    
    score_list.append(win_ratio)
    
    if len(hold_record[0]) == 0:
        hold_avg = 0
    else:
        hold_avg = np.mean(hold_record[0])
    score_list.append(hold_avg)
    
    final_score = score_list[0] * (score_list[1] ** 0.5) * score_list[2] * (score_list[3] ** 0.5)
    final_score = max(0,final_score)
    
    # score_list.append(r_array[0])
    # score_list.append(r_array[-1])
    # return r_annual,max_lose
    return final_score,score_list,r_annual,max_lose,r_array,pos_array









def _get_score(y_pred,y,fee = 0.003,trade_delay = 1):
    """ 
    策略回测打分
    y_pred: X_Train经过遗传函数处理后的值,np.array,shapes:[n] 
    y:和y_pred对应的目标值,默认为每日收盘价,np.array,shapes:[n] 
    fee:手续费，双边
    trade_delay:交易延迟天数，默认为1，当天计算信号，第二天以收盘价成交
    """
    up,down,period = [80,20,60]
    signal = _create_signal_by_percentile(y_pred,up = up,down = down,period = period)
    
    
    close = y
    
    final_score,score_list,r_annual,max_lose = _base_score(signal,close,fee = fee,trade_delay = trade_delay)

    return final_score,score_list,r_annual,max_lose

def _base_score(signal,close,fee = 0.003,trade_delay = 1):
    
    """ 
    策略回测打分
    signal: 每日信号,np.array,shapes:[n] 
    close:每日收盘价,np.array,shapes:[n] 
    fee:手续费，双边
    trade_delay:交易延迟天数，默认为1，当天计算信号，第二天以收盘价成交
    """
    
    n = len(signal)
    pos_array = np.ones_like(signal) * 0
    r_array = np.ones_like(signal)
    trade_array = np.ones_like(signal) * 0  
    
    last_high = -np.inf
    max_lose = 0
    lose_index = [0,0]
    
    trade_record = [[],[]]
    hold_record = [[],[]]
    for i in range(trade_delay,n):
        pos_array[i] = signal[i - trade_delay]
        trade = abs(pos_array[i] - pos_array[i - 1])
        r_array[i] = (close[i] / close[i - 1] - 1) * pos_array[i - 1]
        r_array[i] = (1 + r_array[i] - (trade * fee * 0.5)) * r_array[i - 1]
        
        trade_array[i] = trade
        if i < n - trade_delay:
            
            if pos_array[i] != 0 and pos_array[i - 1] == 0:#新开仓
                last_open_index = i
                last_direction = pos_array[i]
            elif pos_array[i] != pos_array[i - 1]:#平仓或反手
                if last_direction == 1:
                    trade_record[0].append(close[i] / close[last_open_index] - 1 - fee)
                    hold_record[0].append(i - last_open_index)
                else:
                    trade_record[1].append(-(close[i] / close[last_open_index] - 1) - fee)
                    hold_record[1].append(i - last_open_index)
                if pos_array[i] != 0:
                    last_open_index = i
                    last_direction = pos_array[i]
                
                    
            
        if r_array[i] > last_high:
            last_high = r_array[i]
            lose_index[0] = i
        temp_r = r_array[i] / last_high - 1
        if temp_r < max_lose:
            max_lose = temp_r
            lose_index[1] = i
    
    
    r_annual = (r_array[-1] / r_array[0]) ** (252 / n) - 1
    if abs(max_lose) < 0.001:
        r_l = 100
    else:
        r_l = -r_annual / max_lose
    score_list = [r_l]
    # score_list = [r_annual,max_lose,r_l]
    
    trade_n = np.sum(trade_array) / (n / 252)
    score_list.append(trade_n)
    win_n = len(trade_record[0])
    lose_n = len(trade_record[1])
    if win_n + lose_n == 0:
        win_ratio = 0
    else:
        win_ratio = win_n / (win_n + lose_n)
    
    score_list.append(win_ratio)
    
    if len(hold_record[0]) == 0:
        hold_avg = 0
    else:
        hold_avg = np.mean(hold_record[0])
    score_list.append(hold_avg)
    
    final_score = score_list[0] * (score_list[1] ** 0.5) * score_list[2] * (score_list[3] ** 0.5)
    final_score = max(0,final_score)
    
    # score_list.append(r_array[0])
    # score_list.append(r_array[-1])
    return final_score,score_list,r_annual,max_lose


# def get_score2(signal,close,interval = 252,fee = 0.003,trade_delay = 1):#根据每年涨跌调整分数权重
def _get_score2(y_pred,y,fee = 0.003,trade_delay = 1):
    """ 
    策略回测打分
    y_pred: X_Train经过遗传函数处理后的值,np.array,shapes:[n] 
    y:和y_pred对应的目标值,默认为每日收盘价,np.array,shapes:[n] 
    fee:手续费，双边
    trade_delay:交易延迟天数，默认为1，当天计算信号，第二天以收盘价成交
    interval:划区间打分，每个区间的天数
    """
    
    interval = 252
    up,down,period = [80,20,60]
    signal = _create_signal_by_percentile(y_pred,up = up,down = down,period = period)
    
    
    close = y
    
    
    
    
    final_score_all,score_list_all,r_annual_all,max_lose_all = _base_score(signal,close,fee = fee,trade_delay = trade_delay)
    
    # return score_list_all
    signal_all = signal
    close_all = close
    n_data = len(close)
    end_flag = 0
    result = [[0,n_data,close[-1] / close[0] - 1] + score_list_all]
    
    n_part = round(n_data / interval)
    interval = n_data // n_part
    for i in range(n_part):
        t_start = i * interval
        t_end = min((i + 1) * interval + 2,n_data)
        signal = signal_all[t_start:t_end].copy()
        close = close_all[t_start:t_end].copy()            
        final_score,score_list,r_annual,max_lose = _base_score(signal,close,fee = fee,trade_delay = trade_delay)      
  
        result.append([t_start,t_end,close[-1] / close[0] - 1,r_annual] + score_list)
        if end_flag == 1:
            break
    index_r_list = []
    my_rlist = []
    for i in range(1,len(result)):
        index_r_list.append(result[i][2])
        my_rlist.append(result[i][3])
    
    my_rlist = np.array(my_rlist)
    
    index_r_array = np.array(index_r_list)
    
    score_w = set_year_weight(index_r_array)
        
    r_adjust = np.exp(np.dot(np.log(1 + my_rlist),score_w)) - 1
    
    
    if abs(max_lose_all) < 0.001:
        r_l = 100
    else:
        r_l = -r_adjust / max_lose_all
    
    score_list_all[0] = r_l
    final_score = score_list_all[0] * (score_list_all[1] ** 0.5) * score_list_all[2] * (score_list_all[3] ** 0.5)
    final_score = max(0,final_score)
    
    
    # return final_score
    return final_score,score_list_all
    
def load_data():
    fn = BASE_DIR + r'/原始数据/000300.SH.csv'
    df = pd.read_csv(fn,engine = 'python',index_col = 0,encoding = 'gbk')
    df = df[['trade_dt','s_dq_open','s_dq_high','s_dq_low','s_dq_close','s_dq_volume']]
    df = df.set_index('trade_dt')
    df = df.sort_index()
    # tlist = mf.get_list_trading_days(20140101,20191231)
    tlist = mf.get_list_trading_days(20140101,20221129)
    # tlist = mf.get_list_trading_days(20191231,20221129)
    # tlist = mf.get_list_trading_days(20101231,20140101)
    df = df.reindex(tlist)
    df.columns = ['open','high','low','close','s_dq_volume']
    print(df.isna().sum())
    X_Train = df.values
    label = df.columns.tolist()
    Y_Train = df['close'].values
    
    return X_Train,Y_Train,label,tlist


def find_best(Y,close):
    x,y = Y.shape
    sss = []
    for i in range(y):
        signal = _create_signal_by_percentile(Y[:,i])
        final_score,score_list,r_array,pos_array = _get_score(signal,close)
        sss.append(final_score)
    return sss

def get_score_list(est_gp,X_Train,Y_Train):
    tlist = mf.get_list_trading_days(20140101,20191231)
    n_insample = len(tlist)
    result = []
    for i in range(len(est_gp._programs[-1])):
        y_pred = est_gp._programs[-1][i].execute(X_Train)
        signal = _create_signal_by_percentile(y_pred)
        final_score1,score_list,r_array,pos_array = _get_score(signal[:n_insample],Y_Train[:n_insample])
        final_score2,score_list,r_array,pos_array = _get_score(signal[n_insample:],Y_Train[n_insample:])
        formular_len = est_gp._programs[-1][i].length_
        result.append([final_score1,final_score2,formular_len])
    return np.array(result)

def get_score_single(program,X_Train,Y_Train):
    tlist = mf.get_list_trading_days(20140101,20191231)
    n_insample = len(tlist) 
    y_pred = program.execute(X_Train)
    signal = _create_signal_by_percentile(y_pred)
    # final_score1,score_list,r_array,pos_array = _get_score(signal[:n_insample],Y_Train[:n_insample])
    # final_score2,score_list,r_array,pos_array = _get_score(signal[n_insample:],Y_Train[n_insample:])
    
    r_annual1,max_lose1 = base_score(signal[:n_insample],Y_Train[:n_insample])
    r_annual2,max_lose2 = base_score(signal[n_insample:],Y_Train[n_insample:])
    
    formular_len = program.length_
    # result.append([final_score1,final_score2,formular_len])
    # return final_score1,final_score2,formular_len
    return r_annual1,max_lose1,r_annual2,max_lose2,formular_len

def result_output(fname,programs,index_list,X_Train,Y_Train):
    tlist = mf.get_list_trading_days(20140102,20221129)
    n_insample = round(len(tlist) * 0.7)
    fee = 0.003
    trade_delay = 1
    
    result_list = []
    data_list = []
    for index in index_list:
        program = programs._programs[-1][index]
        factor_name = program.__str__()
        y_pred = program.execute(X_Train)
        signal = _create_signal_by_percentile(y_pred)
        close = Y_Train
        

        
        final_score,score_list1,r_annual1,max_lose1,r_array,pos_array = base_score(signal[:n_insample],Y_Train[:n_insample])
        final_score,score_list2,r_annual2,max_lose2,r_array,pos_array = base_score(signal[n_insample:],Y_Train[n_insample:])
        final_score,score_list,r_annual,max_lose,r_array,pos_array = base_score(signal,close,fee = fee,trade_delay = trade_delay)
        # return r_annual,r_annual1,r_annual2
        score1 = [r_annual1,max_lose1] + score_list1
        score2 = [r_annual2,max_lose2] + score_list2
        # return score1,score2
        r_array = r_array
        pos_array = pos_array
        result_list.append([factor_name] + score1 + score2)
        
        df = pd.DataFrame([close,pos_array,r_array]).T
        df.columns = ['close','pos','r']
        df.index = tlist
        data_list.append(df)
    
    label = ['年化收益率','最大回撤','收益回撤比','交易次数','胜率','多头平均持仓天数']
    t1 = '%s_%s' % (tlist[0],tlist[n_insample])
    t2 = '%s_%s' % (tlist[n_insample],tlist[-1])
    my_label = []
    new_label = ['因子表达式','回测区间1']
    for i in range(len(label)):
        my_label.append(label[i] + '_1')
        new_label.append(label[i] + '_1')
    new_label.append('回测区间2')
    for i in range(len(label)):
        my_label.append(label[i] + '_2')
        new_label.append(label[i] + '_2')
    my_label = ['因子表达式'] + my_label
    result_df = pd.DataFrame(result_list,columns = my_label)
    result_df['回测区间1'] = t1
    result_df['回测区间2'] = t2
    result_df = result_df[new_label]
    
    
    writer = pd.ExcelWriter(r'D:/Work/遗传算法测试/训练结果/gp_20230303155910/量价因子表现_20230303155910.xlsx')
    result_df.to_excel(writer,sheet_name = '因子回测')
    for i in range(len(data_list)):
        df = data_list[i]
        df.to_excel(writer,sheet_name = '因子%s净值曲线' % i)
  
        # score_list[i].to_excel(writer, sheet_name='组合%s回测结果' % i)
        # daily_df_list[i].to_excel(writer, sheet_name='组合%s每日净值' % i)
    
    writer.save()
    
    # return result_df,data_list
    


def set_year_weight(r_year_list,up = 0.1,down = -0.09):#根据涨跌幅分配每年的分数权重
    flag = np.ones_like(np.array(r_year_list))
    for i in range(len(flag)):
        r = r_year_list[i]
        if r >= up:
            flag[i] = 1
        elif r <= down:
            flag[i] = -1          
        else:
            flag[i] = 0
            
    index1 = np.where(flag == 1)
    index2 = np.where(flag == -1)
    index3 = np.where(flag == 0)
            
    n1 = len(index1[0])
    n2 = len(index2[0])
    n3 = len(index3[0])
    
    if n1 == 0 or n2 == 0:
        
        flag = np.ones_like(flag) / len(flag)
        
    else:
        flag[index1] = 1 / n1
        flag[index2] = 1 / n2
        if n3 != 0:
            flag[index3] = min(1 / n3,0.5 / n1 + 0.5 / n2)
    flag = flag / np.sum(flag)
    return flag
        
def trend_test(p,period = 21):
    r = p[1:] / p[:-1] - 1
    trade_r = np.ones_like(r) * 0
    for i in range(period,len(r)):
        # if np.sum(r[i - period :i]) > 0:
        if p[i - 1] / p[i - period] > 1:
            trade_r[i] = r[i]
        elif p[i - 1] / p[i - period] < 1:
            trade_r[i] = -r[i]
        else:
            trade_r[i] = 0
            
    return trade_r
        
# from joblib import Parallel, delayed

# X_Train,Y_Train,label,tlist = load_data()
# # xxx = Parallel(n_jobs=3,verbose = 1)(delayed(get_score_single)(ccc[1]._programs[-1][20],X_Train,Y_Train)

# def start_job(X_Train,Y_Train,est_gp,n_jobs = 1):
#     n = len(est_gp._programs[-1])
#     # n = 2
#     result = Parallel(n_jobs=n_jobs,verbose = 0)(delayed(get_score_single)(est_gp._programs[-1][i],X_Train,Y_Train) for i in tqdm(range(n),position = 0))
#     return result

        