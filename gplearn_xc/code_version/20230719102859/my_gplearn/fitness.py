"""Metrics to evaluate the fitness of a program.

The :mod:`gplearn.fitness` module contains some metric with which to evaluate
the computer programs created by the :mod:`gplearn.genetic` module.
"""

# Author: Trevor Stephens <trevorstephens.com>
#
# License: BSD 3 clause

import numbers

import numpy as np
import pandas as pd
from joblib import wrap_non_picklable_objects
from scipy.stats import rankdata
from scipy import stats
__all__ = ['make_fitness']


class _Fitness(object):

    """A metric to measure the fitness of a program.

    This object is able to be called with NumPy vectorized arguments and return
    a resulting floating point score quantifying the quality of the program's
    representation of the true relationship.

    Parameters
    ----------
    function : callable
        A function with signature function(y, y_pred, sample_weight) that
        returns a floating point number. Where `y` is the input target y
        vector, `y_pred` is the predicted values from the genetic program, and
        sample_weight is the sample_weight vector.

    greater_is_better : bool
        Whether a higher value from `function` indicates a better fit. In
        general this would be False for metrics indicating the magnitude of
        the error, and True for metrics indicating the quality of fit.

    """

    def __init__(self, function, greater_is_better):
        self.function = function
        self.greater_is_better = greater_is_better
        self.sign = 1 if greater_is_better else -1

    def __call__(self, *args):
        return self.function(*args)


def make_fitness(*, function, greater_is_better, wrap=True):
    """Make a fitness measure, a metric scoring the quality of a program's fit.

    This factory function creates a fitness measure object which measures the
    quality of a program's fit and thus its likelihood to undergo genetic
    operations into the next generation. The resulting object is able to be
    called with NumPy vectorized arguments and return a resulting floating
    point score quantifying the quality of the program's representation of the
    true relationship.

    Parameters
    ----------
    function : callable
        A function with signature function(y, y_pred, sample_weight) that
        returns a floating point number. Where `y` is the input target y
        vector, `y_pred` is the predicted values from the genetic program, and
        sample_weight is the sample_weight vector.

    greater_is_better : bool
        Whether a higher value from `function` indicates a better fit. In
        general this would be False for metrics indicating the magnitude of
        the error, and True for metrics indicating the quality of fit.

    wrap : bool, optional (default=True)
        When running in parallel, pickling of custom metrics is not supported
        by Python's default pickler. This option will wrap the function using
        cloudpickle allowing you to pickle your solution, but the evolution may
        run slightly more slowly. If you are running single-threaded in an
        interactive Python session or have no need to save the model, set to
        `False` for faster runs.

    """
    if not isinstance(greater_is_better, bool):
        raise ValueError('greater_is_better must be bool, got %s'
                         % type(greater_is_better))
    if not isinstance(wrap, bool):
        raise ValueError('wrap must be an bool, got %s' % type(wrap))
    if function.__code__.co_argcount != 3:
        raise ValueError('function requires 3 arguments (y, y_pred, w),'
                         ' got %d.' % function.__code__.co_argcount)
    if not isinstance(function(np.array([1, 1]),
                      np.array([2, 2]),
                      np.array([1, 1])), numbers.Number):
        raise ValueError('function must return a numeric.')

    if wrap:
        return _Fitness(function=wrap_non_picklable_objects(function),
                        greater_is_better=greater_is_better)
    return _Fitness(function=function,
                    greater_is_better=greater_is_better)


def my_make_fitness(*, function, greater_is_better, wrap=True):

    if not isinstance(greater_is_better, bool):
        raise ValueError('greater_is_better must be bool, got %s'
                         % type(greater_is_better))
    if not isinstance(wrap, bool):
        raise ValueError('wrap must be an bool, got %s' % type(wrap))
    if function.__code__.co_argcount != 3:
        raise ValueError('function requires 3 arguments (y, y_pred, w),'
                         ' got %d.' % function.__code__.co_argcount)
    if not isinstance(function(np.array([1, 1]),
                      np.array([2, 2]),
                      np.array([1, 1])), numbers.Number):
        raise ValueError('function must return a numeric.')

    if wrap:
        return _Fitness(function=wrap_non_picklable_objects(function),
                        greater_is_better=greater_is_better)
    return _Fitness(function=function,
                    greater_is_better=greater_is_better)


