from xfactor.BaseFactor import BaseFactor
import numpy as np
from scipy.stats import linregress

class GTJA021(BaseFactor):
    #  定义因子参数

    # 因子频率，。默认为日频因子， 可不设置
    factor_type = "DAY"
    # 依赖的平台原始数据，包括FactorData和MarketData接口中的数据。 默认为空，必须设置
    depend_data = ["FactorData.Basic_factor.close", "FactorData.Basic_factor.adjfactor"]
    # 计算每个时点的因子所需要前移的数据窗口大小
    # 例如，为日频因子，lag=3表示计算某一日的因子值需要依赖前三个交易日和当日的数据，默认为0，可不设置
    lag = 9
    lag_in = 6

    # 每次播放的计算具体方法。必须实现。
    def calc_single(self, database):
        adjfactor = database.depend_data['FactorData.Basic_factor.adjfactor']
        close = database.depend_data['FactorData.Basic_factor.close'] * adjfactor
        close_ma = close.rolling(self.lag, min_periods=self.lag-self.lag_in+1).mean()
        close_ma_change = (close_ma - close_ma.shift(1)) / close_ma.shift(1)
        ans = close_ma_change.iloc[-self.lag_in:].apply(self.filtered_linregress)
        ans[ans == 0] = np.nan
        return ans

    def filtered_linregress(self, seq):
        target = np.arange(1,self.lag_in+1)
        slope, _, _, p_value, _ = linregress(target, seq)
        if p_value > 0.05:
            return np.nan
        else:
            return slope
