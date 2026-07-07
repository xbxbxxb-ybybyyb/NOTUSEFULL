from xfactor.BaseFactor import BaseFactor
import xfactor.Util as Util
import numpy as np


class SampleMinuteFactor(BaseFactor):
    #  定义因子参数

    # 因子频率，默认为日频因子， 可不设置
    factor_type = "FIX"
    fix_times = ["1000", "1030"]
    # 依赖的平台原始数据，包括FactorData和MarketData接口中的数据。 默认为空，必须设置
    depend_data = ["FactorData.Basic_factor.volume_minute", "FactorData.Basic_factor.close_minute"]
    # 计算每个时点的因子所需要前移的数据窗口大小
    # 例如，为日频因子，lag=3表示计算某一日的因子值需要依赖前三个交易日和当日的数据，默认为0，可不设置
    lag = 0

    # 每次播放的计算具体方法。必须实现。
    def calc_single(self, database):
        volume = database.depend_data['FactorData.Basic_factor.volume_minute']
        close = database.depend_data['FactorData.Basic_factor.close_minute']
        ans = Util.array_coef(volume, close)
        ans[ans == 0.] = np.nan
        return ans
