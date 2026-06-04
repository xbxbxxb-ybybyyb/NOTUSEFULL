from tquant.index_data import IndexData
import pytest
import pandas as pd


class TestIndexData(object):
    """
    测试指数数据接口IndexData
    """
    @classmethod
    def setup_class(cls):
        cls.ind = IndexData()

    @pytest.mark.parametrize('use_prev_name', (True, False))
    @pytest.mark.parametrize('weight_type', (0, 1))
    @pytest.mark.parametrize('plate_id', ('HS300', 'ZZ500', 'SH50', '000300.SH',
                                          '000905.SH', '399001.SZ', '000016.SH', '000002.SH'))
    @pytest.mark.parametrize('t_date', ('20191112', '20191213'))
    def test_get_index_info(self, t_date, plate_id, weight_type, use_prev_name):
        """
        测试查询指数板块的成分股及成分股的权重
        :param t_date:测试日期
        :param plate_id:指数代码
        :param weight_type:权重
        :return:
        """
        result = self.ind.get_index_info(t_date, plate_id, weight_type, use_prev_name=use_prev_name)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('symbol', ('000300.SH', '000001.SH'))
    @pytest.mark.parametrize('t_date', (('20200302 093000000', '20200302 150000250'),
                                        ('20190529 093000000', '20191127 150000250')))
    def test_get_index_tick(self, symbol, t_date):
        """
        测试指数Tick查询
        :param symbol:单支股票代码
        :param t_date:测试时间
        :return:
        """
        result = self.ind.get_index_tick(symbol, *t_date)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('symbol', ('000300.SH', '000001.SH'))
    @pytest.mark.parametrize('t_date', (('20200302 093000000', '20200302 150000250'),
                                        ('20190529 093000000', '20191127 150000250')))
    def test_get_index_kline(self, symbol, t_date):
        """
        测试指数K线查询
        :param symbol:单支股票代码
        :param t_date:测试数据时间
        :return:
        """
        result = self.ind.get_index_kline(symbol, *t_date)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0


if __name__ == "__main__":
    pytest.main(["-v"])
