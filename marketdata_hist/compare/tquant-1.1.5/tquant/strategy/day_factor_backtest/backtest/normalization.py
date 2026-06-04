# -*- coding: utf-8 -*-
"""
Created on Wed Aug 29 16:44:07 2018

@author: hezq
"""
import numpy as np
import pandas as pd
import warnings

warnings.simplefilter(action="ignore", category=RuntimeWarning)


# zhoux的去极值与标准化程序,结果差距最终在于median的区别
# 1.将 nan和inf的值均设为nan
# 2.极值小于有效数字个数的0.1，则进行去极值，否则不去极值
# 3.去极值后如果std==0,则直接减去平均数（避免了标准化后为inf）
# 4.选择功能有axis（对行还是列做去极值以及标准化）


class Normalization2:
    def __init__(self, factor, axis=0, remove_extreme_method='mad', standard=True, weight=5):
        self.factor = factor
        self.axis = axis
        self.extreme = remove_extreme_method  # 去极值的方法，可供选择'mad'（中位数去极值）,'std'（sigma去极值）
        self.standard = standard
        self.weight = weight

    def get_valid(self, factor):  # 满足条件1
        factor[np.isinf(factor)] = np.nan
        return factor

    def mad_remove_extreme(self, arr):  # arr是一个一维向量，'mad'去极值方法，满足条件2

        diversion = len(np.unique(arr[~np.isnan(arr)])) / (~np.isnan(arr)).sum()

        if diversion > 0.1 and ~np.isinf(diversion):

            md = np.nanmedian(arr)
            mdmd = np.nanmedian(abs(arr[arr != md] - md))

            upper = md + self.weight * mdmd
            lower = md - self.weight * mdmd

            if ((arr > upper) | (arr < lower)).sum() <= (~np.isnan(arr)).sum() * 0.1:
                arr[arr > upper] = upper
                arr[arr < lower] = lower

            elif ((arr > upper) | (arr < lower)).sum() <= (~np.isnan(arr)).sum() * 0.2:
                upper = md + (self.weight + 1) * mdmd
                lower = md - (self.weight + 1) * mdmd
                arr[arr > upper] = upper
                arr[arr < lower] = lower

            else:
                upper = md + (self.weight + 2) * mdmd
                lower = md - (self.weight + 2) * mdmd
                arr[arr > upper] = upper
                arr[arr < lower] = lower

        return arr

    def std_remove_extreme(self, arr):  ## arr是一个一维向量，'std'去极值方法，满足条件2

        diversion = len(np.unique(arr[~np.isnan(arr)])) / (~np.isnan(arr)).sum()

        if diversion > 0.1 and ~np.isinf(diversion):

            mu = np.nanmean(arr)
            sigma = np.nanstd(arr, ddof=1)

            upper = mu + self.weight * sigma
            lower = mu - self.weight * sigma

            if (((arr > upper) | (arr < lower)).sum() <= (~np.isnan(arr)).sum() * 0.1):
                arr[arr > upper] = upper
                arr[arr < lower] = lower

            elif (((arr > upper) | (arr < lower)).sum() <= (~np.isnan(arr)).sum() * 0.2):
                upper = md + (self.weight + 1) * mdmd
                lower = md - (self.weight + 1) * mdmd
                arr[arr > upper] = upper
                arr[arr < lower] = lower

            else:
                upper = md + (self.weight + 2) * mdmd
                lower = md - (self.weight + 2) * mdmd
                arr[arr > upper] = upper
                arr[arr < lower] = lower

        return arr

    def norm_dataframe(self):
        index_ = self.factor.index
        columns_ = self.factor.columns
        factor = self.factor.astype(np.float64).values

        factor = self.get_valid(factor)  # 确保是深复制

        if self.axis == 1:  # axis 选择功能，默认是对行做去极值，标准化，满足条件4
            factor = factor.T
        if self.extreme == 'mad':
            factor = np.apply_along_axis(self.mad_remove_extreme, 1, factor)
        elif self.extreme == 'std':
            factor = np.apply_along_axis(self.std_remove_extreme, 1, factor)

        if self.standard:
            mu = np.nanmean(factor, axis=1)
            sigma = np.nanstd(factor, axis=1, ddof=1)
            factor[sigma == 0, :] = np.subtract(factor[sigma == 0, :].T, mu[sigma == 0]).T
            factor[sigma != 0, :] = np.divide(np.subtract(factor[sigma != 0, :].T, mu[sigma != 0]), sigma[sigma != 0]).T

        if self.axis == 1:  # 将最后的结果转置（与前面的axis）保持一致
            factor = factor.T
        return pd.DataFrame(factor, index=index_, columns=columns_)
