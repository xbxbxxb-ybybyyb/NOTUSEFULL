from tquant.stock_data import StockData
from tquant.basic_data import BasicData
from tquant.psfactor import PsFactorData
import pytest
import pandas as pd
import os

class TestPsFactorData(object):
    low_library_name = 'low_' + str(20180808)
    high_library_name = 'high_' + str(20180808)
    low_list = {}
    high_list = {}
    for i in range(1, 5):
        low_list[("low" + str(i))] = 'double'
        high_list[("high" + str(i))] = 'double'

    @classmethod
    def setup_class(cls):
        cls.tps = PsFactorData()
        cls.sd = StockData()
        cls.bd = BasicData()

    @pytest.mark.skip
    def test_get_library_info(self, update_calc_environ):
        """
        测试get_library_info查询所有本用户有读写权限的库名和对应的因子信息
        :return:
        """
        os.environ["scene"] = 'calc'
        library_info = self.tps.get_library_info()
        # assert len(library_info) > 0
        assert isinstance(library_info, dict)

    @pytest.mark.skip
    @pytest.mark.parametrize('library_name, library_type', [(high_library_name, 'T+0'), (low_library_name, 'Alpha')])
    def test_create_factor_library(self, library_name, library_type):
        """
        测试create_factor_library创建指定名称和类型的因子库
        :return:
        """
        try:
            library = self.tps.create_factor_library(library_name, library_type)
            assert library is True
        except Exception as e:
            assert '已存在' in str(e)

    @pytest.mark.skip
    @pytest.mark.parametrize('t_data, expect', [(("a20200506111", "T+01"), '设置错误'),
                                                (("a20200506111", "T+01"), '设置错误'),
                                                (("1a20200506111", "T+0"), '命名不规范'),
                                                (("low_20180808", "T+0"), '已存在'),
                                                (('high_20180808', "T+0"), '已存在')])
    def test_create_factor_library_exe(self, t_data, expect):
        """
        create_factor_library异常测试
        :param t_data: 测试数据
        :param expect: 期望现象
        :return:
        """
        with pytest.raises(Exception) as ex_info:
            self.tps.create_factor_library(*t_data)
        assert expect in str(ex_info.value)

    @pytest.mark.skip
    @pytest.mark.parametrize('library_name, factor_names', [(high_library_name, high_list),
                                                            (high_library_name, {'high': 'string'}),
                                                            (high_library_name, {'OpenPx': 'double', 'ClosePx': 'double',
                                                                                 'HighPx': 'double', 'LowPx': 'double'}),
                                                            (low_library_name, low_list),
                                                            (low_library_name, {'low': 'string'})])
    def test_add_factor(self, library_name, factor_names):
        """
        测试add_factor增加因子
        :return:
        """
        try:
            result = self.tps.add_factor(library_name, factor_names)
            assert result is True
        except Exception as e:
            assert '已存在' in str(e)

    @pytest.mark.skip
    def test_update_factor_value_by_factor(self):
        """
        测试update_factor_value_by_factor更新低频因子值
        :return:
        """
        date_list = self.bd.get_trading_day('20200506', '20200630')
        df2_1 = self.sd.get_factor_price_daily(['300707.SZ', '300726.SZ', '300705.SZ', '601658.SH'], date_list,
                                               ['pre_close'])
        df2_1.index.names = ['MDDate', 'HTSCSecurityID']
        df2_1.rename(columns={'pre_close': 'Value'}, inplace=True)
        # 注：必须包含Value,并将MMDate和HTSCSecurityID作为索引
        result = self.tps.update_factor_value_by_factor(TestPsFactorData.low_library_name,
                                                        df2_1, 'low3', check_olddata=True,
                                                        allow_merge_olddata=True)
        assert result is True

    @pytest.mark.skip
    @pytest.mark.parametrize('check_olddata', [True, False])
    def test_update_factor_value_by_security(self, check_olddata):
        """
        测试update_factor_value_by_stock更新高频因子值
        :return:
        """
        high_df = self.sd.get_stock_tick('688363.SH', '20200506 093000000', '20200515 150000250')
        high_df_tmp = high_df.loc[:, ["MDDate", "MDTime", "OpenPx", "ClosePx", "HighPx", "LowPx"]]
        # 注：必须传入MDDate,MDTime(因子时刻)
        result = self.tps.update_factor_value_by_security(TestPsFactorData.high_library_name,
                                                          high_df_tmp, '688363.SH',
                                                          check_olddata=check_olddata)
        assert result is True

    @pytest.mark.skip
    @pytest.mark.parametrize('in_dataframe', [True, False])
    def test_get_factor_value_low(self, in_dataframe):
        low_df = self.tps.get_factor_value(TestPsFactorData.low_library_name,
                                           ['20200506', '20200509'], factor_list=['low3'],
                                           in_dataframe=in_dataframe)
        if in_dataframe is True:
            assert isinstance(low_df, pd.DataFrame)
        else:
            assert isinstance(low_df, dict)

    @pytest.mark.skip
    def test_get_factor_value_high(self):
        high_df = self.tps.get_factor_value(TestPsFactorData.high_library_name,
                                            ['20200506'], security_list=['688363.SH'])
        assert isinstance(high_df, dict)

    @pytest.mark.skip
    @pytest.mark.parametrize('factor_list', (['OpenPx', 'high2', 'ClosePx', 'HighPx', 'LowPx', 'high1'],
                                             ['OpenPx', 'high2']))
    def test_search_by_stock_date(self, factor_list):
        """
        测试search_by_stock_date ： 按股票、日期查询因子
        :param factor_list:
        :return:
        """
        result = self.tps.search_by_stock_date(TestPsFactorData.high_library_name,
                                               '688363.SH', '20200506', factor_list)
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.skip
    def test_search_by_stock_factor(self):
        result = self.tps.search_by_stock_factor(TestPsFactorData.high_library_name,
                                                 '688363.SH', 'OpenPx',
                                                 ['20200506', '20200822', '20200823'])
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.skip
    def test_search_by_stock(self):
        result = self.tps.search_by_stock(TestPsFactorData.high_library_name,
                                          '688363.SH', ['20200506', '20200822', '20200823'])
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.skip
    def test_search_by_date(self):
        result = self.tps.search_by_date(TestPsFactorData.high_library_name, '20200506',
                                         ['688363.SH', '000001.SZ', '000002.SH'])
        assert isinstance(result, list)
        assert len(result) > 0


if __name__ == "__main__":
    pytest.main(["-v"])


