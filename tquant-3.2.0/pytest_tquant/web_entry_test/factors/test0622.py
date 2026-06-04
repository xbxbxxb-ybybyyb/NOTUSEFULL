# -*- coding: utf-8 -*-
from SmartFactor.BaseFactor import Factor


class test0622(Factor):
    
    factor_type = "DAY"         # 因子类型 ： 日频(DAY)
    factor_name = 'test0622'  # 设置因子名称，因子名称只包含大小写字母，数字或下划线。
    security_type = 'stock'     # 因子适用的证券类型， 股票stock 基金fund（开发中） 债券bond（开发中） 期货future（开发中）
    day_lag = 2  # 需要回溯的日频时间窗口，单位为天，低频因子专用
    quarter_lag = 2 # 需要回溯的季度窗口，单位为季度，若计算需要依赖财务类因子，可通过该参数设置回溯的时间。
    #财务类因子： BasicFinancialFactor.    日频因子 BasicDayFactor.close,BasicDayFactor.alpha 个人因子：因子库名.因子名
    depend_factor = ["market.close", "market.low", "market.high"]  # 设置依赖因子
    security_pool = "ALLA"       # 标的池  str or List 例如：“ALLA”,"SHA","SZA",['000001.SZ','601688.SH']

    def calc(self, factor_data, dt_to):
        # TODO: 待实现的因子类方法
        # params: factor_data: 创建因子时选择的依赖因子的数据，格式为 multiindex DataFrame， 形如：
        # params: dt_to：fator_data中提供了 dt_to-day_lag 到 dt_to 或者 dt_to前quarter_lag个季度 的依赖因子数据。
        # return：pandas.Series [index : 标的 value: 因子值]
        close = factor_data['BasicDayFactor.close']  
        low = factor_data['BasicDayFactor.low']
        high = factor_data['BasicDayFactor.high']
        part1 = (2 * close - low - high) / (high - low)
        res = part1.diff(1).loc[dt_to] * (-1)
        return res



if __name__ == "__main__":
    start_date = '20191102'
    end_date = '20191114'
    ins = test0622()
    res = ins.run_day_factor_value(start_date=start_date, end_date=end_date)
    print(res)