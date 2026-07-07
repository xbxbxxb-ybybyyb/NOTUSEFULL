from xfactor.BaseFactor import BaseFactor
import numpy as np


class GTJA009(BaseFactor):
    #  定义因子参数

    # 因子频率，。默认为日频因子， 可不设置
    factor_type = "DAY"
    # 依赖的平台原始数据，包括FactorData和MarketData接口中的数据。 默认为空，必须设置
    depend_data = ["FactorData.Basic_factor.high", "FactorData.Basic_factor.low", "FactorData.Basic_factor.volume","FactorData.Basic_factor.adjfactor"]
    # 计算每个时点的因子所需要前移的数据窗口大小
    # 例如，为日频因子，lag=3表示计算某一日的因子值需要依赖前三个交易日和当日的数据，默认为0，可不设置
    lag = 7

    # 每次播放的计算具体方法。必须实现。
    def calc_single(self, database):
        adjfactor = database.depend_data['FactorData.Basic_factor.adjfactor']
        high = database.depend_data['FactorData.Basic_factor.high'] * adjfactor
        low = database.depend_data['FactorData.Basic_factor.low'] * adjfactor
        volume = database.depend_data['FactorData.Basic_factor.volume'] / adjfactor
        part1 = ((high+low)*0.5-(high.shift(1)+low.shift(1))*0.5)*(high-low)/(high+low)*0.5
        part1 = np.minimum(np.maximum(part1, -0.05), 0.05)
        part2 = volume.rank(axis=1,pct=True)
        ans = (part1 * part2).ewm(alpha=2.0/self.lag).mean()
        ans = ans.iloc[-1, :]
        ans[ans == 0] = np.nan
        return ans
