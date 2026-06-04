from xfactor.BaseFactor import BaseFactor
import numpy as np


# 禁止依赖FactorData、MarketData、h5_io等取数接口。
# 禁止在类中使用multiprocessing等并行化方式，因为在框架层面已经进行了并行化。
# 编写Fix因子子类时，要充分考虑执行效率，若性能太差(如计算某日某个时间点超过2分钟，具体待定)，实盘将不采用。
# 设置lag要合理，需要多少天的数据就设置多少天，不要多取
# 在rolling时，需要采用numpy的方式进行计算，如rolling(5).apply(lambda x:np.nanstd(x, ddof=1))
# 提交的因子代码中，不能包含print或log语句，否则会影响每日因子计算的复盘。

# 类名必须和文件名一致
class SampleDayFactor(BaseFactor):
    factor_type = "DAY"
    depend_data = ["FactorData.Basic_factor.close", "FactorData.Basic_factor.adjfactor"]

    # 计算每个时点的因子所需要前移的数据窗口大小
    # 例如，为日频因子，lag=3表示计算某一日的因子值需要依赖前三个交易日和当日的数据，默认为0，可不设置
    lag = 60
    # 播放后得到的结果，可按照该长度进行rolling等计算，具体rolling方法需要在reform方法中定义。 默认为1，可不设置。
    reform_window = 5

    # 每次播放的计算具体方法。必须实现。
    def calc_single(self, database):
        adj_factor = database.depend_data['FactorData.Basic_factor.adjfactor']
        close = database.depend_data['FactorData.Basic_factor.close'] * adj_factor
        factor_data = close.rolling(self.lag, min_periods=1).apply(np.sum)
        return factor_data.iloc[-1, :]

    # 针对播放后的结果，进行相关的rolling等操作。所用的前序数据长度应为reform_window。默认不修改temp_result， 可不重写。
    def reform(self, temp_result):
        return temp_result.rolling(self.reform_window, min_periods=1).apply(lambda x: np.nanstd(x, ddof=1))