def _weighted_pearson(y, y_pred, w):
    """Calculate the weighted Pearson correlation coefficient."""
    with np.errstate(divide='ignore', invalid='ignore'):
        y_pred_demean = y_pred - np.average(y_pred, weights=w)
        y_demean = y - np.average(y, weights=w)
        corr = ((np.sum(w * y_pred_demean * y_demean) / np.sum(w)) /
                np.sqrt((np.sum(w * y_pred_demean ** 2) *
                         np.sum(w * y_demean ** 2)) /
                        (np.sum(w) ** 2)))
    if np.isfinite(corr):
        return np.abs(corr)
    return 0.


def _weighted_spearman(y, y_pred, w):
    """Calculate the weighted Spearman correlation coefficient."""
    y_pred_ranked = np.apply_along_axis(rankdata, 0, y_pred)
    y_ranked = np.apply_along_axis(rankdata, 0, y)
    return _weighted_pearson(y_pred_ranked, y_ranked, w)


def _mean_absolute_error(y, y_pred, w):
    """Calculate the mean absolute error."""
    return np.average(np.abs(y_pred - y), weights=w)


def _mean_square_error(y, y_pred, w):
    """Calculate the mean square error."""
    return np.average(((y_pred - y) ** 2), weights=w)


def _root_mean_square_error(y, y_pred, w):
    """Calculate the root mean square error."""
    return np.sqrt(np.average(((y_pred - y) ** 2), weights=w))


def _log_loss(y, y_pred, w):
    """Calculate the log loss."""
    eps = 1e-15
    inv_y_pred = np.clip(1 - y_pred, eps, 1 - eps)
    y_pred = np.clip(y_pred, eps, 1 - eps)
    score = y * np.log(y_pred) + (1 - y) * np.log(inv_y_pred)
    return np.average(-score, weights=w)




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

def _get_first_rank(rk_array,low = 0.5):
    x,y = rk_array.shape
    low_rank = y * low
    for i in range(x):
        for j in range(y):
            if rk_array[i,j] > low_rank:
                rk_array[i,j] = rk_array[i,j] + rk_array[i,j] - low_rank
    return np.mean(rk_array,axis = 0)

