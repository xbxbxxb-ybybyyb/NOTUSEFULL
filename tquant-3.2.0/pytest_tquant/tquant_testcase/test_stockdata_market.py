from tquant.stock_data import StockData
from MDCDataProvider.utils import mdc_check_no_value
import pytest
import pandas as pd
import configparser
import os


class TestStockData(object):
    """
    测试StockData行情数据接口
    """
    conn = configparser.ConfigParser()
    # 加载现有配置文件
    conn.read(r"/opt/anaconda3/lib/python3.6/site-packages/MDCDataProvider/conf/DXPDataProvider.ini",
              encoding="utf-8-sig")
    file_type = conn.get('task', 'file.type')

    @classmethod
    def setup_class(cls):
        cls.sd = StockData()

    @pytest.mark.parametrize('t_date', [('20200701 093000000', '20200730 150000250'),
                                        ('20200701 093000000', '20200806 150000250')])
    @pytest.mark.parametrize('trading_code', ['600833.SH', '300755.SZ'])
    def test_get_stock_transaction(self, trading_code, t_date):
        """
        测试get_stock_transaction 逐笔成交查询
        :param trading_code:股票代码
        :param t_date:时间范围
        :return:
        """
        df = self.sd.get_stock_transaction(trading_code, *t_date)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('t_date', [('20211101 093000000', '20211130 150000250'),
                                        ('20211201 093000000', '20211213 150000250')])
    @pytest.mark.parametrize('trading_code', ['000001.SZ', '603991.SH'])
    def test_get_stock_transaction_new_time(self, trading_code, t_date):
        """
        测试get_stock_transaction 逐笔成交查询(只增加了新日期)
        :param trading_code:股票代码
        :param t_date:时间范围
        :return:
        """
        df = self.sd.get_stock_transaction(trading_code, *t_date)
        assert type(df) == pd.DataFrame
        assert len(df) > 0

    @pytest.mark.parametrize('t_date', [('20211201 093000000', '20211213 200000000')])
    @pytest.mark.parametrize('trading_code', ['000001.SZ', '603991.SH'])
    def test_mdc_check_no_value_transaction(self, trading_code, t_date):
        new_df = self.sd.get_stock_transaction(trading_code, *t_date)

        old_df = self.sd.get_stock_transaction(trading_code, *t_date, use_legacy_data=True)
        result = mdc_check_no_value(new_df, old_df)

        assert result == True

    @pytest.mark.parametrize('stock', ['688001.SH'])
    @pytest.mark.parametrize('t_data', [('20200701 09300000', '20200730 150000250'),
                                        ('20200701 093000000', '20200730 15000025')])
    @pytest.mark.parametrize('expect', ['格式错误'])
    def test_get_stock_transaction_exe(self, stock, t_data, expect):
        """
        异常测试（未包含股票传入未其他类型（list）、None、''）
        :param t_data:测试数据
        :param expect:预期结果
        :return:
        """
        with pytest.raises(Exception) as ex_info:
            self.sd.get_stock_transaction(stock, *t_data)
        assert expect in str(ex_info.value)

    @pytest.mark.parametrize('t_date', [('20200315 093000000', '20200320 150000250'),
                                        ('20190715 093000000', '20190720 150000250')])
    @pytest.mark.parametrize('trading_code', ['000008.SZ', '000001.SZ'])
    @pytest.mark.skipif(file_type == 'DXP', reason='DFS条件下测试')
    def test_get_stock_order(self, trading_code, t_date):
        """
        测试get_stock_order 逐笔委托查询
        :param trading_code:股票代码
        :param t_date:时间范围
        :return:
        """
        df = self.sd.get_stock_order(trading_code, *t_date)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert type(df) == pd.DataFrame
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('t_date', [('20211101 093000000', '20211110 150000250'),
                                        ('20211201 093000000', '20211213 150000250')])
    @pytest.mark.parametrize('trading_code', ['000001.SZ', '603991.SH'])
    @pytest.mark.skipif(file_type == 'DXP', reason='DFS条件下测试')
    def test_get_stock_order_new_time(self, trading_code, t_date):
        """
        测试get_stock_order 逐笔委托查询(只增加了新日期)
        :param trading_code:股票代码
        :param t_date:时间范围
        :return:
        """
        df = self.sd.get_stock_order(trading_code, *t_date)
        assert type(df) == pd.DataFrame
        assert len(df) > 0

    @pytest.mark.parametrize('t_date', [('20211201 093000000', '20211213 200000000')])
    @pytest.mark.parametrize('trading_code', ['000001.SZ'])
    def test_mdc_check_no_value_order(self, trading_code, t_date):
        new_df = self.sd.get_stock_order(trading_code, *t_date)

        old_df = self.sd.get_stock_order(trading_code, *t_date, use_legacy_data=True)
        result = mdc_check_no_value(new_df, old_df)

        assert result == True

    @pytest.mark.parametrize('stock', ['000001.SH'])
    @pytest.mark.parametrize('t_data', [('20200701 09300000', '20200730 150000250'),
                                        ('20200701 093000000', '20200730 15000025')])
    @pytest.mark.parametrize('expect', ['格式错误'])
    def test_get_stock_order_exe(self, stock, t_data, expect):
        """
        异常测试（未包含股票传入未其他类型（list）、None、''）
        :param t_data:测试数据
        :param expect:预期结果
        :return:
        """
        with pytest.raises(Exception) as ex_info:
            self.sd.get_stock_order(stock, *t_data)
        assert expect in str(ex_info.value)

    @pytest.mark.parametrize('t_date', [('20191101 093000000', '20191215 150000250'),
                                        ('20191101 093000000', '20191130 150000250')])
    @pytest.mark.parametrize('trading_code', ['000004.SZ', '000001.SZ'])
    @pytest.mark.parametrize('k_type', ['Kline1M4ZT', 'Kline5M4ZT', 'Kline10M4ZT', 'Kline60M4ZT'])
    def test_get_stock_kline(self, trading_code, t_date, k_type):
        """
        测试get_stock_kline 股票K线查询
        :param trading_code:股票代码
        :param t_date:时间范围
        :return:
        """
        df = self.sd.get_stock_kline(trading_code, *t_date, k_type)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('stock', ['000001.SZ'])
    @pytest.mark.parametrize('t_data', [('20200701 09300000', '20200730 150000250'),
                                        ('20200701 093000000', '20200730 15000025')])
    @pytest.mark.parametrize('expect', ['格式错误'])
    def test_get_stock_kline_exe(self, stock, t_data, expect):
        """
        异常测试（未包含股票传入未其他类型（list）、None、''）
        :param t_data:测试数据
        :param expect:预期结果
        :return:
        """
        with pytest.raises(Exception) as ex_info:
            self.sd.get_stock_kline(stock, *t_data)
        assert expect in str(ex_info.value)

    @pytest.mark.parametrize('t_date', [('20200201 093000000', '20200318 150000250', ['0']),
                                        ('20200201 093000000', '20200228 150000250', ['0', '1'])])
    @pytest.mark.parametrize('trading_code', ['000429.SZ', '000544.SZ'])
    def test_get_stock_tick(self, trading_code, t_date):
        """
        测试get_stock_tick 股票Tick查询
        :param trading_code: 股票代码
        :param t_date: 时间范围
        :return:
        """
        df = self.sd.get_stock_tick(trading_code, *t_date)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('t_date', [('20211101 093000000', '20211130 150000250', ['0']),
                                        ('20211201 093000000', '20211213 150000250', ['0', '1'])])
    @pytest.mark.parametrize('trading_code', ['000001.SZ', '603991.SH'])
    def test_get_stock_tick_new_time(self, trading_code, t_date):
        """
        测试get_stock_tick 股票Tick查询(只增加了新日期)
        :param trading_code: 股票代码
        :param t_date: 时间范围
        :return:
        """
        df = self.sd.get_stock_tick(trading_code, *t_date)
        assert type(df) == pd.DataFrame
        assert len(df) > 0

    @pytest.mark.parametrize('t_date', [('20211201 093000000', '20211213 200000000')])
    @pytest.mark.parametrize('trading_code', ['000001.SZ', '603991.SH'])
    def test_mdc_check_no_value_tick(self, trading_code, t_date):
        new_df = self.sd.get_stock_tick(trading_code, *t_date)

        old_df = self.sd.get_stock_tick(trading_code, *t_date, use_legacy_data=True)
        result = mdc_check_no_value(new_df, old_df)

        assert result == True

    @pytest.mark.parametrize('stock', ['000001.SZ'])
    @pytest.mark.parametrize('t_data', [('20200701 09300000', '20200730 150000250'),
                                        ('20200701 093000000', '20200730 15000025')])
    @pytest.mark.parametrize('expect', ['格式错误'])
    def test_get_stock_tick_exe(self, stock, t_data, expect):
        """
        异常测试（未包含股票传入未其他类型（list）、None、'',tuple）
        :param t_data:测试数据
        :param expect:预期结果
        :return:
        """
        with pytest.raises(Exception) as ex_info:
            self.sd.get_stock_tick(stock, *t_data)
        assert expect in str(ex_info.value)



if __name__ == "__main__":
    pytest.main(["-v"])
