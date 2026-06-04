from xfactor.BaseFactor import BaseFactor
import numpy as np


class SampleFixFactor(BaseFactor):
    factor_type = 'FIX'
    depend_data = ['FactorData.Basic_factor.amt_minute']
    minute_lag = 10
    reform_window = 5

    def calc_single(self, database):
        amt = database.depend_data['FactorData.Basic_factor.amt_minute']
        factor_value = amt.std()
        return factor_value

    def reform(self, temp_result):
        return temp_result.rolling(self.reform_window, min_periods=1).apply(lambda x: np.nanstd(x, ddof=1))
