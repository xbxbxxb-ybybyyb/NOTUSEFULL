# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     FactorFunc
   Description :    因子相关计算
   Author :       K0380044
   date：          2019/11/20
-------------------------------------------------
   Change Activity:
                   2019/11/20:
-------------------------------------------------
"""

from functools import reduce
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


class FacFunc:
    @staticmethod
    def SMA(s1, n, m):
        """
        :param s1: pd.Series
        :param n: int n
        :param m: int weight n>m
        :return:float
        question:why fillna 0? point?
        """
        s1.fillna(method='ffill', inplace=True)
        s1.fillna(method='bfill', inplace=True)
        s1.fillna(value=0, inplace=True)
        # return reduce(lambda x, y: y * m / n + x * (n - m) / n, s1)
        return s1.ewm(alpha=m / n).mean()

    @staticmethod
    def TSMAX(s1, n):
        """
        TSMAX(A, n) 序列A 过去n 天的最大值
        :param s1:
        :param n:
        :return:
        """
        return s1.rolling(n).max()

    @staticmethod
    def TSMIN(s1, n):
        """
        TSMIN(A, n) 序列A 过去n 天的最小值
        :param s1:
        :param n:
        :return:
        """
        return s1.rolling(n).min()

    @staticmethod
    def RANK(s1):
        """
        向量A 升序排序
        :param s1:pd.Series
        :return:
        qustion:只是排序 sort
        无百分比
        """
        # return s1.rank(pct=False)
        return s1.sort_values()

    @staticmethod
    def TSRANK(s1, window=10):
        """
        TSRANK(A, n)    序列 A 的末位值在过去 n 天的顺序排位
        :param s1:
        :return value
        """
        return s1.rank().iloc[-1]/window

    @staticmethod
    def COVIANCE(s1, s2, windows=10):
        """
        COVIANCE (A, B, n) 序列A、B 过去n 天协方差
        :param s1:
        :param s2:
        :param windows:
        :return:
        """
        result = s1.rolling(windows).cov(s2)
        return result

    @staticmethod
    def DELAY(s1, period=1):
        """
        delay 1 sdk窗口至少是2
        :param s1:
        :param period:
        :return:pd.Series  alpha84
        """
        return s1.shift(period)

    @staticmethod
    def SUM(s1, n):
        """
        SUM(A, n)   序列 A 过去 n 天求和
        :param s1:
        :param n:
        :return:
        """
        s1.fillna(method='ffill', inplace=True)
        s1.fillna(method='bfill', inplace=True)
        return s1.rolling(n).sum()

    @staticmethod
    def MEAN(s1, window=10):
        """
        MEAN(A, n)序列 A 过去 n 天均值
        :param s1:
        :param window:
        :return:
        """
        s1.fillna(method='ffill', inplace=True)
        s1.fillna(method='bfill', inplace=True)
        return s1.rolling(window).mean()

    @staticmethod
    def DELTA(s1, n):
        """
        序列A值与过去第n天的差值
        :param s1:
        :param n:
        :return:
        """
        return s1 - s1.shift(n)

    @staticmethod
    def DECAYLINEAR(s1, n):
        """
        DECAYLINEAR(A, d)   对 A 序列计算移动平均加权，其中权重对应 d,d-1,…,1（权重和为 1）
        :return: 
        """
        s1.fillna(method='ffill', inplace=True)
        s1.fillna(method='bfill', inplace=True)
        s1.fillna(value=0, inplace=True)
        return s1.rolling(n).apply(FacFunc.rolling_decay, raw=True)

    @staticmethod
    def rolling_decay(s1):
        """
        :param s1:
        :return:
        """
        n = len(s1)
        w = np.array(range(1, n + 1)[::-1])
        t = w.sum()
        return (w / t * s1).sum()
        # weight = range(1, len(df) + 1)[::-1] / np.array(range(1, len(df) + 1)).sum()
        # weight = np.array(weight).reshape(1, -1)
        # return np.dot(weight, np.asarray(df))

    @staticmethod
    def CORR(s1, s2, n):
        """
        CORR(A, B, n)   序列 A、 B 过去 n 天相关系数
        :param s1:
        :param s2:
        :return:
        """
        s1.fillna(method='ffill', inplace=True)
        s1.fillna(method='bfill', inplace=True)
        s2.fillna(method='ffill', inplace=True)
        s2.fillna(method='bfill', inplace=True)
        return s1.rolling(n).corr(s2)

    @staticmethod
    def STD(s1, window=10):
        """
        STD(A, n)   序列 A 过去 n 天标准差
        :param s1:
        :param window:
        :return:
        """
        return s1.rolling(window).std()

    @staticmethod
    def MAX(A, B):
        """
        MAX(A, B)在 A,B 中选择最大的数
        :param A:
        :param B:
        :return:
        """
        return max(A, B)

    @staticmethod
    def REGBETA(s1, s2):
        """
        REGBETA(A, B, n)    前 n 期样本 A 对 B 做回归所得回归系数

        :param s1:
        :param s2:
        :return:
        """
        linreg = LinearRegression()
        linreg.fit(pd.DataFrame(s1), s2)
        return linreg.coef_[0]

    @staticmethod
    def REGRESI(s1, s2):
        """
        REGRESI(A, B, n)    前 n 期样本 A 对 B 做回归所得的残差
        :param s1:
        :param s2:
        :return:
        """
        linreg = LinearRegression()
        linreg.fit(pd.DataFrame(s1), s2)
        return linreg.intercept_

    @staticmethod
    def WMA(s1, window):
        """
        计算 A前 n期样本加权平均值权重为 0.9i，(i 表示样本距离当前时点的间隔)
        :param s1:
        :param window:
        :return:
        """
        s1.fillna(method='ffill', inplace=True)
        s1.fillna(method='bfill', inplace=True)
        s1.fillna(value=0, inplace=True)
        result = s1.rolling(window).apply(lambda x: np.average(x, weights=list(range(len(x)))[::-1]), raw=False)
        return result


if __name__ == '__main__':
    s1 = pd.Series([1, 2, 3, 4, 5], name='s1')
    s2 = pd.Series([2, 3, 4, 4, 4.5], name='s2')
    s3 = pd.Series([3, 5, 7], name='3')
    df1 = pd.DataFrame([[1.1, 2, 3], [3, 2, 1]],columns=list('ABC'))
    print(FacFunc.CORR(s1,s3,3))

