from tquant.bond_data import BondData
from tquant.fund_data import FundData
from tquant.future_data import FutureData
from tquant.index_data import IndexData
from tquant.option_data import OptionData
from tquant.stock_data import StockData

import pytest
import pandas as pd
import configparser
import os


class TestDataDay(object):
    """
    测试全市场行情数据接口
    """
    conn = configparser.ConfigParser()
    # 加载现有配置文件
    conn.read(r"/opt/anaconda3/lib/python3.6/site-packages/MDCDataProvider/conf/DXPDataProvider.ini",
              encoding="utf-8-sig")
    file_type = conn.get('task', 'file.type')

    @classmethod
    def setup_class(cls):
        cls.bd = BondData()
        cls.fd = FundData()
        cls.ftd = FutureData()
        cls.ind = IndexData()
        cls.od = OptionData()
        cls.sd = StockData()

    @pytest.mark.parametrize('exchange_house', ['SZ', 'SH'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('bar_size', ['Tick', 'Transaction', 'Order'])
    def test_get_bond_data_day(self, exchange_house, date, bar_size):
        """
        测试get_bond_data_day 获取指定日期全市场债券行情数据
        :param exchange_house: 交易所
        :param date: 日期
        :param bar_size: 数据表名称
        :param sort_by_receive_time: 按数据到达时间排序(默认为False)
        :return:
        """
        df = self.bd.get_bond_data_day(exchange_house=exchange_house, date=date, bar_size=bar_size)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('exchange_house', ['SZ', 'SH'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('sort_by_receive_time', [False, True])
    def test_get_bond_tick_by_exchange(self, exchange_house, date, sort_by_receive_time):
        """
        测试get_bond_tick_by_exchange 按天全市场债券Tick查询
        :param exchange_house: 交易所
        :param date: 日期
        :param sort_by_receive_time: 按数据到达时间排序
        :return:
        """
        df = self.bd.get_bond_tick_by_exchange(exchange_house=exchange_house, date=date,
                                               sort_by_receive_time=sort_by_receive_time)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('exchange_house', ['SZ', 'SH'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('sort_by_receive_time', [False, True])
    def test_get_bond_transaction_by_exchange(self, exchange_house, date, sort_by_receive_time):
        """
        测试get_bond_transaction_by_exchange 按天全市场债券逐笔委托查询
        :param exchange_house: 交易所
        :param date: 日期
        :param sort_by_receive_time: 按数据到达时间排序
        :return:
        """
        df = self.bd.get_bond_transaction_by_exchange(exchange_house=exchange_house, date=date,
                                                      sort_by_receive_time=sort_by_receive_time)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('exchange_house', ['SZ', 'SH'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('sort_by_receive_time', [False, True])
    def test_get_bond_order_by_exchange(self, exchange_house, date, sort_by_receive_time):
        """
        测试get_bond_order_by_exchange 按天全市场债券逐笔成交查询
        :param exchange_house: 交易所
        :param date: 日期
        :param sort_by_receive_time: 按数据到达时间排序
        :return:
        """
        df = self.bd.get_bond_order_by_exchange(exchange_house=exchange_house, date=date,
                                                sort_by_receive_time=sort_by_receive_time)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('exchange_house', ['SZ', 'SH'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('bar_size', ['Tick', 'Transaction', 'Order'])
    def test_get_fund_data_day(self, exchange_house, date, bar_size):
        """
        测试get_fund_data_day 获取指定日期全市场基金行情数据
        :param exchange_house: 交易所
        :param date: 日期
        :param bar_size: 数据表名称
        :param sort_by_receive_time: 按数据到达时间排序(默认为False)
        :return:
        """
        df = self.fd.get_fund_data_day(exchange_house=exchange_house, date=date, bar_size=bar_size)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('exchange_house', ['SZ', 'SH'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('sort_by_receive_time', [False, True])
    def test_get_fund_tick_by_exchange(self, exchange_house, date, sort_by_receive_time):
        """
        测试get_fund_tick_by_exchange 按天全市场基金Tick查询
        :param exchange_house: 交易所
        :param date: 日期
        :param sort_by_receive_time: 按数据到达时间排序
        :return:
        """
        df = self.fd.get_fund_tick_by_exchange(exchange_house=exchange_house, date=date,
                                               sort_by_receive_time=sort_by_receive_time)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('exchange_house', ['SZ', 'SH'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('sort_by_receive_time', [False, True])
    def test_get_fund_transaction_by_exchange(self, exchange_house, date, sort_by_receive_time):
        """
        测试get_fund_transaction_by_exchange 按天全市场基金逐笔委托查询
        :param exchange_house: 交易所
        :param date: 日期
        :param sort_by_receive_time: 按数据到达时间排序
        :return:
        """
        df = self.fd.get_fund_transaction_by_exchange(exchange_house=exchange_house, date=date,
                                                      sort_by_receive_time=sort_by_receive_time)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('exchange_house', ['SZ', 'SH'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('sort_by_receive_time', [False, True])
    def test_get_fund_order_by_exchange(self, exchange_house, date, sort_by_receive_time):
        """
        测试get_fund_order_by_exchange 按天全市场基金逐笔成交查询
        :param exchange_house: 交易所
        :param date: 日期
        :param sort_by_receive_time: 按数据到达时间排序
        :return:
        """
        df = self.fd.get_fund_order_by_exchange(exchange_house=exchange_house, date=date,
                                                sort_by_receive_time=sort_by_receive_time)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.skip
    @pytest.mark.parametrize('exchange_house', ['CF'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('bar_size', ['Tick'])
    def test_get_future_data_day(self, exchange_house, date, bar_size):
        """
        测试get_future_data_day 获取指定日期全市场期货行情数据
        :param exchange_house: 交易所
        :param date: 日期
        :param bar_size: 数据表名称
        :param sort_by_receive_time: 按数据到达时间排序(默认为False)
        :return:
        """
        df = self.ftd.get_future_data_day(exchange_house=exchange_house, date=date, bar_size=bar_size)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.skip
    @pytest.mark.parametrize('exchange_house', ['CF'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('sort_by_receive_time', [False, True])
    def test_get_future_tick_by_exchange(self, exchange_house, date, sort_by_receive_time):
        """
        测试get_future_tick_by_exchange 按天全市场期货Tick查询
        :param exchange_house: 交易所
        :param date: 日期
        :param sort_by_receive_time: 按数据到达时间排序
        :return:
        """
        df = self.ftd.get_future_tick_by_exchange(exchange_house=exchange_house, date=date,
                                                  sort_by_receive_time=sort_by_receive_time)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('exchange_house', ['SZ', 'SH'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('bar_size', ['Index'])
    def test_get_index_data_day(self, exchange_house, date, bar_size):
        """
        测试get_index_data_day 获取指定日期全市场指数行情数据
        :param exchange_house: 交易所
        :param date: 日期
        :param bar_size: 数据表名称
        :param sort_by_receive_time: 按数据到达时间排序(默认为False)
        :return:
        """
        df = self.ind.get_index_data_day(exchange_house=exchange_house, date=date, bar_size=bar_size)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('exchange_house', ['SZ', 'SH'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('sort_by_receive_time', [False, True])
    def test_get_index_by_exchange(self, exchange_house, date, sort_by_receive_time):
        """
        测试get_index_by_exchange 按天全市场指数查询
        :param exchange_house: 交易所
        :param date: 日期
        :param sort_by_receive_time: 按数据到达时间排序
        :return:
        """
        df = self.ind.get_index_by_exchange(exchange_house=exchange_house, date=date,
                                            sort_by_receive_time=sort_by_receive_time)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('exchange_house', ['SZ', 'SH'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('bar_size', ['Tick'])
    def test_get_option_data_day(self, exchange_house, date, bar_size):
        """
        测试get_option_data_day 获取指定日期全市场指数行情数据
        :param exchange_house: 交易所
        :param date: 日期
        :param bar_size: 数据表名称
        :param sort_by_receive_time: 按数据到达时间排序(默认为False)
        :return:
        """
        df = self.od.get_option_data_day(exchange_house=exchange_house, date=date, bar_size=bar_size)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('exchange_house', ['SZ', 'SH'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('sort_by_receive_time', [False, True])
    def test_get_option_tick_by_exchange(self, exchange_house, date, sort_by_receive_time):
        """
        测试get_option_tick_by_exchange 按天全市场指数查询
        :param exchange_house: 交易所
        :param date: 日期
        :param sort_by_receive_time: 按数据到达时间排序
        :return:
        """
        df = self.od.get_option_tick_by_exchange(exchange_house=exchange_house, date=date,
                                                 sort_by_receive_time=sort_by_receive_time)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('exchange_house', ['SZ', 'SH'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('bar_size', ['Stock', 'Transaction', 'Order'])
    def test_get_stock_data_day(self, exchange_house, date, bar_size):
        """
        测试get_stock_data_day 获取指定日期全市场行情数据
        :param exchange_house: 交易所
        :param date: 日期
        :param bar_size: 数据表名称
        :param sort_by_receive_time: 按数据到达时间排序(默认为False)
        :return:
        """
        df = self.sd.get_stock_data_day(exchange_house=exchange_house, date=date, bar_size=bar_size)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('exchange_house', ['SZ', 'SH'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('sort_by_receive_time', [False, True])
    def test_get_stock_tick_by_exchange(self, exchange_house, date, sort_by_receive_time):
        """
        测试get_stock_tick_by_exchange 按天查询全市场股票Tick查询
        :param exchange_house: 交易所
        :param date: 日期
        :param sort_by_receive_time: 按数据到达时间排序
        :return:
        """
        df = self.sd.get_stock_tick_by_exchange(exchange_house=exchange_house, date=date,
                                                sort_by_receive_time=sort_by_receive_time)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('exchange_house', ['SZ', 'SH'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('sort_by_receive_time', [False, True])
    def test_get_stock_transaction_by_exchange(self, exchange_house, date, sort_by_receive_time):
        """
        测试get_stock_transaction_by_exchange 按天查询全市场逐笔委托查询
        :param exchange_house: 交易所
        :param date: 日期
        :param sort_by_receive_time: 按数据到达时间排序
        :return:
        """
        df = self.sd.get_stock_transaction_by_exchange(exchange_house=exchange_house, date=date,
                                                       sort_by_receive_time=sort_by_receive_time)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0

    @pytest.mark.parametrize('exchange_house', ['SZ', 'SH'])
    @pytest.mark.parametrize('date', ['20220125'])
    @pytest.mark.parametrize('sort_by_receive_time', [False, True])
    def test_get_stock_order_by_exchange(self, exchange_house, date, sort_by_receive_time):
        """
        测试get_stock_order_by_exchange 按天查询全市场逐笔成交查询
        :param exchange_house: 交易所
        :param date: 日期
        :param sort_by_receive_time: 按数据到达时间排序
        :return:
        """
        df = self.sd.get_stock_order_by_exchange(exchange_house=exchange_house, date=date,
                                                 sort_by_receive_time=sort_by_receive_time)
        assert type(df) == pd.DataFrame
        if os.environ.get('DSWMAP_envTag') != 'prd':
            assert len(df) == 0
        else:
            assert len(df) > 0


if __name__ == "__main__":
    pytest.main(["-v"])