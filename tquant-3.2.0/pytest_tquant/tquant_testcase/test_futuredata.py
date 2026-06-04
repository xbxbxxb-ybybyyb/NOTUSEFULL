from tquant.future_data import FutureData
import pytest
import pandas as pd
import os

class TestFutureData(object):
    """
    测试期货数据接口FutureData
    """
    @classmethod
    def setup_class(cls):
        cls.fd = FutureData()

    @pytest.mark.parametrize('symbol', ['TF2009.CF'])
    def test_get_instrument_info(self, symbol):
        """
        测试获取合约属性
        :param symbol:期货合约代码
        :return:
        """
        result = self.fd.get_instrument_info(symbol)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('start_date, end_date', [(20190101, 20190108), ('20190101', '20190108')])
    @pytest.mark.parametrize('symbol', ['all','ALL','RB', 'CU'])
    def test_get_instrument_all(self, symbol, start_date, end_date):
        """
        测试获取时间区间内的合约
        :param symbol:合约品种符号
        :param t_date:查询时间段
        :return:
        """
        result = self.fd.get_instrument_all(symbol, start_date, end_date)
        assert len(result) > 0
        if symbol in ['ALL','all']:
            assert isinstance(result, dict)

        else:
            assert isinstance(result, list)

    @pytest.mark.parametrize('test_data', [('IF2008.CF', '20200701 000000000', '20200730 000000000'),
                                           ('ICZL', '20211101 000000000', '20211130 000000000'),
                                           ('ZN2211.SHF', '20211201 000000000', '20211220 000000000')])
    @pytest.mark.parametrize('k_type', ['K_1MIN', 'K_5MIN', 'K_10MIN', 'K_60MIN'])
    def test_get_future_kline(self, test_data, k_type):
        """
        测试获取期货行情K线数据
        :param symbol:合约名称
        :param t_date:查询时间段
        :param bar_size:数据周期枚举类
        :return:
        """
        result = self.fd.get_future_kline(*test_data, k_type)
        assert type(result) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(result) == 0
        else:
            assert len(result) > 0

    @pytest.mark.parametrize('test_data', [('IH2008.CF', '20200701 000000000', '20200730 000000000'),
                                           ('IC00.CF', '20211101 000000000', '20211130 000000000'),
                                           ('ZN2211.SHF', '20211201 000000000', '20211220 000000000')])
    def test_get_future_tick(self, test_data):
        """
        测试获取期货行情Tick数据
        :param symbol:合约名称
        :param t_date:查询时间段
        :return:
        """
        result = self.fd.get_future_tick(*test_data)
        assert type(result) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(result) == 0
        else:
            assert len(result) > 0



if __name__ == '__main__':
    pytest.main(['-v'])
