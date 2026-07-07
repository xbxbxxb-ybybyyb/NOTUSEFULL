# -*- coding: utf-8 -*-
import numpy as np
from MyBaseFactorCal import *
from xquant.factordata import FactorData
import datetime as dt

fa = FactorData()


class FactorDailyGTJA134(DailyFactorPlayerBase):
    """
    *因子名 :
    *因子功能描述：
    *因子参数：
    ["FactorDailyGTJA134",{'n': 0, 'Data_Base': ['play_day_close','play_day_volume'], 'play_day_lag': 13,
    'play_min_lag': None, 'generator_lag': 1,'type': 1500}, "F_D_GTJA134.h5"]

    """
    def __init__(self, alpha_factor_root_path, stock_list, start_date_int, end_date_int, params):
        super().__init__(alpha_factor_root_path, stock_list, start_date_int, end_date_int, params)
        self.n = params['n']

    def load_data(self, data_name_str, start_date, end_date):
        # 获取数据的函数全部在这里编写，最后的index必须为datetime
        data = None
        if data_name_str == 'play_day_volume':
            data = fa.get_factor_value('Basic_factor', stock=stock_list,
                                     mddate=[str(i) for i in range(start_date_int, end_date_int)],
                                     factor_names=['volume'])["volume"].unstack()
            data.index = [dt.datetime.strptime(x, "%Y%m%d") for x in data.index]

            # play_day_volume = Dtk.get_panel_daily_pv_df(self.stock_list, start_date, end_date, pv_type='volume',
            #                                    adj_type='FORWARD')
            # data = Dtk.convert_df_index_type(play_day_volume, 'date_int', 'datetime')
        elif data_name_str == 'play_day_close':
            data = fa.get_factor_value("Basic_factor", stock=stock_list,
                                       mddate=[str(i) for i in range(start_date_int, end_date_int)],
                                       factor_names=["close"])["close"].unstack()
            data.index = [dt.datetime.strptime(x, "%Y%m%d") for x in data.index]
        return data

    def factor_generator(self):
        # 数据通过self.data_base字典获取
        alpha = self.play_intermediate(self.intermediate)
        return alpha

    def intermediate(self):
        volume = self.data_base_play['play_day_volume']
        close = self.data_base_play['play_day_close']
        ans = (close - close.shift(self.play_day_lag-1)) / (close.shift(self.play_day_lag-1)) * volume
        ans = ans.iloc[-1, :]
        ans[ans == 0] = np.nan
        return ans


if __name__=="__main__":
    stock_list = fa.hset('INDEX', '20180830', 'HS300')["stock"].tolist()
    start_date_int = 20180101
    end_date_int = 20180630

    params = {'n': 0, 'Data_Base': ['play_day_close','play_day_volume'], 'play_day_lag': 13,
    'play_min_lag': None, 'generator_lag': 1,'type': 1500}

    obj = FactorDailyGTJA134(alpha_factor_root_path="", stock_list=stock_list, start_date_int=start_date_int,
                             end_date_int=end_date_int, params=params)

    print(obj.factor_calc())

