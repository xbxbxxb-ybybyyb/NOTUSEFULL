from tquant.stock_data import StockData
import pytest
import pandas as pd


class TestStockData(object):
    """
    测试StockData行情数据接口
    """
    @classmethod
    def setup_class(cls):
        cls.sd = StockData()

    @pytest.mark.parametrize('t_date', (('20200701 093000000', '20200730 150000250'),
                                        ('20200701 093000000', '20200806 150000250')))
    @pytest.mark.parametrize('trading_code', ('688001.SH', '688599.SH'))
    def test_get_stock_transaction(self, trading_code, t_date):
        """
        测试get_stock_transaction 逐笔成交查询
        :param trading_code:股票代码
        :param t_date:时间范围
        :return:
        """
        df = self.sd.get_stock_transaction(trading_code, *t_date)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert len(df.columns) == 27 and 'MDRecordID' in df.columns and 'MDValidType' in df.columns

    @pytest.mark.parametrize('t_data, expect', ((('688001.SH', '20200701 09300000', '20200730 150000250'), '格式错误'),
                                                (('688001.SH', '20200701 093000000', '20200730 15000025'), '格式错误')))
    def test_get_stock_transaction_exe(self, t_data, expect):
        """
        异常测试（未包含股票传入未其他类型（list）、None、''）
        :param t_data:测试数据
        :param expect:预期结果
        :return:
        """
        with pytest.raises(Exception) as ex_info:
            self.sd.get_stock_transaction(*t_data)
        assert expect in str(ex_info.value)

    @pytest.mark.parametrize('t_date', (('20200301 093000000', '20200330 150000250'),
                                        ('20200301 093000000', '20200406 150000250')))
    @pytest.mark.parametrize('trading_code', ('000008.SZ', '000001.SZ'))
    def test_get_stock_order(self, trading_code, t_date):
        """
        测试get_stock_order 逐笔委托查询
        :param trading_code:股票代码
        :param t_date:时间范围
        :return:
        """
        df = self.sd.get_stock_order(trading_code, *t_date)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert len(df.columns) == 28 and 'MDRecordID' in df.columns and 'ConfirmID' in df.columns

    @pytest.mark.parametrize('t_data, expect', ((('000001.SZ', '20200701 09300000', '20200730 150000250'), '格式错误'),
                                                (('000001.SZ', '20200701 093000000', '20200730 15000025'), '格式错误')))
    def test_get_stock_order_exe(self, t_data, expect):
        """
        异常测试（未包含股票传入未其他类型（list）、None、''）
        :param t_data:测试数据
        :param expect:预期结果
        :return:
        """
        with pytest.raises(Exception) as ex_info:
            self.sd.get_stock_order(*t_data)
        assert expect in str(ex_info.value)

    @pytest.mark.parametrize('t_date', (('20191101 093000000', '20191215 150000250'),
                                        ('20191101 093000000', '20191130 150000250')))
    @pytest.mark.parametrize('trading_code', ('000001.SH', '000001.SZ'))
    def test_get_stock_kline(self, trading_code, t_date):
        """
        测试get_stock_kline 股票K线查询
        :param trading_code:股票代码
        :param t_date:时间范围
        :return:
        """
        df = self.sd.get_stock_kline(trading_code, *t_date)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert len(df.columns) == 17 and 'MDRecordID' in df.columns and 'SettlePrice' in df.columns

    @pytest.mark.parametrize('t_data, expect', ((('000001.SZ', '20200701 09300000', '20200730 150000250'), '格式错误'),
                                                (('000001.SZ', '20200701 093000000', '20200730 15000025'), '格式错误')))
    def test_get_stock_kline_exe(self, t_data, expect):
        """
        异常测试（未包含股票传入未其他类型（list）、None、''）
        :param t_data:测试数据
        :param expect:预期结果
        :return:
        """
        with pytest.raises(Exception) as ex_info:
            self.sd.get_stock_kline(*t_data)
        assert expect in str(ex_info.value)

    @pytest.mark.parametrize('t_date', (('20200201 093000000', '20200318 150000250', [0]),
                                        ('20200201 093000000', '20200228 150000250', [0, 1])))
    @pytest.mark.parametrize('trading_code', ('000429.SZ', '000544.SZ'))
    def test_get_stock_tick(self, trading_code, t_date):
        """
        测试get_stock_tick 股票Tick查询
        :param trading_code: 股票代码
        :param t_date: 时间范围
        :return:
        """
        df = self.sd.get_stock_tick(trading_code, *t_date)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert len(df.columns) == 119 and 'MDRecordID' in df.columns and 'MDValidType' in df.columns

    @pytest.mark.parametrize('t_data, expect', ((('000001.SZ', '20200701 09300000', '20200730 150000250'), '格式错误'),
                                                (('000001.SZ', '20200701 093000000', '20200730 15000025'), '格式错误')))
    def test_get_stock_tick_exe(self, t_data, expect):
        """
        异常测试（未包含股票传入未其他类型（list）、None、'',tuple）
        :param t_data:测试数据
        :param expect:预期结果
        :return:
        """
        with pytest.raises(Exception) as ex_info:
            self.sd.get_stock_tick(*t_data)
        assert expect in str(ex_info.value)


if __name__ == "__main__":
    pytest.main(["-v"])
