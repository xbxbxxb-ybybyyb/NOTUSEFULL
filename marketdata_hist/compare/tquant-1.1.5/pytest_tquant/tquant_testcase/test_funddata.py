from tquant.fund_data import FundData
import pytest
import pandas as pd


class TestFundData(object):
    """
    测试基金数据接口FundData
    """
    @classmethod
    def setup_class(cls):
        cls.fd = FundData()

    @pytest.mark.parametrize('symbol', ('518800.SH', '515520.SH'))
    @pytest.mark.parametrize('t_date', (('20200512 090000000', '20200513 200000000'),
                                        ('20200512 090000000', '20200613 200000000')))
    def test_get_fund_tick(self, symbol, t_date):
        """
        测试获取ETF和LOF基金行情Tick数据
        TODO 异常测试需添加
        :param symbol:基金标的代码
        :param t_date:测试时间
        :return:
        """
        result = self.fd.get_fund_tick(symbol, *t_date)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('symbol', ('518800.SH', '515520.SH'))
    @pytest.mark.parametrize('t_date', (('20200402 090000000', '20200503 200000000'),
                                        ('20200512 090000000', '20200613 200000000')))
    @pytest.mark.parametrize('bar_size', ('K_1MIN', 'K_DAY'))
    def test_get_fund_kline(self, symbol, t_date, bar_size):
        """
        测试获取ETF和LOF基金行情K线数据
        TODO 异常测试需添加
        :param symbol:基金标的代码
        :param t_date:测试时间
        :param bar_size:数据周期枚举类
        :return:
        """
        result = self.fd.get_fund_kline(symbol, *t_date, bar_size)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('symbol', ('159968.SZ',))
    @pytest.mark.parametrize('t_date', (('20200312 090000000', '20200313 200000000'),
                                        ('20200330 090000000', '20200413 200000000')))
    def test_get_fund_order(self, symbol, t_date):
        """
        测试 获取ETF和LOF基金行情委托数据
        TODO 异常测试需添加
        :param symbol:基金标的代码
        :param t_date:测试时间
        :return:
        """
        result = self.fd.get_fund_order(symbol, *t_date)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('symbol', ('511660.SH',))
    @pytest.mark.parametrize('t_date', (('20200312 090000000', '20200313 200000000'),
                                        ('20200330 090000000', '20200413 200000000')))
    def test_get_fund_transaction(self, symbol, t_date):
        """
        测试获取ETF和LOF基金行情成交数据
        TODO 异常测试需添加
        :param symbol:基金标的代码
        :param t_date:测试时间
        :return:
        """
        result = self.fd.get_fund_transaction(symbol, *t_date)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('code', ('159901.SZ', '511660.SH'))
    def test_get_fund_issuance_info(self, code):
        """
        测试查询基金的基本信息数据
        TODO 异常测试需添加
        :param code:基金标的代码
        :return:
        """
        result = self.fd.get_fund_issuance_info(code)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('t_data, expect', ((('20200403', 'ETF'), 296), (('20200403', 'LOF'), 247),
                                                (('20200403', 'ALL'), 543)))
    def test_get_fund_set(self, t_data, expect):
        """
        测试查询指定日期的基金代码列表
        TODO 异常测试需添加
        :param t_data:测试数据
        :param expect:基金数量
        :return:
        """
        result = self.fd.get_fund_set(*t_data)
        assert isinstance(result, list)
        assert len(result) == expect


if __name__ == '__main__':
    pytest.main(['-v'])
