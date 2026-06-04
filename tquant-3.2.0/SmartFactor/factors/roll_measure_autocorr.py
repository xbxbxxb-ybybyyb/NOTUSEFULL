# -*- coding:utf-8 -*-
from SmartFactor.HFBaseFactor import HFBaseFactor
import pandas as pd
import numpy as np
import time


class roll_measure_autocorr(HFBaseFactor):
    factor_type = "TICK"  # 目前仅支持tick级高频因子的开发
    factor_name = 'roll_measure_autocorr'
    security_type = 'fund' #目前仅支持stock和fund两种证券类型
    security_pool = ['159958.SZ'] #
    depend_factor = []  # 依赖的个人因子
    custom_params = {'interval_seconds':300, 'sample_period': 15}  #

    def calc(self, price_data, factor_data, custom_params):
        def roll_measure_autocorr(price_series: pd.Series, window: int = 2) -> pd.DataFrame:
            """
            :param prices: (pd.Series) prices
            :param window: (int) Estimation window
            :return: (pd.Series) Roll measure
            """
            prices = price_series.diff()
            price_diff_lag = prices.shift(1)
            return (2 * np.sqrt(abs(prices.rolling(2).cov(price_diff_lag)))) / (1 - prices.autocorr())
        # 数据预处理
        df = price_data["tick"]
        # 以下是因子计算逻辑
        buy_one = df['BuyPriceQueue'].apply(lambda x: float(x[0]))
        sell_one = df['SellPriceQueue'].apply(lambda x: float(x[0]))
        high_px = df['IntervalHighPx']
        low_px = df['IntervalLowPx']
        mid_px = (high_px + low_px) / 2
        # 买一卖一部分波动
        bid_ask_spread = buy_one - sell_one
        price_bs = mid_px - bid_ask_spread
        res = roll_measure_autocorr(price_bs, 2)
        # 高频因子的calc方法需要返回一个index为MDTime，value为因子值的pd.Series
        res.index = df['MDTime']
        return res