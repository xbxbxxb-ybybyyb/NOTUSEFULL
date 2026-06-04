# -*- coding: utf-8 -*-
from SmartFactor.HFBaseFactor import HFBaseFactor

class hfre_multi_sam(HFBaseFactor):
    factor_type = "TICK"
    factor_name = "hfre_multi_sam"
    security_type = "stock"
    security_pool = ['000004.SZ']
    depend_factor = []
    data_input_mode = ['TRANSACTION_SAMPLE']
    custom_params = {"sample_period":10}
    def calc(self, price_data, factor_data, custom_params):
        # TODO: 待实现的因子计算方法
        # 返回的高频因子res格式：pandas.Series  [index : MDTime value: 因子值]
        tran_price_data = price_data['transaction']
        tran_buymoney_sum = tran_price_data['BuyMoney']['sum']
        res = tran_buymoney_sum.diff(10) / tran_buymoney_sum.shift(10) * 1000
        res.index = tran_price_data['MDTime']
        return res


if __name__ == "__main__":
    start_date = '20191104'
    end_date = '20191104'
    ins = hfre_multi_sam()
    res = ins.run_hfre_factor_value(start_date=start_date, end_date=end_date)
    print(res)