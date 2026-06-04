# -*- coding:utf-8 -*-

# 标签的开发也基于高频基类 开发方式与高频因子完全一致
from SmartFactor.HFBaseFactor import HFBaseFactor
import talib as ta

class label_multi_sam(HFBaseFactor):
    factor_type = "TICK"
    factor_name = "label_multi_sam"
    security_type = "stock"
    security_pool = ['000004.SZ']
    depend_factor = []
    custom_params = {"sample_period":10}
    data_input_mode = ['TRANSACTION_SAMPLE']

    def calc(self, price_data, factor_data, custom_params):
        # TODO: 待实现的因子计算方法
        # 返回的高频银子res格式： pandas.Series [index: MDTime value: 因子值]
        tran_price_data = price_data['transaction']
        tran_buymoney_sum = tran_price_data['BuyMoney']['sum']
        res = tran_buymoney_sum.diff(10) / tran_buymoney_sum.shift(10) * 1000
        res.index = tran_price_data['MDTime']
        return res