from xfactor.BaseFactor import BaseFactor
import numpy as np


class GTJA002(BaseFactor):
    #  定义因子参数

    # 因子频率，。默认为日频因子， 可不设置
    factor_type = "DAY"
    # 依赖的平台原始数据，包括FactorData和MarketData接口中的数据。 默认为空，必须设置
    depend_data = ["FactorData.Basic_factor.close", "FactorData.Basic_factor.high", "FactorData.Basic_factor.low","FactorData.Basic_factor.adjfactor"]
    # 计算每个时点的因子所需要前移的数据窗口大小
    # 例如，为日频因子，lag=3表示计算某一日的因子值需要依赖前三个交易日和当日的数据，默认为0，可不设置
    lag = 1

    # 每次播放的计算具体方法。必须实现。
    def calc_single(self, database):
        adjfactor = database.depend_data['FactorData.Basic_factor.adjfactor']
        close = database.depend_data['FactorData.Basic_factor.close'] * adjfactor
        high = database.depend_data['FactorData.Basic_factor.high'] * adjfactor
        low = database.depend_data['FactorData.Basic_factor.low'] * adjfactor
        ans = ((close - low) - (high - close)) / (high - low)
        ans = ans.diff(periods=self.lag)
        ans = ans.iloc[-1, :]
        ans[ans == 0] = np.nan
        return ans