def _create_signal_by_percentile_all(x, Y_Train, up_list=[90, 80, 70, 60], period_list=[21 * 3, 21 * 6, 21 * 12],
                                     score_period=21 * 3, sample_period=4, win_rate=0.74):  # 根据分位数生成买卖信号
    """
    根据分位数生成买卖信号
    x: np.array,shapes:[n]
    up:分位数阈值上限,0-100
    down:分位数阈值下限,0-100
    period:分位数计算周期，不包括当前值
    """
    n = len(x)
    signal_matrix = np.ones((n, len(up_list) * len(period_list))) * 0
    r_matrix = np.ones_like(signal_matrix) * 0.0
    t_start = np.max(period_list)
    for j in range(len(up_list)):
        for k in range(len(period_list)):
            up = up_list[j]
            period = period_list[k]
            down = 100 - up

            signal = np.ones_like(x) * 0
            for i in range(t_start, len(x)):
                p = stats.percentileofscore(x[i - period: i], x[i])
                if p > up:
                    signal[i] = 1
                elif p < down:
                    signal[i] = -1
                else:
                    signal[i] = 0

            signal_matrix[:, j + k * len(up_list)] = signal
            # print(j + k * len(up_list))

            final_score, score_list0, r_annual0, max_lose0, r_array, pos_array = base_score(signal, Y_Train)
            r_matrix[:, j + k * len(up_list)] = r_array

    rd = np.ones_like(r_matrix) * 0.0
    rd[1:, :] = r_matrix[1:, :] / r_matrix[:-1, :] - 1
    r = np.ones_like(r_matrix) * 0.0
    std = np.ones_like(r_matrix) * 0.0
    a, b = rd.shape
    for i in range(b):
        std[:, i] = pd.Series(rd[:, i]).rolling(score_period).std().values * 252 ** 0.5
    r[score_period:, :] = (r_matrix[score_period:, :] / r_matrix[:-score_period:, :]) ** (252 / score_period) - 1

    index1 = np.where(r > 0.05)
    score = r - 0.05
    score[index1] = (r[index1] - 0.05) / std[index1]

    rank = pd.DataFrame(score).rank(axis=1, method='min', ascending=False).values

    best_signal = signal = np.ones_like(x) * 0
    best_group_array = np.ones_like(x) * -1

    last_group = -1
    for i in range(t_start + score_period * sample_period, len(best_signal)):
        if i % 21 == 0:
            index = np.arange(0, score_period * sample_period, score_period)
            index = index[::-1]
            rk = rank[i - index, :]
            first_rank = _get_first_rank(rk)
            if last_group == -1:
                best_group = np.argmin(first_rank)
                best_signal[i] = signal_matrix[i, best_group]
                last_group = best_group
            else:
                win_array = np.ones_like(rk) * 0
                a, b = win_array.shape
                for j in range(a):
                    win_array[j, :] = rk[j, :] < rk[j, last_group]
                win_group = np.sum(win_array, axis=0)
                win_index = np.where(win_group >= a * win_rate)[0]
                # score_group = np.where(first_rank < first_rank[last_group])

                if len(win_index) == 0:
                    best_signal[i] = signal_matrix[i, last_group]
                else:
                    win_group = np.argmin(first_rank[win_index])
                    if first_rank[win_group] < first_rank[last_group]:
                        best_group = win_index[win_group]
                        best_signal[i] = signal_matrix[i, best_group]
                        last_group = best_group
                    else:
                        best_signal[i] = signal_matrix[i, last_group]

        else:
            best_signal[i] = signal_matrix[i, last_group]
        best_group_array[i] = last_group

    return best_signal




def _my_score(y, y_pred,w):
    
    
    """ 
    根据分位数生成买卖信号
    x: np.array,shapes:[n] 
    up:分位数阈值上限,0-100
    down:分位数阈值下限,0-100
    period:分位数计算周期，不包括当前值
    不满足最低要求会附加惩罚系数
    """    
    # # y_pred = y_pred.reshape(-1,)
    # y_pred = y_pred[w]
    # y = y[w]
    # up,down,period = 80,20,60
    # signal = np.ones_like(y_pred) * 0
    # for i in range(period,len(y_pred)):
    #     p = stats.percentileofscore(y_pred[i - period : i],y_pred[i])
    #     if p > up:
    #         signal[i] = 1
    #     elif p < down:
    #         signal[i] = -1
    #     else:
    #         signal[i] = 0

    y_pred = y_pred.reshape(-1, )
    y_pred = y_pred[w]
    y = y[w]

    signal = _create_signal_by_percentile(y_pred)
    close = y
    fee,trade_delay = 0.003,1
    
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
        # if i < n - trade_delay:
        if 1:
            
            if pos_array[i] != 0 and pos_array[i - 1] == 0:#新开仓
                last_open_index = i
                last_direction = pos_array[i]
            elif (pos_array[i] != pos_array[i - 1]) or (i == n - 1 and pos_array[i] != 0):#平仓或反手
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
    
    if abs(max_lose) < 0.001:
        r_l = 100
    else:
        r_l = -((r_array[-1] / r_array[0]) ** (252 / n) - 1) / max_lose
    score_list = [r_l]
    
    trade_n = np.sum(trade_array) / (n / 252)
    score_list.append(trade_n)
    # win_n = len(trade_record[0])
    # lose_n = len(trade_record[1])

    trade_record_all = np.array(trade_record[0] + trade_record[1])
    win_record = np.where(trade_record_all > 0)[0]
    win_n = len(win_record)
    lose_n = len(trade_record_all) - win_n

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
    # final_score = max(0,final_score)    
    final_score = final_score
    penalty = min(0,(score_list[0] - 0.3)) + min(0,(score_list[1] - 2)) + min(0,(score_list[2] - 0.5)) + min(0,(score_list[3] - 6))
    final_score = 10 * penalty + final_score
    return final_score   


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
        # print(i, close[i], close[i - 1],r_array[i],trade,r_array[i - 1],fee)
        r_array[i] = (1 + r_array[i] - (trade * fee * 0.5)) * r_array[i - 1]
        
        trade_array[i] = trade
        # if i < n - trade_delay:
        if 1:
            if pos_array[i] != 0 and pos_array[i - 1] == 0:#新开仓
                last_open_index = i
                last_direction = pos_array[i]
            # elif pos_array[i] != pos_array[i - 1]:#平仓或反手
            elif (pos_array[i] != pos_array[i - 1]) or (i == n - 1 and pos_array[i] != 0):  # 平仓或反手
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
    
    trade_n = np.sum(trade_array) / (n / 252)
    score_list.append(trade_n)
    # win_n = len(trade_record[0])
    # lose_n = len(trade_record[1])


    trade_record_all = np.array(trade_record[0] + trade_record[1])
    win_record = np.where(trade_record_all > 0)[0]
    win_n = len(win_record)
    lose_n = len(trade_record_all) - win_n

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
    # final_score = max(0,final_score)
    
    # score_list.append(r_array[0])
    # score_list.append(r_array[-1])
    return final_score,score_list,r_annual,max_lose


