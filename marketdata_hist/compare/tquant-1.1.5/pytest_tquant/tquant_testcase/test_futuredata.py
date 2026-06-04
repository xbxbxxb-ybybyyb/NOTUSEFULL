from tquant.future_data import FutureData
import pytest
import pandas as pd


class TestFutureData(object):
    """
    测试期货数据接口FutureData
    """
    @classmethod
    def setup_class(cls):
        cls.fd = FutureData()

    @pytest.mark.parametrize('symbol', ('IF', 'TF', 'TF2009.CF'))
    def test_get_instrument_info(self, symbol):
        """
        测试获取合约属性
        :param symbol:期货合约代码
        :return:
        """
        result = self.fd.get_instrument_info(symbol)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize("t_date", ((20190101, 20190108), ('20190101', '20190108')))
    @pytest.mark.parametrize("symbol", ('RB', 'CU'))
    def test_get_instrument_all(self, symbol, t_date):
        """
        测试获取时间区间内的合约
        :param symbol:合约品种符号
        :param t_date:查询时间段
        :return:
        """
        result = self.fd.get_instrument_all(symbol, *t_date)
        assert len(result) > 0
        assert isinstance(result, list)

    @pytest.mark.parametrize("t_date", (("20200209 000000000", "20200221 000000000"),
                                        ("20200209 000000000", "20200222 000000000")))
    @pytest.mark.parametrize('symbol', ('ZN2101.SHF', 'ICZL'))
    def test_get_future_kline(self, symbol, t_date):
        """
        测试获取期货行情K线数据
        :param symbol:合约名称
        :param t_date:查询时间段
        :param bar_size:数据周期枚举类
        :return:
        """
        result = self.fd.get_future_kline(symbol, *t_date)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('t_date', (('20200701 000000000', '20200730 000000000'),))
    @pytest.mark.parametrize('symbol', ('IC2007.CF', 'IC2008.CF', 'IF2007.CF', 'IH2008.CF'))
    def test_get_future_tick(self, symbol, t_date):
        """
        测试获取期货行情Tick数据
        :param symbol:合约名称
        :param t_date:查询时间段
        :return:
        """
        result = self.fd.get_future_tick(symbol, *t_date)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)


if __name__ == "__main__":
    pytest.main(["-v"])
