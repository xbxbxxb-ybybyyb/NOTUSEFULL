# -*- coding:utf-8 -*-

# 标签的开发也基于高频基类 开发方式与高频因子完全一致
from SmartFactor.HFBaseFactor import HFBaseFactor
import talib as ta

class Label_test(HFBaseFactor):
    factor_type = "TICK"
    factor_name = "Label_test"
    security_type = "stock"
    security_pool = ['000001.SZ']
    depend_factor = []
    custom_params = {"sample_period":3}
    data_input_mode = ['TICK_RAW']

    def calc(self, price_data, factor_data, custom_params):
        # TODO: 待实现的因子计算方法
        # 返回的高频银子res格式： pandas.Series [index: MDTime value: 因子值]
        df = price_data['tick']
        n_tick=10
        df['value'] = ta.ROC(df['LastPx'].values, timeperiod=n_tick)
        res = df['value'] * 0.8
        res.index = df['MDTime']
        return res