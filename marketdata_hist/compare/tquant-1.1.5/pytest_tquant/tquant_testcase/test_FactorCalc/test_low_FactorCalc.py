from tquant.SmartFactor.BaseFactor import Factor
import pytest
import pandas as pd


class BasicDayFactor(Factor):
    """
    参数校验与日频因子测试
    Alpha2
    (-1 * DELTA((((CLOSE - LOW) -  (HIGH - CLOSE)) / (HIGH - LOW)), 1))
    """
    factor_type = "DAY"         # 因子类型 ： 日频(DAY)
    factor_name = 'BasicDayFactor'  # 设置因子名称，因子名称只包含大小写字母，数字或下划线。
    security_type = 'stock'     # 因子适用的证券类型， 股票stock 基金fund（开发中） 债券bond（开发中） 期货future（开发中）
    day_lag = 2  # 需要回溯的日频时间窗口，单位为天，低频因子专用
    quarter_lag = 2  # 需要回溯的季度窗口，单位为季度，若计算需要依赖财务类因子，可通过该参数设置回溯的时间。
    # 财务类因子： BasicFinancialFactor.    日频因子 BasicDayFactor.close,BasicDayFactor.alpha 个人因子：因子库名.因子名
    depend_factor = ["BasicDayFactor.close", "BasicDayFactor.low", "BasicDayFactor.high"]  # 设置依赖因子
    security_pool = "SZA"       # 标的池  str or List 例如：“ALLA”,"SHA","SZA",['000001.SZ','601688.SH']

    # factor_data: dict key: 因子名 value: 因子截面 DataFrame
    def calc(self, factor_data):
        close = factor_data['BasicDayFactor.close']
        low = factor_data['BasicDayFactor.low']
        high = factor_data['BasicDayFactor.high']
        part1 = (2 * close - low - high) / (high - low)
        result = part1.diff(1).iloc[-1] * (-1)
        return result


class Financial(Factor):
    """
    BasicFinancialFactor 财务因子测试
    """
    factor_type = "DAY"         # 因子类型 ： 日频(DAY)
    factor_name = 'Financial'  # 设置因子名称，因子名称只包含大小写字母，数字或下划线。
    security_type = 'stock'     # 因子适用的证券类型， 股票stock 基金fund（开发中） 债券bond（开发中） 期货future（开发中）
    day_lag = 2  # 需要回溯的日频时间窗口，单位为天，低频因子专用
    quarter_lag = 2 # 需要回溯的季度窗口，单位为季度，若计算需要依赖财务类因子，可通过该参数设置回溯的时间。
    #财务类因子： BasicFinancialFactor.    日频因子 BasicDayFactor.close,BasicDayFactor.alpha 个人因子：因子库名.因子名
    depend_factor = ["BasicFinancialFactor.eps_basic", "BasicFinancialFactor.eps_diluted", "BasicFinancialFactor.eps_diluted2"]
    security_pool = ['002314.SZ', '600422.SH', '603369.SH', '601658.SH']       # 标的池  str or List 例如：“ALLA”,"SHA","SZA",['000001.SZ','601688.SH']

    def calc(self, factor_data):
        totalasset_ttm = factor_data["BasicFinancialFactor.eps_basic"]
        yoyeps_diluted = factor_data["BasicFinancialFactor.eps_diluted"]
        yoyocfps = factor_data["BasicFinancialFactor.eps_diluted2"]
        part1 = (totalasset_ttm + yoyeps_diluted + yoyocfps)
        return part1.iloc[-1]


class BasicDay_Financial(Factor):
    """
    BasicFinancialFactor 财务因子测试与日频
    """
    factor_type = "DAY"         # 因子类型 ： 日频(DAY)
    factor_name = 'BasicDay_Financial'  # 设置因子名称，因子名称只包含大小写字母，数字或下划线。
    security_type = 'stock'     # 因子适用的证券类型， 股票stock 基金fund（开发中） 债券bond（开发中） 期货future（开发中）
    day_lag = 2  # 需要回溯的日频时间窗口，单位为天，低频因子专用
    quarter_lag = 2 # 需要回溯的季度窗口，单位为季度，若计算需要依赖财务类因子，可通过该参数设置回溯的时间。
    #财务类因子： BasicFinancialFactor.    日频因子 BasicDayFactor.close,BasicDayFactor.alpha 个人因子：因子库名.因子名
    depend_factor = ["BasicDayFactor.open", "BasicFinancialFactor.eps_diluted", "BasicFinancialFactor.eps_diluted2"]
    security_pool = ['002314.SZ', '600422.SH', '603369.SH', '601658.SH']       # 标的池  str or List 例如：“ALLA”,"SHA","SZA",['000001.SZ','601688.SH']

    def calc(self, factor_data):
        open = factor_data["BasicDayFactor.open"]
        yoyeps_diluted = factor_data["BasicFinancialFactor.eps_diluted"]
        yoyocfps = factor_data["BasicFinancialFactor.eps_diluted2"]
        part1 = (open + yoyeps_diluted + yoyocfps)
        return part1.iloc[-1]


