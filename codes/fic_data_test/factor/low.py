import os, sys
from tquant.SmartFactor.BaseFactor import Factor
import pandas as pd
import numpy as np


os.environ["ENV_VERSION"] = ''
os.environ['DSWMAP_envTag'] = 'prd'
class low(Factor):
    """
    Alpha2
    (-1 * DELTA((((CLOSE - LOW) -  (HIGH - CLOSE)) / (HIGH - LOW)), 1))
    """
    factor_type = "DAY"
    factor_name = 'low'  # 设置因子名称
    security_type = 'stock'
    day_lag = 2  # 获取数据的时间窗口长度
    depend_factor = ["market.close","market.low","market.high"]  # 设置依赖因子
    security_pool = "SZA"

    def calc(self, factor_data):

        close = factor_data['BasicDayFactor.close']  # 取出的数据是 index为时间，columns为股票的升序排列
        low = factor_data['BasicDayFactor.low']
        high = factor_data['BasicDayFactor.high']
        # -1*delta(((close-low)-(high-close))/(high-low),1)
        part1 = (2 * close - low - high) / (high - low)
        result = part1.diff(1).iloc[-1] * (-1)

        return result


if __name__ == '__main__':
    factor = alpha2()
    df = factor.run_day_factor_value(start_date='20191102', end_date='20191114', dynamic_load_attr=False)
    print(df)
    print(df.shape)
    #factor.add_factor_days(dt_from='20191112', dt_to='20191115')

