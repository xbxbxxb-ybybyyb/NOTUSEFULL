from tquant.fund_data import FundData
from MDCDataProvider.utils import mdc_check_no_value
import pytest
import pandas as pd
import os
import configparser


class TestFundData(object):
    """
    测试基金数据接口FundData
    """
    conn = configparser.ConfigParser()
    # 加载现有配置文件
    conn.read(r"/opt/anaconda3/lib/python3.6/site-packages/MDCDataProvider/conf/DXPDataProvider.ini",
              encoding="utf-8-sig")
    file_type = conn.get('task', 'file.type')

    @classmethod
    def setup_class(cls):
        cls.fd = FundData()

    @pytest.mark.parametrize('symbol', ['518800.SH', '515520.SH'])
    @pytest.mark.parametrize('start_time, end_time', [('20200512 090000000', '20200513 200000000'),
                                                      ('20200512 090000000', '20200613 200000000')])
    def test_get_fund_tick(self, symbol, start_time, end_time):
        """
        测试获取ETF和LOF基金行情Tick数据
        TODO 异常测试需添加
        :param symbol:基金标的代码
        :param t_date:测试时间
        :return:
        """
        result = self.fd.get_fund_tick(symbol, start_time, end_time)
        assert isinstance(result, pd.DataFrame)
        if os.environ.get("DSWMAP_envTag") != 'prd':
            assert len(result) == 0
        else:
            assert len(result) > 0

    @pytest.mark.parametrize('symbol', ['159968.SZ','518800.SH'])
    @pytest.mark.parametrize('start_time, end_time', [('20211101 090000000', '20211130 200000000'),
                                                      ('20211201 090000000', '20211213 200000000')])
    def test_get_fund_tick_new_time(self, symbol, start_time, end_time):
        """
        测试获取ETF和LOF基金行情Tick数据(增加了新日期)
        TODO 异常测试需添加
        :param symbol:基金标的代码
        :param t_date:测试时间
        :return:
        """
        result = self.fd.get_fund_tick(symbol, start_time, end_time)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('t_date', [('20211201 093000000', '20211213 200000000')])
    @pytest.mark.parametrize('trading_code', ['159968.SZ','518800.SH'])
    def test_mdc_check_no_value_tick(self, trading_code, t_date):
        new_df = self.fd.get_fund_tick(trading_code, *t_date)

        old_df = self.fd.get_fund_tick(trading_code, *t_date, use_legacy_data=True)
        result = mdc_check_no_value(new_df, old_df)

        assert result == True

    @pytest.mark.parametrize('symbol', ['518800.SH', '515520.SH'])
    @pytest.mark.parametrize('start_time, end_time', [('20200402 090000000', '20200503 200000000'),
                                                      ('20200512 090000000', '20200613 200000000')])
    @pytest.mark.parametrize('bar_size', ['K_1MIN', 'K_5MIN', 'K_10MIN', 'K_60MIN', 'K_DAY'])
    def test_get_fund_kline(self, symbol, start_time, end_time, bar_size):
        """
               测试获取ETF和LOF基金行情K线数据
               TODO 异常测试需添加
               :param symbol:基金标的代码
               :param t_date:测试时间
               :param bar_size:数据周期枚举类
               :return:
               """
        result = self.fd.get_fund_kline(symbol, start_time, end_time, bar_size)
        assert isinstance(result, pd.DataFrame)
        if os.environ.get("DSWMAP_envTag") != 'prd':
            assert len(result) == 0
        else:
            assert len(result) > 0

    @pytest.mark.parametrize('symbol', ['159968.SZ'])
    @pytest.mark.parametrize('t_date', [('20200312 090000000', '20200313 200000000'),
                                        ('20200330 090000000', '20200413 200000000')])
    @pytest.mark.skipif(file_type == 'DXP', reason="DXP没有fundorder表")
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
        if (os.environ.get("DSWMAP_envTag") != 'prd'):
            assert len(result) == 0
        else:
            assert len(result) > 0

    @pytest.mark.parametrize('symbol', ['159968.SZ','518800.SH'])
    @pytest.mark.parametrize('t_date', [('20211101 090000000', '20211130 200000000'),
                                        ('20211201 090000000', '20211213 200000000')])
    #@pytest.mark.skipif(file_type == 'DXP', reason="DXP没有fundorder表")
    def test_get_fund_order_new_time(self, symbol, t_date):
        """
        测试 获取ETF和LOF基金行情委托数据(增加了新日期)
        TODO 异常测试需添加
        :param symbol:基金标的代码
        :param t_date:测试时间
        :return:
        """
        result = self.fd.get_fund_order(symbol, *t_date)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('t_date', [('20211201 093000000', '20211213 200000000')])
    @pytest.mark.parametrize('trading_code', ['159968.SZ','518800.SH'])
    def test_mdc_check_no_value_order(self, trading_code, t_date):
        new_df = self.fd.get_fund_order(trading_code, *t_date)

        old_df = self.fd.get_fund_order(trading_code, *t_date, use_legacy_data=True)
        result = mdc_check_no_value(new_df, old_df)

        assert result == True

    @pytest.mark.parametrize('symbol', ['511660.SH'])
    @pytest.mark.parametrize('start_time, end_time', [('20200312 090000000', '20200313 200000000'),
                                                      ('20200330 090000000', '20200413 200000000')])
    def test_get_fund_transaction(self, symbol, start_time, end_time):
        """
        测试获取ETF和LOF基金行情成交数据
        TODO 异常测试需添加
        :param symbol:基金标的代码
        :param t_date:测试时间
        :return:
        """
        result = self.fd.get_fund_transaction(symbol, start_time, end_time)
        assert isinstance(result, pd.DataFrame)
        if os.environ.get("DSWMAP_envTag") != 'prd':
            assert len(result) == 0
        else:
            assert len(result) > 0

    @pytest.mark.parametrize('symbol', ['159968.SZ','518800.SH'])
    @pytest.mark.parametrize('start_time, end_time', [('20211101 090000000', '20211130 200000000'),
                                                      ('20211201 090000000', '20211213 200000000')])
    def test_get_fund_transaction_new_time(self, symbol, start_time, end_time):
        """
        测试获取ETF和LOF基金行情成交数据(只增加了新日期)
        TODO 异常测试需添加
        :param symbol:基金标的代码
        :param t_date:测试时间
        :return:
        """
        result = self.fd.get_fund_transaction(symbol, start_time, end_time)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('t_date', [('20211201 093000000', '20211213 200000000')])
    @pytest.mark.parametrize('trading_code', ['159968.SZ','518800.SH'])
    def test_mdc_check_no_value_transaction(self, trading_code, t_date):
        new_df = self.fd.get_fund_transaction(trading_code, *t_date)

        old_df = self.fd.get_fund_transaction(trading_code, *t_date, use_legacy_data=True)
        result = mdc_check_no_value(new_df, old_df)

        assert result == True

    @pytest.mark.parametrize('code', ['159901.SZ', '511660.SH'])
    @pytest.mark.skipif(os.environ["DSWMAP_envTag"] == 'prd', reason='生产环境下没有fund_d_marketindex表')
    def test_get_fund_issuance_info(self, code):
        """
        测试查询基金的基本信息数据
        TODO 异常测试需添加
        :param code:基金标的代码
        :return:
        """
        result = self.fd.get_fund_issuance_info(code)
        assert isinstance(result, pd.DataFrame)
        if os.environ.get("DSWMAP_envTag") != 'prd':
            assert len(result) == 0
        else:
            assert len(result) > 0

    @pytest.mark.parametrize('t_data, expect', [(('20200403', 'ETF'), 296), (('20200403', 'LOF'), 247),
                                                (('20200403', 'ALL'), 543)])
    @pytest.mark.skip()
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
