from xfactor.BaseFactor import BaseFactor
import numpy as np


class GTJA005(BaseFactor):
    #  定义因子参数

    # 因子频率，。默认为日频因子， 可不设置
    factor_type = "DAY"
    # 依赖的平台原始数据，包括FactorData和MarketData接口中的数据。 默认为空，必须设置
    depend_data = ["FactorData.Basic_factor.high", "FactorData.Basic_factor.volume", "FactorData.Basic_factor.adjfactor"]
    # 计算每个时点的因子所需要前移的数据窗口大小
    # 例如，为日频因子，lag=3表示计算某一日的因子值需要依赖前三个交易日和当日的数据，默认为0，可不设置
    lag = 5

    # 每次播放的计算具体方法。必须实现。
    def calc_single(self, database):
        adjfactor = database.depend_data['FactorData.Basic_factor.adjfactor']
        high = database.depend_data['FactorData.Basic_factor.high'] * adjfactor
        volume = database.depend_data['FactorData.Basic_factor.volume'] / adjfactor
        volume_rank = volume.rolling(self.lag,min_periods=1).apply(self.tsrank)
        high_rank = high.rolling(self.lag,min_periods=1).apply(self.tsrank)
        corr = high_rank.rolling(self.lag,min_periods=1).corr(volume_rank)
        corr[corr>1] = np.nan
        corr[corr<-1] = np.nan
        ans = -corr.max()
        ans[ans == 0] = np.nan
        return ans

    def tsrank(self, seq):
        length = len(seq)
        order = 1
        for i in seq:
            if i > seq[-1]:
                order += 1
        return order/length