class Person_Factor(Factor):
    """
    个人因子计算与日频因子
    """
    factor_type = "DAY"         # 因子类型 ： 日频(DAY)
    factor_name = 'Person_Factor'  # 设置因子名称，因子名称只包含大小写字母，数字或下划线。
    security_type = 'stock'     # 因子适用的证券类型， 股票stock 基金fund（开发中） 债券bond（开发中） 期货future（开发中）
    day_lag = 2  # 需要回溯的日频时间窗口，单位为天，低频因子专用
    quarter_lag = 2 # 需要回溯的季度窗口，单位为季度，若计算需要依赖财务类因子，可通过该参数设置回溯的时间。
    #财务类因子： BasicFinancialFactor.    日频因子 BasicDayFactor.close,BasicDayFactor.alpha 个人因子：因子库名.因子名
    depend_factor = ["low20180808.low3", "BasicDayFactor.low", "BasicDayFactor.high"]
    security_pool = ['002314.SZ', '600422.SH', '603369.SH', '601658.SH']       # 标的池  str or List 例如：“ALLA”,"SHA","SZA",['000001.SZ','601688.SH']

    def calc(self, factor_data):
        low3 = factor_data["low20180808.low3"]
        low = factor_data['BasicDayFactor.low']
        high = factor_data["BasicDayFactor.high"]
        part1 = (low3 + low + high)
        return part1.iloc[-1]


class Test_low_FactorCalc(object):
    @classmethod
    def setup_class(cls):
        cls.bdf = BasicDayFactor()
        cls.fc = Financial()
        cls.bd_f = BasicDay_Financial()
        cls.pf = Person_Factor()

    @pytest.mark.parametrize('factor_type, expect', (('DAY1', 'factor_type目前仅支持'),
                                                     ('TICK1', 'factor_type目前仅支持'),
                                                     (1, 'factor_type目前仅支持')))
    def test_factor_factor_type_exe(self, factor_type, expect):
        with pytest.raises(Exception) as exe_info:
            self.bdf.factor_type = factor_type
            self.bdf.run_day_factor_value(start_date='20191102', end_date='20191114')
        assert expect in str(exe_info.value)
        self.bdf.factor_type = 'DAY'

    @pytest.mark.parametrize('factor_name, expect', (('%new_marketdata', '不符合格式'),
                                                     ('new_marketdata#', '不符合格式'),
                                                     ('new_marketdata1', '不一致'),
                                                     (1, '字符串格式')))
    def test_factor_factor_name_exe(self, factor_name, expect):
        with pytest.raises(Exception) as exe_info:
            self.bdf.factor_name = factor_name
            self.bdf.run_day_factor_value(start_date='20191102', end_date='20191114')
        assert expect in str(exe_info.value)
        self.bdf.factor_name = 'BasicDayFactor'

    @pytest.mark.parametrize('security_type, expect', (('fund', '目前仅支持stock'), ('stock1', '目前仅支持stock'),
                                                       ('STOCK', '目前仅支持stock')))
    def test_factor_security_type_exe(self, security_type, expect):
        with pytest.raises(Exception) as exe_info:
            self.bdf.security_type = security_type
            self.bdf.run_day_factor_value(start_date='20191102', end_date='20191114')
        assert expect in str(exe_info.value)
        self.bdf.security_type = 'stock'

    @pytest.mark.parametrize('day_lag, expect', ((0, '[1,250]'), (255, '[1,250]'), ('1', '传入一个整数')))
    def test_factor_day_lag_exe(self, day_lag, expect):
        with pytest.raises(Exception) as exe_info:
            self.bdf.day_lag = day_lag
            self.bdf.run_day_factor_value(start_date='20191102', end_date='20191114')
        assert expect in str(exe_info.value)
        self.bdf.day_lag = 2

    @pytest.mark.parametrize('quarter_lag, expect', ((0, '[1,4]'), (5, '[1,4]'), ('1', '传入一个整数')))
    def test_factor_quarter_lag_exe(self, quarter_lag, expect):
        with pytest.raises(Exception) as exe_info:
            self.bdf.quarter_lag = quarter_lag
            self.bdf.run_day_factor_value(start_date='20191102', end_date='20191114')
        assert expect in str(exe_info.value)
        self.bdf.quarter_lag = 3

    @pytest.mark.parametrize('depend_factor, expect', (([], '依赖的因子'),))
    def test_factor_quarter_lag_exe(self, depend_factor, expect):
        with pytest.raises(Exception) as exe_info:
            self.bdf.depend_factor = depend_factor
            self.bdf.run_day_factor_value(start_date='20191102', end_date='20191114')
        assert expect in str(exe_info.value)
        self.bdf.depend_factor = ["BasicDayFactor.close", "BasicDayFactor.low", "BasicDayFactor.high"]

    @pytest.mark.parametrize('security_pool, expect', (("SZA1", '标的池参数'), ([], '股票不能为空'),
                                                       (1, '暂不支持传入该类型的')))
    def test_factor_security_pool_exe(self, security_pool, expect):
        with pytest.raises(Exception) as exe_info:
            self.bdf.security_pool = security_pool
            self.bdf.run_day_factor_value(start_date='20191102', end_date='20191114')
        assert expect in str(exe_info.value)
        self.bdf.security_pool = 'SZA'

    def test_BasicDayFactor(self):
        df = self.bdf.run_day_factor_value(start_date='20191102', end_date='20191114')
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_BasicFinancialFactor(self):
        df = self.fc.run_day_factor_value(start_date='20191008', end_date='20191008')
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_BasicDay_Financial(self):
        df = self.bd_f.run_day_factor_value(start_date='20191008', end_date='20191008')
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_Person_Factor(self):
        df = self.pf.run_day_factor_value(start_date='20200508', end_date='20200509')
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0


if __name__ == '__main__':
    pytest.main(['-v'])
