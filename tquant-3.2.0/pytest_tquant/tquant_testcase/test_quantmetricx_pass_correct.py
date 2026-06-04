import numpy as np, pandas as pd
from datetime import datetime as dt
from tquant.strategy.day_factor_backtest_new.QuantMetricx import *
import pytest
import os


class TestQuantMetricx(object):

    @classmethod
    def setup_class(cls):
        cls.file_path = ['/app/mount/code/zyy/quantmetricx_test_datas']
        cls.file_path_total = cls.file_path + ['nw_total_share_pct.pkl']
        cls.file_path_total = '/'.join(cls.file_path_total)
        cls.file_path_res = ['/app/mount/code/zyy/quantmetricx_test_res_datas']
        cls.factor_data = pd.read_pickle(cls.file_path_total)  # 北向资金原始数据pickle文件路径
        cls.factor_data.index.names = ['mddate', 'stock']
        # factor_data.reset_index(inplace=True)
        # factor_data['mddate'] = factor_data['mddate'].apply(pd.Timestamp)
        # factor_data.set_index(['mddate', 'stock'], inplace=True)
        cls.factor_data = cls.factor_data['NW_total_share_pct'].unstack()
        cls.factor_data = cls.factor_data.sort_index()
        cls.factor_data = cls.factor_data.loc['20190102':'20190331', :]

    @pytest.mark.parametrize('price_use', ['close', 'open', 'vwap'])
    @pytest.mark.parametrize('universe', ['alpha_universe', 'hs300', 'sz50'])
    @pytest.mark.parametrize('holding_period', [1, 5, 10])
    @pytest.mark.parametrize('ret_shift', [True, False])
    @pytest.mark.parametrize('ic_type', ['original', 'score_weighted'])
    def test_factor_ic_calc(self, price_use, universe, holding_period, ret_shift, ic_type):
        """
            测试factor_ic_calc计算因子IC值
            :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
            :param price_use: 计算收益率因子，默认用收盘价，可改成open、vwap
            :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
            :param holding_period: 持有期（int）
            :param ret_shift: 如果是True，收益率计算周期为 T+2/T+1，如果是False，收益率计算周期为 T+1/T+0
            :param ic_type: 如果是original，因子值等权，如果是score_weighted，按因子值排名加权。默认original
            :param min_pct: 因子值有效标的数量最低比例
            :return: 因子IC值
            """
        res_pass = factor_ic_calc(self.factor_data, price_use, universe, holding_period, ret_shift, ic_type)
        assert len(res_pass) > 0

    @pytest.mark.parametrize('price_use', ['close', 'open', 'vwap'])
    @pytest.mark.parametrize('universe', ['alpha_universe', 'hs300', 'sz50'])
    @pytest.mark.parametrize('holding_period', [1, 5, 10])
    @pytest.mark.parametrize('ret_shift', [True, False])
    @pytest.mark.parametrize('ic_type', ['original', 'score_weighted'])
    def test_factor_ic_by_industry_calc(self, price_use, universe, holding_period, ret_shift, ic_type):
        """
            测试factor_ic_by_industry_calc分行业计算因子IC
            :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
            :param price_use: 计算收益率因子，默认用收盘价，可改成open、vwap
            :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
            :param holding_period: 持有期（int）
            :param ret_shift: 如果是True，收益率计算周期为 T+2/T+1，如果是False，收益率计算周期为 T+1/T+0
            :param ic_type: 如果是original，因子值等权，如果是score_weighted，按因子值排名加权。默认original
            :return:
            """
        res_pass = factor_ic_by_industry_calc(factor_data=self.factor_data, price_use=price_use, universe=universe,
                                              holding_period=holding_period, ret_shift=ret_shift, ic_type=ic_type)
        assert len(res_pass) > 0

    @pytest.mark.parametrize('price_use', ['close', 'open', 'vwap'])
    @pytest.mark.parametrize('universe', ['alpha_universe', 'hs300', 'sz50'])
    @pytest.mark.parametrize('ic_type', ['original', 'score_weighted'])
    @pytest.mark.parametrize('ret_shift', [True, False])
    def test_factor_ic_duration_calc(self, price_use, universe, ic_type, ret_shift):
        """
            测试factor_ic_duration_calc因子IC随时间持续性
            :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
            :param price_use: 计算收益率因子，默认用收盘价，可改成open、vwap
            :param ic_type: 如果是original，因子值等权，如果是score_weighted，按因子值排名加权。默认original
            :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
            :return: 因子IC随时间的持续性
            """

        res_pass = factor_ic_duration_calc(factor_data=self.factor_data, price_use=price_use,
                                           universe=universe, ic_type=ic_type, ret_shift=ret_shift)
        assert len(res_pass) > 0


    @pytest.mark.parametrize('price_use', ['close', 'open', 'vwap'])
    @pytest.mark.parametrize('universe', ['alpha_universe', 'hs300', 'sz50'])
    @pytest.mark.parametrize('max_lag', [3, 5, 8])
    @pytest.mark.parametrize('holding_period', [1, 5, 10])
    @pytest.mark.parametrize('ic_type', ['original', 'score_weighted'])
    @pytest.mark.parametrize('ret_shift', [True, False])
    def test_factor_alpha_decay_calc(self, price_use, universe, max_lag, holding_period, ic_type, ret_shift):
        """
            测试factor_alpha_decay_calc因子IC随时间的衰减
            :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
            :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
            :param price_use: 计算收益率因子，默认用收盘价，可改成open、vwap
            :param max_lag: 因子值与收益率之间相差的最大周期(int)
            :param holding_period: 持有期（int）
            :param ic_type: 如果是original，因子值等权，如果是score_weighted，按因子值排名加权。默认original
            :param ret_shift: 如果是True，收益率计算周期为 T+2/T+1，如果是False，收益率计算周期为 T+1/T+0
            :return: 因子IC随时间的衰减
            """

        res_pass = factor_alpha_decay_calc(factor_data=self.factor_data, price_use=price_use, universe=universe,
                                           max_lag=max_lag, holding_period=holding_period, ic_type=ic_type,
                                           ret_shift=ret_shift)
        assert len(res_pass) > 0


    @pytest.mark.parametrize('price_use', ['close', 'open', 'vwap'])
    @pytest.mark.parametrize('holding_period', [1, 5, 10])
    @pytest.mark.parametrize('ret_shift', [True, False])
    @pytest.mark.parametrize('universe', ['alpha_universe', 'hs300', 'sz50'])
    def test_factor_regression_analysis(self, price_use, holding_period, ret_shift, universe):
        """
         测试factor_regression_analysis因子回归分析
         原接口regression_analysis，原接口中没有被调用，输出excel里没数据
            :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
            :param price_use: 计算收益率因子，默认用收盘价，可改成open、vwap
            :param holding_period: 持有期（int）
            :param ret_shift: 如果是True，收益率计算周期为 T+2/T+1，如果是False，收益率计算周期为 T+1/T+0
            :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
            :param params_of_regressor: 默认['Industry', 'Size']，目前仅支持按照行业数据和市值因子数据做回归分析
            :return:
            """

        res_pass = factor_regression_analysis(factor_data=self.factor_data, price_use=price_use,
                                              holding_period=holding_period,
                                              ret_shift=ret_shift, universe=universe)
        assert len(res_pass) > 0

    @pytest.mark.parametrize('universe', ['alpha_universe', 'hs300', 'sz50'])
    def test_factor_neutralization_calc(self, universe):
        """
        测试factor_neutralization_calc中性化因子值
        输出excel里没有该数据
        :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
        :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
        :param params_of_regressor: 因子中性化使用的回归参数，通常为 市值因子 或 行业因子 默认为['Industry','Size']
        :return: 中性化因子值
        """
        res_pass = factor_neutralization_calc(factor_data=self.factor_data, universe=universe)
        assert len(res_pass) > 0

    @pytest.mark.parametrize('universe', ['alpha_universe', 'hs300', 'sz50'])
    @pytest.mark.parametrize('fillna', [False, True])
    @pytest.mark.parametrize('median', [False, True])
    @pytest.mark.parametrize('standard', [False, True])
    def test_factor_standard_process_calc(self, universe, fillna, median, standard):
        """
         测试factor_standard_process_calc因子数据预处理
         输出excel里没有该数据
        :param industry_type: 行业类型
        :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
        :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
        :param fillna: 是否按照行业中位数进行nan值填充
        :param median: 是否采用3sigema的方式去极值
        :param standard: 是否对数据进行标准化处理
        :return: 对原始因子数据进行预处理
        """
        res_pass = factor_standard_process_calc(factor_data=self.factor_data, universe=universe, fillna=fillna,
                                                median=median, standard=standard)
        assert len(res_pass) > 0

    @pytest.mark.parametrize('universe', ['alpha_universe', 'hs300'])
    @pytest.mark.parametrize('benchmark', ['alpha_universe', 'hs300'])
    @pytest.mark.parametrize('transaction_cost', [0, 0.0013])
    @pytest.mark.parametrize('by_industry', [False, True])
    @pytest.mark.parametrize('price_use', ['close', 'open', 'vwap'])
    @pytest.mark.parametrize('holding_period', [1, 5, 10])
    def test_factor_segment_test(self, price_use, holding_period, universe, benchmark, transaction_cost, by_industry):
        """
         测试factor_segment_test因子分层测试收益
        :param factor_pd: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
        :param price_use: 计算收益率因子，默认用收盘价，可改成open、vwap
        :param holding_period: 持有期（int）
        :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
        :param benchmark: 基准，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
        :param segment_num: 分层测试所分层数，int类型
        :param handle_insufficient: 数据是否不足，bool类型
        :param handle_return_outlier: 是否采用Winsorize变换，bool类型
        :param return_bucket_ic: 是否返回分层平均收益与分层因子均值的IC值，bool类型
        :param return_industry: 是否返回行业，bool类型
        :param transaction_cost: float类型，手续费+滑点+契税，取值范围：无：0，万三佣金+千分之一印花税+无滑点：0.0013，万三佣金+千分之一印花税+千分之一滑点：0.0023，默认0.0013
        :param max_quantile: 平均收益最佳的分组
        :param by_industry: bool类型，分层测试中性化，默认False
        :param industry_type: 因子行业中性化，str类型，中信行业：CITIC_I，暂时只支持中信行业
        :return: 因子分层测试收益
        """

        res_pass = factor_segment_test(factor_pd=self.factor_data, price_use=price_use, holding_period=holding_period,
                                       universe=universe, benchmark=benchmark,
                                       transaction_cost=transaction_cost, by_industry=by_industry)
        assert len(res_pass) > 0

    @pytest.mark.parametrize('price_use', ['close', 'open', 'vwap'])
    @pytest.mark.parametrize('holding_period', [1, 5, 10])
    @pytest.mark.parametrize('universe', ['alpha_universe', 'hs300', 'sz50'])
    @pytest.mark.parametrize('benchmark', ['alpha_universe', 'hs300', 'sz50'])
    @pytest.mark.parametrize('transaction_cost', [0, 0.0013])
    @pytest.mark.parametrize('by_industry', [False, True])
    @pytest.mark.parametrize('interest_type', ['SAMPLE', 'cumprod'])
    def test_factor_segment_performance_measure(self, price_use, holding_period, universe,
                                                benchmark, transaction_cost, by_industry, interest_type):
        """
        测试factor_segment_performance_measure投资组合利差统计
        :param factor_pd: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
        :param price_use: 计算收益率因子，默认用收盘价，可改成open、vwap
        :param holding_period: 持有期（int）
        :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
        :param benchmark: 基准，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
        :param segment_num: int类型，分层数，默认10层
        :param handle_insufficient: 数据是否不足，bool类型
        :param handle_return_outlier: 是否采用Winsorize变换，bool类型
        :param return_industry: 是否返回行业，bool类型
        :param transaction_cost: float类型，手续费+滑点+契税，取值范围：无：0，万三佣金+千分之一印花税+无滑点：0.0013，万三佣金+千分之一印花税+千分之一滑点：0.0023，默认0.0013
        :param max_quantile: 平均收益最佳的分组
        :param by_industry: bool类型，分层测试中性化，默认False
        :param industry_type: 因子行业中性化，str类型，中信行业：CITIC_I，暂时只支持中信行业
        :param interest_type: SIMPLE或cumprod.默认为cumprod，cumprod模式下，计算收益的方式为累乘， SIMPLE模式下，计算收益的方式为累加
        :return:
        """
        res_pass = factor_segment_performance_measure(factor_pd=self.factor_data, price_use=price_use,
                                                      holding_period=holding_period, universe=universe,
                                                      benchmark=benchmark, transaction_cost=transaction_cost,
                                                      by_industry=by_industry, interest_type=interest_type)
        assert len(res_pass) > 0

    @pytest.mark.parametrize('universe', ['alpha_universe', 'hs300', 'sz50'])
    @pytest.mark.parametrize('seg_benchmark', ['alpha_universe', 'hs300', 'sz50'])
    def test_factor_distribution_calc(self, universe, seg_benchmark):
        """
         测试factor_distribution_calc因子值分布统计息
        :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
        :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
        :param seg_benchmark: 分层基准，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
        :return: 因子值分布统计息
        """
        res_pass = factor_distribution_calc(factor_data=self.factor_data, universe=universe,
                                            seg_benchmark=seg_benchmark)
        assert len(res_pass) > 0


if __name__ == '__main__':
    pytest.main(['-v'])
