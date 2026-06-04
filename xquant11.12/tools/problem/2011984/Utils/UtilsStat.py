import numpy as np
import math


def calc_r_square(x, y):
    """计算R-Square"""
    x_bar = np.mean(x)
    y_bar = np.mean(y)
    SSR = 0
    var_x = 0
    var_y = 0
    for i in range(0, len(x)):
        diff_x_bar = x[i] - x_bar
        diff_y_bar = y[i] - y_bar
        SSR += (diff_x_bar * diff_y_bar)
        var_x += diff_x_bar ** 2
        var_y += diff_y_bar ** 2
    SST = math.sqrt(var_x * var_y)
    r_square = (SSR / SST) ** 2 if SST != 0 else 0
    return r_square


def calc_corr(x, y):
    x, y = np.array(x), np.array(y)
    return np.corrcoef(x, y)[0][1]


def dict_sel(dict_origin, select_key):
    return dict([(x, y) for (x, y) in dict_origin.items() if x in select_key])


def calculate_mad(x):
    x = x[~np.isnan(x)]
    x_med = np.median(x)
    mad = np.median(np.abs(x - x_med))
    return mad
