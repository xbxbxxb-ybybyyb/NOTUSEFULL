#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/6/2 21:09
import numpy as np
import warnings

warnings.simplefilter(action="ignore", category=RuntimeWarning)


class PreProcessData:
    @staticmethod
    def winsorize(factor_data, weight=5):
        """"""
        md = np.nanmedian(factor_data, axis=0)
        mad = np.nanmedian(np.abs(np.subtract(factor_data, md)), axis=0)
        upper = md + weight * mad
        lower = md - weight * mad

        factor_data = np.clip(factor_data, lower, upper)

        return lower, upper, factor_data

    @staticmethod
    def compute_m12(factor_data):
        mu = np.nanmean(factor_data, axis=0)
        sigma = np.nanstd(factor_data, axis=0)
        return mu, sigma

    def normalize(self, factor_data):
        """"""
        mu, sigma = self.compute_m12(factor_data)

        factor_data[:, sigma == 0] = np.subtract(factor_data[:, sigma==0], mu[sigma == 0])
        factor_data[:, sigma != 0] = np.divide(np.subtract(factor_data[:, sigma != 0], mu[sigma != 0]), sigma[sigma != 0])

        return mu, sigma, factor_data


## 去极值与标准化程序,结果差距最终在于median的区别
## 1.去极值后如果std==0,则直接减去平均数
## 2 去极值的方法，可供选择"mad"（中位数去极值）, "std"（sigma去极值）
## 3.选择功能有axis（对行(axis=0)还是列(axis=1)做去极值以及标准化）

class Normalization:
    def __init__(self, axis=1, winsorize_method="mad", weight=5, standard=True):
        self.axis = axis
        self.winsorize_method = winsorize_method
        self.standard = standard
        self.weight = weight

    def mad_remove_extreme(self, arr):
        md = np.nanmedian(arr)
        mad = np.nanmedian(abs(arr - md))

        upper = md + self.weight * mad
        lower = md - self.weight * mad

        arr[arr > upper] = upper
        arr[arr < lower] = lower

        return arr

    def std_remove_extreme(self, arr):
        mu = np.nanmean(arr)
        sigma = np.nanstd(arr, ddof=1)

        upper = mu + self.weight * sigma
        lower = mu - self.weight * sigma

        arr[arr > upper] = upper
        arr[arr < lower] = lower

        return arr

    def winsorize(self, factor_data):
        if self.winsorize_method == "mad":
            factor_data = np.apply_along_axis(self.mad_remove_extreme,  1 - self.axis, factor_data)
        elif self.winsorize_method == "std":
            factor_data = np.apply_along_axis(self.std_remove_extreme,  1 - self.axis, factor_data)
        return factor_data

    def normalize(self, factor_data):
        if self.axis == 1:
            factor_data = factor_data.T

        mu = np.nanmean(factor_data, axis=1)
        sigma = np.nanstd(factor_data, axis=1, ddof=1)

        if self.standard:
            factor_data[sigma == 0, :] = np.subtract(factor_data[sigma == 0, :].T, mu[sigma == 0]).T
            factor_data[sigma != 0,:] = np.divide(np.subtract(factor_data[sigma != 0, :].T, mu[sigma != 0]), sigma[sigma != 0]).T

        if self.axis == 1:
            factor_data = factor_data.T

        return mu, sigma, factor_data