def _base_score2(signal, close, fee=0.003, trade_delay=1):
    """
    策略回测打分,加入波动率
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
    lose_index = [0, 0]

    trade_record = [[], []]
    hold_record = [[], []]
    for i in range(trade_delay, n):
        pos_array[i] = signal[i - trade_delay]
        trade = abs(pos_array[i] - pos_array[i - 1])
        r_array[i] = (close[i] / close[i - 1] - 1) * pos_array[i - 1]
        # print(i, close[i], close[i - 1],r_array[i],trade,r_array[i - 1],fee)
        r_array[i] = (1 + r_array[i] - (trade * fee * 0.5)) * r_array[i - 1]

        trade_array[i] = trade
        # if i < n - trade_delay:
        if 1:
            if pos_array[i] != 0 and pos_array[i - 1] == 0:  # 新开仓
                last_open_index = i
                last_direction = pos_array[i]
            # elif pos_array[i] != pos_array[i - 1]:#平仓或反手
            elif (pos_array[i] != pos_array[i - 1]) or (i == n - 1 and pos_array[i] != 0):  # 平仓或反手
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
    vol = np.std(r_array[1:] / r_array[:-1] - 1, ddof=1) * 252 ** 0.5
    if abs(max_lose) < 0.001:
        r_l = 100
    else:
        r_l = -r_annual / max_lose
    score_list = [r_l]

    trade_n = np.sum(trade_array) / (n / 252)
    score_list.append(trade_n)
    # win_n = len(trade_record[0])
    # lose_n = len(trade_record[1])

    trade_record_all = np.array(trade_record[0] + trade_record[1])
    win_record = np.where(trade_record_all > 0)[0]
    win_n = len(win_record)
    lose_n = len(trade_record_all) - win_n

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
    # final_score = max(0,final_score)

    # score_list.append(r_array[0])
    # score_list.append(r_array[-1])
    return final_score, score_list, r_annual, max_lose, vol



def base_score(signal, close, fee=0.003, trade_delay=1):
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
    lose_index = [0, 0]

    trade_record = [[], []]
    hold_record = [[], []]
    for i in range(trade_delay, n):
        pos_array[i] = signal[i - trade_delay]
        trade = abs(pos_array[i] - pos_array[i - 1])
        r_array[i] = (close[i] / close[i - 1] - 1) * pos_array[i - 1]
        r_array[i] = (1 + r_array[i] - (trade * fee * 0.5)) * r_array[i - 1]

        trade_array[i] = trade
        # if i < n - trade_delay:
        # if i < n - trade_delay:

        if pos_array[i] != 0 and pos_array[i - 1] == 0:  # 新开仓
            last_open_index = i
            last_direction = pos_array[i]
        elif pos_array[i] != pos_array[i - 1] or (i == n - 1 and pos_array[i] != 0):  # 平仓或反手
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

    # print(trade_record)

    r_annual = (r_array[-1] / r_array[0]) ** (252 / n) - 1
    if abs(max_lose) < 0.001:
        r_l = np.divide(-r_annual, max_lose)
        if np.isnan(r_l):
            r_l = 0
        else:
            r_l = max(r_l, 100)
    else:
        r_l = -r_annual / max_lose
    score_list = [r_l]
    # score_list = [r_annual,max_lose,r_l]
    # print(np.sum(trade_array))
    trade_n = np.sum(trade_array) / (n / 252)
    score_list.append(trade_n)
    trade_record_all = np.array(trade_record[0] + trade_record[1])
    win_record = np.where(trade_record_all > 0)[0]
    # win_n = len(trade_record[0])
    # lose_n = len(trade_record[1])

    win_n = len(win_record)
    lose_n = len(trade_record_all) - win_n
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
    final_score = max(0, final_score)

    # score_list.append(r_array[0])
    # score_list.append(r_array[-1])
    # return r_annual,max_lose
    return final_score, score_list, r_annual, max_lose, r_array, pos_array



def _my_score_interval(y, y_pred,w):
    """ 
    根据分位数生成买卖信号
    x: np.array,shapes:[n] 
    up:分位数阈值上限,0-100
    down:分位数阈值下限,0-100
    period:分位数计算周期，不包括当前值
    在_my_score基础上，根据每年的指数涨跌幅进行加权
    """    
    # # y_pred = y_pred.reshape(-1,)
    # y_pred = y_pred[w]
    # y = y[w]
    # up,down,period = 80,20,60
    # signal = np.ones_like(y_pred) * 0
    # for i in range(period,len(y_pred)):
    #     p = stats.percentileofscore(y_pred[i - period : i],y_pred[i])
    #     if p > up:
    #         signal[i] = 1
    #     elif p < down:
    #         signal[i] = -1
    #     else:
    #         signal[i] = 0
    y_pred = y_pred.reshape(-1, )
    y_pred = y_pred[w]
    y = y[w]

    signal = _create_signal_by_percentile(y_pred)       
    
    close = y
    fee,trade_delay = 0.003,1
    interval = 252
    final_score_all,score_list_all,r_annual_all,max_lose_all = _base_score(signal,close,fee = fee,trade_delay = trade_delay)    

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
    
    score_w = _set_year_weight(index_r_array)
        
    r_adjust = np.exp(np.dot(np.log(1 + my_rlist),score_w)) - 1    
    
    if abs(max_lose_all) < 0.001:
        # r_l = 100
        r_l = np.divide(-r_adjust,max_lose_all)
        if np.isnan(r_l):
            r_l = 0
        else:
            r_l = min(5,r_l)
    else:
        r_l = -r_adjust / max_lose_all

    r_l = min(5, r_l)

    score_list_all[0] = r_l
    final_score = score_list_all[0] * (score_list_all[1] ** 0.5) * score_list_all[2] * (score_list_all[3] ** 0.5)
    # final_score = max(0,final_score)

    penalty = min(0, (score_list_all[0] - 0.3)) + min(0, (score_list_all[1] - 2)) + min(0, (score_list_all[2] - 0.5)) + min(0, (
                score_list_all[3] - 6))
    final_score = 10 * penalty + final_score

    return final_score

def _set_year_weight(r_year_list,up = 0.1,down = -0.09):#根据涨跌幅分配每年的分数权重
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

def _my_score_rl_only(y, y_pred,w):#涨跌权重、只看回撤比(回撤基准-0.05)
    """ 
    策略回测打分
    y_pred: X_Train经过遗传函数处理后的值,np.array,shapes:[n] 
    y:和y_pred对应的目标值,默认为每日收盘价,np.array,shapes:[n] 
    fee:手续费，双边
    trade_delay:交易延迟天数，默认为1，当天计算信号，第二天以收盘价成交
    interval:划区间打分，每个区间的天数
    """
    y_pred = y_pred.reshape(-1, )
    y_pred = y_pred[w]
    y = y[w]

    signal = _create_signal_by_percentile(y_pred)      
    # print(y[0])
    close = y  
    fee,trade_delay = 0.003,1
    interval = 252
    # print(close[0])
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
        # print(i, close[0])
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
    
    score_w = _set_year_weight(index_r_array)
        
    r_adjust = np.exp(np.dot(np.log(1 + my_rlist),score_w)) - 1

    
    if r_adjust >= 0:
        r_l = - r_adjust / (max_lose_all - 0.05)
    else:
        r_l = r_adjust / (1 + max(max_lose_all,-0.9) - 0.05)        
    final_score = r_l
    
    return final_score


def _my_score_lose_penalty(y, y_pred, w):  # 涨跌权重、只看回撤比(回撤基准-0.05)
    """
    策略回测打分  亏损年份给与更多惩罚
    y_pred: X_Train经过遗传函数处理后的值,np.array,shapes:[n]
    y:和y_pred对应的目标值,默认为每日收盘价,np.array,shapes:[n]
    fee:手续费，双边
    trade_delay:交易延迟天数，默认为1，当天计算信号，第二天以收盘价成交
    interval:划区间打分，每个区间的天数
    """

    para = 3
    rf = 0.03

    y_pred = y_pred.reshape(-1, )
    y_pred = y_pred[w]
    y = y[w]

    signal = _create_signal_by_percentile(y_pred)
    # print(y[0])
    close = y
    fee, trade_delay = 0.003, 1
    interval = 252
    # print(close[0])
    final_score_all, score_list_all, r_annual_all, max_lose_all, vol_all = _base_score2(signal, close, fee=fee,
                                                                                        trade_delay=trade_delay)

    # return score_list_all
    signal_all = signal
    close_all = close
    n_data = len(close)
    end_flag = 0
    result = [[0, n_data, close[-1] / close[0] - 1] + score_list_all]

    n_part = round(n_data / interval)
    interval = n_data // n_part
    for i in range(n_part):
        t_start = i * interval
        t_end = min((i + 1) * interval + 2, n_data)
        signal = signal_all[t_start:t_end].copy()
        close = close_all[t_start:t_end].copy()

        final_score, score_list, r_annual, max_lose = _base_score(signal, close, fee=fee, trade_delay=trade_delay)

        result.append([t_start, t_end, close[-1] / close[0] - 1, r_annual] + score_list)
        if end_flag == 1:
            break
    index_r_list = []
    my_rlist = []
    for i in range(1, len(result)):
        index_r_list.append(result[i][2])
        my_rlist.append(result[i][3])

    my_rlist = np.array(my_rlist)

    for i in range(len(my_rlist)):
        if my_rlist[i] < 0:
            my_rlist[i] *= para

    r_mean = np.mean(my_rlist)
    if r_mean - rf > 0:
        final_score = (r_mean - rf) / vol_all
    else:
        final_score = np.log(max(0.00001, 1 + r_mean - rf)) - np.log(1 + vol_all)

    return final_score


def _base_score_fix_lose(signal, close, fee=0.003, trade_delay=1):
    """
    策略回测打分
    signal: 每日信号,np.array,shapes:[n]
    close:每日收盘价,np.array,shapes:[n]
    fee:手续费，双边
    trade_delay:交易延迟天数，默认为1，当天计算信号，第二天以收盘价成交
    """
    fix_lose = -0.03

    n = len(signal)
    pos_array = np.ones_like(signal) * 0
    r_array = np.ones_like(signal)
    trade_array = np.ones_like(signal) * 0

    last_high = -np.inf
    max_lose = 0
    lose_index = [0, 0]

    trade_record = [[], []]
    hold_record = [[], []]
    for i in range(trade_delay, n):
        pos_array[i] = signal[i - trade_delay]
        trade = abs(pos_array[i] - pos_array[i - 1])
        r_array[i] = (close[i] / close[i - 1] - 1) * pos_array[i - 1]
        # print(i, close[i], close[i - 1],r_array[i],trade,r_array[i - 1],fee)
        r_array[i] = (1 + r_array[i] - (trade * fee * 0.5)) * r_array[i - 1]

        trade_array[i] = trade
        # if i < n - trade_delay:
        if 1:
            if pos_array[i] != 0 and pos_array[i - 1] == 0:  # 新开仓
                last_open_index = i
                last_direction = pos_array[i]
            # elif pos_array[i] != pos_array[i - 1]:#平仓或反手
            elif (pos_array[i] != pos_array[i - 1]) or (i == n - 1 and pos_array[i] != 0):  # 平仓或反手
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

    max_lose = max_lose - 0.05
    if abs(max_lose) < 0.001:
        # r_l = 100
        r_l = np.divide(-r_annual,max_lose)
        if np.isnan(r_l):
            r_l = 0
    else:
        r_l = -r_annual / max_lose

    r_l = _my_sigmod(r_l,x_start = 5,k = 1,c = 1)
    score_list = [r_l]

    trade_n = np.sum(trade_array) / (n / 252)
    score_list.append(trade_n)
    # win_n = len(trade_record[0])
    # lose_n = len(trade_record[1])

    trade_record_all = np.array(trade_record[0] + trade_record[1])
    win_record = np.where(trade_record_all > 0)[0]
    win_n = len(win_record)
    lose_n = len(trade_record_all) - win_n

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

    return final_score, score_list, r_annual, max_lose

def _my_sigmod(x,x_start = 5,k = 1,c = 1):
    if x <= x_start:
        f = x
    else:
        f = x_start + (1 / (1 + np.exp(-c * (x - x_start))) - 0.5) * 4 * k / c
    return f


def _my_score_fixed_lose(y, y_pred, w):
    """
    根据分位数生成买卖信号
    x: np.array,shapes:[n]
    up:分位数阈值上限,0-100
    down:分位数阈值下限,0-100
    period:分位数计算周期，不包括当前值
    在_my_score基础上，根据每年的指数涨跌幅进行加权
    """

    y_pred = y_pred.reshape(-1, )
    y_pred = y_pred[w]
    y = y[w]

    signal = _create_signal_by_percentile(y_pred)

    close = y
    fee, trade_delay = 0.003, 1
    interval = 252
    final_score, score_list, r_annual, max_lose = _base_score_fix_lose(signal, close, fee=fee,
                                                                              trade_delay=trade_delay)

    final_score = score_list[0] * (score_list[1] ** 0.5) * score_list[2] * (score_list[3] ** 0.5)
    final_score = final_score
    penalty = min(0,(score_list[0] - 0.25)) + min(0,(score_list[1] - 2)) + min(0,(score_list[2] - 0.5)) + min(0,(score_list[3] - 6))
    final_score = 10 * penalty + final_score

    return final_score

def _my_score_fixed_lose_auto_para(y, y_pred, w):
    """
    根据分位数生成买卖信号
    x: np.array,shapes:[n]
    up:分位数阈值上限,0-100
    down:分位数阈值下限,0-100
    period:分位数计算周期，不包括当前值
    在_my_score基础上，根据每年的指数涨跌幅进行加权
    """

    y_pred = y_pred.reshape(-1, )
    y_pred = y_pred[w]
    y = y[w]

    # signal = _create_signal_by_percentile(y_pred)
    signal = _create_signal_by_percentile_all(y_pred,y,win_rate = 0.49)

    close = y
    fee, trade_delay = 0.003, 1
    interval = 252
    final_score, score_list, r_annual, max_lose = _base_score_fix_lose(signal, close, fee=fee,
                                                                              trade_delay=trade_delay)

    final_score = score_list[0] * (score_list[1] ** 0.5) * score_list[2] * (score_list[3] ** 0.5)
    final_score = final_score
    penalty = min(0,(score_list[0] - 0.25)) + min(0,(score_list[1] - 2)) + min(0,(score_list[2] - 0.5)) + min(0,(score_list[3] - 6))
    final_score = 10 * penalty + final_score

    return final_score


def _my_score_rl_only_auto_para(y, y_pred, w):  # 涨跌权重、只看回撤比(回撤基准-0.05)
    """
    策略回测打分
    y_pred: X_Train经过遗传函数处理后的值,np.array,shapes:[n]
    y:和y_pred对应的目标值,默认为每日收盘价,np.array,shapes:[n]
    fee:手续费，双边
    trade_delay:交易延迟天数，默认为1，当天计算信号，第二天以收盘价成交
    interval:划区间打分，每个区间的天数
    """
    y_pred = y_pred.reshape(-1, )
    y_pred = y_pred[w]
    y = y[w]

    # signal = _create_signal_by_percentile(y_pred)
    signal = _create_signal_by_percentile_all(y_pred, y, win_rate=0.49)
    # print(y[0])
    close = y
    fee, trade_delay = 0.003, 1
    interval = 252
    # print(close[0])
    final_score_all, score_list_all, r_annual_all, max_lose_all = _base_score(signal, close, fee=fee,
                                                                              trade_delay=trade_delay)

    # return score_list_all
    signal_all = signal
    close_all = close
    n_data = len(close)
    end_flag = 0
    result = [[0, n_data, close[-1] / close[0] - 1] + score_list_all]

    n_part = round(n_data / interval)
    interval = n_data // n_part
    for i in range(n_part):
        t_start = i * interval
        t_end = min((i + 1) * interval + 2, n_data)
        signal = signal_all[t_start:t_end].copy()
        close = close_all[t_start:t_end].copy()
        # print(i, close[0])
        final_score, score_list, r_annual, max_lose = _base_score(signal, close, fee=fee, trade_delay=trade_delay)

        result.append([t_start, t_end, close[-1] / close[0] - 1, r_annual] + score_list)
        if end_flag == 1:
            break
    index_r_list = []
    my_rlist = []
    for i in range(1, len(result)):
        index_r_list.append(result[i][2])
        my_rlist.append(result[i][3])

    my_rlist = np.array(my_rlist)

    index_r_array = np.array(index_r_list)

    score_w = _set_year_weight(index_r_array)

    r_adjust = np.exp(np.dot(np.log(1 + my_rlist), score_w)) - 1

    if r_adjust >= 0:
        r_l = - r_adjust / (max_lose_all - 0.05)
    else:
        r_l = r_adjust / (1 + max(max_lose_all, -0.9) - 0.05)
    final_score = r_l

    return final_score

weighted_pearson = _Fitness(function=_weighted_pearson,
                            greater_is_better=True)
weighted_spearman = _Fitness(function=_weighted_spearman,
                             greater_is_better=True)
mean_absolute_error = _Fitness(function=_mean_absolute_error,
                               greater_is_better=False)
mean_square_error = _Fitness(function=_mean_square_error,
                             greater_is_better=False)
root_mean_square_error = _Fitness(function=_root_mean_square_error,
                                  greater_is_better=False)
log_loss = _Fitness(function=_log_loss,
                    greater_is_better=False)

my_score = _Fitness(function=_my_score,
                    greater_is_better=True)

my_score_interval = _Fitness(function=_my_score_interval,greater_is_better=True)

my_score_rl_only = _Fitness(function=_my_score_rl_only,greater_is_better=True)

my_score_rl_only_auto_para = _Fitness(function=_my_score_rl_only_auto_para,greater_is_better=True)

my_score_fixed_lose = _Fitness(function=_my_score_fixed_lose,greater_is_better=True)

my_score_fixed_lose_auto_para = _Fitness(function=_my_score_fixed_lose_auto_para,greater_is_better=True)

my_score_lose_penalty = _Fitness(function=_my_score_lose_penalty,greater_is_better=True)

_fitness_map = {'pearson': weighted_pearson,
                'spearman': weighted_spearman,
                'mean absolute error': mean_absolute_error,
                'mse': mean_square_error,
                'rmse': root_mean_square_error,
                'log loss': log_loss,
                'my_score':my_score,
                'my_score_interval':my_score_interval,
                'my_score_rl_only':my_score_rl_only,
                'my_score_fixed_lose':my_score_fixed_lose,
                'my_score_fixed_lose_auto_para':my_score_fixed_lose_auto_para,
                'my_score_rl_only_auto_para':my_score_rl_only_auto_para,
                'my_score_lose_penalty':my_score_lose_penalty,

                }

