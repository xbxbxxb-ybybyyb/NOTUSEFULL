# -*- coding: utf-8 -*-
"""
   File Name：     factor_factory_py
   Author :        k0180110
   Modify Date:    2019-11-13
"""
import pandas as pd
import numpy as np
from scipy.stats import stats
from sklearn.linear_model import LinearRegression
from statsmodels.regression.linear_model import OLS
import statsmodels.api as sm


class Func:

    @staticmethod
    def dtm(open, high):
        condition = open.diff(1) <= 0
        open = condition * np.maximum((high - open), open.diff(1))
        return open

    @staticmethod
    def dbm(open, low):
        condition = open.diff(1) > 0
        open = condition * np.maximum((open - low), open.diff(1))
        return open

    @staticmethod
    def max_df(df1, df2):
        df3 = pd.concat([df1, df2], axis=0)
        result = df3.max()
        return result

    @staticmethod
    def tr(high, low, close):
        part1 = high - low
        part2 = Func.abs((high - Func.delay(close)))
        part3 = Func.max_df(part1, part2)
        part4 = low - Func.delay(close)
        result = Func.max_df(part3, part4)
        return result

    @staticmethod
    def hd(high):
        result = high - Func.delay(high)
        return result

    @staticmethod
    def ld(low):
        result = Func.delay(low) - low
        return result

    @staticmethod
    def count(df, window=10, condition=True):
        """对df前n项条件求数量，df所有数据置为1，其中condition表示选择条件"""
        df.iloc[:, :] = 1
        return Func.ts_sum(df * condition, window)

    @staticmethod
    def FILTER(df, condition=True):
        return df * condition

    @staticmethod
    def fama(self):
        pass

    @staticmethod
    def sumac_df(df, window=10):
        """序列df过去n天累乘"""
        return df.rolling(window).sum()

    @staticmethod
    def rolling_decay(df):
        """用于wma函数"""
        weight = range(1, len(df) + 1)[::-1] / np.array(range(1, len(df) + 1)).sum()
        weight = np.array(weight).reshape(1, -1)
        return np.dot(weight, np.asarray(df))

    @staticmethod
    def decayliner(df, window):
        df.fillna(method='ffill', inplace=True)
        df.fillna(method='bfill', inplace=True)
        df.fillna(value=0, inplace=True)
        return df.rolling(window).apply(Func.rolling_decay, raw=True)

    @staticmethod
    def rolling_wma(df):
        """用于wma函数"""
        weight = (Func.sequence(len(df)) - 1)[::-1] * 0.9 * 2 / (len(df) * (len(df) + 1))
        weight = np.array(weight).reshape(1, -1)
        return np.dot(weight, np.asarray(df))

    @staticmethod
    def wma_df(df, window):
        df.fillna(method='ffill', inplace=True)
        df.fillna(method='bfill', inplace=True)
        df.fillna(value=0, inplace=True)
        result = df.rolling(window).apply(Func.rolling_wma, raw=True)
        return result

    @staticmethod
    def rolling_rank(na):
        return stats.rankdata(na)[-1] / len(na)

    @staticmethod
    def ts_rank(df, window=10):
        """序列df的末位值在过去n天的顺序排位"""
        return df.rolling(window).apply(Func.rolling_rank)

    @staticmethod
    def ts_min(df, window=10):
        """序列df过去n天的最小值"""
        return df.rolling(window).min()

    @staticmethod
    def ts_max(df, window=10):
        """序列df过去n天的最大值"""
        return df.rolling(window).max()

    @staticmethod
    def delay(df, period=1):
        """df延迟period长度的值"""
        return df.shift(period)

    @staticmethod
    def ts_sum(df, window=10):
        """序列df过去n天求和"""
        return df.rolling(window).sum()

    @staticmethod
    def sumif(df, window=10, condition=True):
        """对df前n项条件求和，其中condition表示选择条件"""
        return Func.ts_sum(df * condition, window)

    @staticmethod
    def sign(df):
        """对df取符号函数"""
        return np.sign(df)

    @staticmethod
    def sequence(n):
        """生成 1~n 的等差序列"""
        return np.asarray(range(1, n + 1))

    @staticmethod
    def rank(df):
        """向量df升序排序"""
        return df.rank(axis=1, pct=True)

    @staticmethod
    def rolling_prod(na):
        """prod 的辅助函数"""
        return np.prod(na)

    @staticmethod
    def prod(df, window=10):
        """序列df过去n天累乘"""
        return df.rolling(window).apply(Func.rolling_prod, raw=True)

    @staticmethod
    def mean(df, window=10):
        """序列df过去n天均值"""
        return df.rolling(window).mean()

    # ------------------已用
    @staticmethod
    def stddev(df, window=10):
        """序列df过去n天标准差"""
        return df.rolling(window).std()

    @staticmethod
    def correlation(df1, df2, windows=10):
        result = df1.rolling(windows).corr(df2)
        return result

    @staticmethod
    def coviance(df1, df2, windows=10):
        result = df1.rolling(windows).cov(df2)
        return result

    @staticmethod
    def abs(df):
        return df.abs()

    """ 
    def sma(df, n, m):
        # Yi+1 =(dfi*m+Yi*(n-m))/n，其中Y表示最终结果 
        # Clean data
        if pd.Series(df).isnull().any():
            df.fillna(method='ffill', inplace=True)
            df.fillna(method='bfill', inplace=True)
            df.fillna(value=0, inplace=True)
        y = [list(df)[0]]
        for x in range(0, len(list(df)) - 1):
            y.append((list(df)[x] * m + y[-1] * (n - m)) / n)
        return y

    for col in close.columns:
        close[col] = Func.sma(close[col], 3, 1)
    """

    @staticmethod
    def sma(na, n, m):
        y = [list(na)[0]]
        for x in range(1, len(list(na))):
            y.append((list(na)[x] * m + y[-1] * (n - m)) / n)
        return y[-1]

    @staticmethod
    def sma_df(df, n, m):
        """Yi+1 =(dfi*m+Yi*(n-m))/n，其中Y表示最终结果"""
        df.fillna(method='ffill', inplace=True)
        df.fillna(method='bfill', inplace=True)
        df.fillna(value=0, inplace=True)
        return df.rolling(window=n).apply(Func.sma, args=(n, m))

    @staticmethod
    def sma_df_2(df, n, m):
        """Yi+1 =(dfi*m+Yi*(n-m))/n，其中Y表示最终结果"""
        df.fillna(method='ffill', inplace=True)
        df.fillna(method='bfill', inplace=True)
        df.fillna(value=0, inplace=True)
        y = df.iloc[0:1]
        for x in range(1, len(df)):
            y = y.append((df.iloc[x] * m / n) + (y.iloc[-1] * (n - m) / n), ignore_index=True)
        y.index = df.index
        return y

    # 调用方式
    # qqq = Func.sma_df(close, 3, 1)

    @staticmethod
    def reg_beta(x_df, y_df):
        # 传进来的是df，循环每一列和df_b做回归
        y = np.array(y_df).reshape(-1, 1)
        x = np.array(x_df).reshape(-1, 1)
        x = sm.add_constant(x)
        res = sm.OLS(y, x)
        res_fit = res.fit()
        try:
            return res_fit.params[1]
        except IndexError as err:
            return res_fit.params[0]

    @staticmethod
    def reg_sigma(x_df, y_df):
        # 传进来的是df，循环每一列和df_b做回归
        y = np.array(y_df).reshape(-1, 1)
        x = np.array(x_df).reshape(-1, 1)
        x = sm.add_constant(x)
        res = sm.OLS(y, x)
        res_fit = res.fit()
        result = y - res.predict(res_fit.params)
        return result

    @staticmethod
    def ts_argmax(df):
        """用于highday函数"""
        # 这个为什么再-1
        return len(df) - np.argmax(df) - 1

    @staticmethod
    def highday(df, window=10):
        return df.rolling(window).apply(Func.ts_argmax, raw=True)

    @staticmethod
    def ts_argmin(df):
        """用于highday函数"""
        # 这个为什么再-1
        return len(df) - np.argmin(df) - 1

    @staticmethod
    def lowday(df, window=10):
        return df.rolling(window).apply(Func.ts_argmin, raw=True)
