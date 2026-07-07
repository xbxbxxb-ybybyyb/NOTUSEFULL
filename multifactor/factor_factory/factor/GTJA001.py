from xfactor.BaseFactor import BaseFactor
import xfactor.Util as Util
import numpy as np
import pandas as pd


class GTJA001(BaseFactor):
    #  定义因子参数

    # 因子频率，。默认为日频因子， 可不设置
    factor_type = "DAY"
    # 依赖的平台原始数据，包括FactorData和MarketData接口中的数据。 默认为空，必须设置
    depend_data = ["FactorData.Basic_factor.open", "FactorData.Basic_factor.close", "FactorData.Basic_factor.volume",
                   "FactorData.Basic_factor.adjfactor"]
    # 计算每个时点的因子所需要前移的数据窗口大小
    # 例如，为日频因子，lag=3表示计算某一日的因子值需要依赖前三个交易日和当日的数据，默认为0，可不设置
    lag = 6

    # 每次播放的计算具体方法。必须实现。
    def calc_single(self, database):
        adjfactor = database.depend_data['FactorData.Basic_factor.adjfactor']
        volume = database.depend_data['FactorData.Basic_factor.volume'] / adjfactor
        open_df = database.depend_data['FactorData.Basic_factor.open'] * adjfactor
        close = database.depend_data['FactorData.Basic_factor.close'] * adjfactor
        volume_pct_rank = ((volume - volume.shift(1)) / volume.shift(1)).rank(axis=1, pct=True)
        price_pct_rank = ((close - open_df) / open_df).rank(axis=1, pct=True)
        ans = Util.arraycoef(volume_pct_rank.iloc[-self.lag:], price_pct_rank.iloc[-self.lag:])
        ans[ans == 0] = np.nan
        return ans
