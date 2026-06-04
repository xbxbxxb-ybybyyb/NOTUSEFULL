import pandas as pd
import numpy as np
from pathlib import Path
import json
import datetime as dt


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate
    
@static_vars(tic=dt.datetime.now())
def pprint(*args, **kwargs):
    print(('%.3fs <- prev msg: ' % (dt.datetime.now() - pprint.tic).total_seconds()).rjust(22), *args, **kwargs)
    pprint.tic = dt.datetime.now()


def multi_astype(pd_raw):
    y = pd_raw.reset_index()
    y.Ticker = y.Ticker.astype('category')
    y.set_index(['dt', 'Ticker'], append=False, inplace=True)
    y = y.sort_index(level=0)
    return y

def multi_astype_obj(pd_raw):
    y = pd_raw.reset_index()
    y.Ticker = y.Ticker.astype('object')
    y.set_index(['dt', 'Ticker'], append=False, inplace=True)
    y = y.sort_index(level=0)
    return y

def pd_unstack(pd_raw):
    if type(pd_raw) == pd.DataFrame:
        columns_lst = pd_raw.columns
    elif type(pd_raw) == pd.Series:
        columns_lst = []
    else:
        raise AssertionError
    if len(columns_lst) > 1:
        rtn = {}
        for item in columns_lst:
            rtn[item]= pd_raw[item].unstack()
    else:
        rtn = pd_raw.unstack()
    return rtn


def tracer(key):
    path = Path.home().joinpath('multifactor.json')
    counter = read_tracer(path)
    counter = auto_add(key, counter)
    set_tracer(path, counter)


def read_tracer(path):
    Path.touch(path)
    with open(path, 'r') as fin:
        try:
            counter = json.load(fin)
        except json.JSONDecodeError:
            counter = None
    return counter


def set_tracer(path, value):
    Path.touch(path)
    with open(path, 'w') as fout:
        json.dump(value, fout)


def auto_add(key, var):
    if var is None:
        var = dict()
    if key in var:
        var[key] += 1
    else:
        var[key] = 1
    return var


def resider(x, y, method='lstsq', add_const=True, mean_only=False, r_square=False, return_sm=False):
    # Two step regression
    # 1: Determine dummy columns in matrix and use them to remove mean
    # 2: Regular ols: OLS or least square to calculate residual
    # Direct OLS or least square may have problems with dummy columns with few 1s
    # Less computation and more robustness
    # x -> axis0: stocks, axis1: factors
    y = y.flatten()  # 1-D array
    dummy_cols = np.apply_along_axis(is_dummy, 0, x)
    d_array = x[:, dummy_cols]
    s_array = x[:, ~dummy_cols]
    r2 = np.nan
    if d_array.shape[1] != 0:
        d_mean_array = np.array([i / j if j != 0 else 0 for i, j in
                                 zip(np.dot(d_array.T, y).flatten(), d_array.sum(axis=0))])
        y = y - np.dot(d_array, d_mean_array)
    if not mean_only and s_array.shape[1] != 0:
        if method == 'lstsq':
            if add_const:
                # Prepend constant in accordance with sm.OLS
                x = np.concatenate((np.ones((s_array.shape[0], 1)), s_array), axis=1)
            else:
                x = s_array
            try:
                coeff, residual_sum = np.linalg.lstsq(x, y, rcond=None)[0:2]
                resid = y - np.dot(x, coeff)
                if r_square:
                    r2 = 1 - residual_sum[0] / (y.size * y.var())
            except:
                resid = np.full_like(y, np.nan, dtype=np.double)
        elif method == 'sm.OLS':
            import statsmodels.api as sm
            x = s_array
            try:
                if add_const:
                    ols_problem = sm.OLS(y, sm.add_constant(x)).fit()
                else:
                    ols_problem = sm.OLS(y, x).fit()
                if return_sm:
                    return ols_problem
                resid = ols_problem.resid
                if r_square:
                    r2 = ols_problem.rsquared
            except:
                resid = np.full_like(y, np.nan, dtype=np.double)
        else:
            raise AssertionError
    else:
        resid = y
    if r_square:
        return resid, r2
    else:
        return resid


def is_dummy(x):
    x = np.array(x) if not isinstance(x, np.ndarray) else x
    one_num = np.count_nonzero(x == 1)
    zero_num = np.count_nonzero(x == 0)
    if one_num + zero_num == x.size:
        return True
    else:
        return False

        