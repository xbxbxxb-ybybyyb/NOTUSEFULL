"""Metrics to evaluate the fitness of a program.

The :mod:`gplearn.fitness` module contains some metric with which to evaluate
the computer programs created by the :mod:`gplearn.genetic` module.
"""

# Author: Trevor Stephens <trevorstephens.com>
#
# License: BSD 3 clause

import numbers

import numpy as np
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


def _my_score(y, y_pred,w):
    
    
    """ 
    根据分位数生成买卖信号
    x: np.array,shapes:[n] 
    up:分位数阈值上限,0-100
    down:分位数阈值下限,0-100
    period:分位数计算周期，不包括当前值
    """    
    # y_pred = y_pred.reshape(-1,)
    y_pred = y_pred[w]
    y = y[w]
    up,down,period = 80,20,60
    signal = np.ones_like(y_pred) * 0
    for i in range(period,len(y_pred)):
        p = stats.percentileofscore(y_pred[i - period : i],y_pred[i])
        if p > up:
            signal[i] = 1
        elif p < down:
            signal[i] = -1
        else:
            signal[i] = 0
        

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
    
    if abs(max_lose) < 0.001:
        r_l = 100
    else:
        r_l = -((r_array[-1] / r_array[0]) ** (252 / n) - 1) / max_lose
    score_list = [r_l]
    
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
    # final_score = max(0,final_score)    
    final_score = final_score
    penalty = min(0,(score_list[0] - 0.3)) + min(0,(score_list[1] - 2)) + min(0,(score_list[2] - 0.5)) + min(0,(score_list[3] - 6))
    final_score = 10 * penalty + final_score
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

_fitness_map = {'pearson': weighted_pearson,
                'spearman': weighted_spearman,
                'mean absolute error': mean_absolute_error,
                'mse': mean_square_error,
                'rmse': root_mean_square_error,
                'log loss': log_loss,
                'my_score':my_score
                }
