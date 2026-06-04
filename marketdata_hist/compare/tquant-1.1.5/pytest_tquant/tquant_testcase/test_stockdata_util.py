from tquant.stock_data import StockData
import pytest
import pandas as pd


class TestStockData(object):
    """
    测试StockData工具数据接口
    """
    @classmethod
    def setup_class(cls):
        cls.sd = StockData()

    @pytest.mark.parametrize('trading_code', ('688001.SH', ['688001.SH'], ['000001.SZ', '688599.SH']))
    def test_get_stock_basics(self, trading_code):
        """
        测试get_stock_basics获取股票的基本信息
        :param trading_code:单支股票代码或多支股票的列表
        :return:
        """
        df = self.sd.get_stock_basics(trading_code)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    @pytest.mark.parametrize('t_data, expect', ((13, 'list/string类型'),))
    def test_get_stock_basics_exe(self, t_data, expect):
        """
        异常测试get_stock_basics获取股票的基本信息
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd.get_stock_basics(t_data)
        assert expect in str(exe_info.value)

    @pytest.mark.parametrize('date_time', ('20191231', '20180108'))
    @pytest.mark.parametrize('plate_id', ('CITICS.b1', 'CITICS.b101', 'CITICS.b10102', 'CITICS.b106040700',
                                          'SW.61', 'SW.6102', 'SW.610102', 'SW.61010201',
                                          'CSRC.12', 'CSRC.1202', 'CSRC.120102'))
    def test_get_plate_info_industry(self, date_time, plate_id):
        """
        测试get_plate_info获取行业板块成分股信息
        :param date_time:
        :param plate_id:
        :return:
        """
        result = self.sd.get_plate_info('INDUSTRY', date_time, plate_id)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('date_time', ('20191231',))
    @pytest.mark.parametrize('plate_id', ('ALLA', 'SHA', 'SZA', 'SME', 'GEM', 'ALLA_HIS', 'STI', 'MBA'))
    def test_get_plate_info_market(self, date_time, plate_id):
        """
        测试get_plate_info获取市场板块成分股信息
        :param date_time:
        :param plate_id:
        :return:
        """
        result = self.sd.get_plate_info('MARKET', date_time, plate_id)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('date_time', ('20191231', '20180108'))
    @pytest.mark.parametrize('plate_id', ('00030730', '00031015'))
    def test_get_plate_info_concept(self, date_time, plate_id):
        """
        测试get_plate_info获取概念板块成分股信息
        :param date_time:
        :param plate_id:
        :return:
        """
        result = self.sd.get_plate_info('CONCEPT', date_time, plate_id)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('t_data, expect', ((('INDUSTRY1', '20030101', 'CITICS.b1'), '目前只支持'),
                                                (('INDUSTRY', {'20030101'}, 'CITICS.b1'), 'str'),
                                                (('INDUSTRY', '200301011', 'CITICS.b1'), '格式')))
    def test_get_plate_info_exe(self, t_data, expect):
        """
        异常测试get_plate_info查询成分股信息
        :param t_data: 测试数据
        :param expect: 期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd.get_plate_info(*t_data)
        assert expect in str(exe_info.value)

    @pytest.mark.parametrize('switch_flag', ('ON', 'OFF'))
    @pytest.mark.parametrize("industry_type, level", (('CSRC', 1), ('CSRC', 2),
                                                      ('CITICS', 1), ('CITICS', 2), ('CITICS', 3),
                                                      ('SW', 1), ('SW', 2), ('SW', 3)))
    def test_get_stock_industry(self, industry_type, level, switch_flag):
        """
        测试get_stock_industry股票行业信息
        :param industry_type:行业类型
        :param level:行业级别
        :return:
        """
        trading_codes = self.sd.get_plate_info('MARKET', '20180309', 'SHA').loc[:, 'stock'].tolist()[:100]
        result = self.sd.get_stock_industry(trading_codes, '20180516', industry_type,
                                            industry_level=level, switch_flag=switch_flag)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('filter_date', ('20180516', '20191231'))
    @pytest.mark.parametrize('filter_type', ('STPT', 'SUSPEND', 'OPENUPLIMIT', 'OPENDOWNLIMIT', 'SSO',
                                             'STSPEND', 'STUP', 'STDOWN', 'UPSPEND', 'DNSPWND'))
    def test_stock_filter(self, filter_date, filter_type):
        """
        测试stock_filter股票池过滤
        :param filter_date:查询日期
        :param filter_type:过滤类型
        :return:
        """
        stock_pool = self.sd.get_plate_info('MARKET', '20180309', 'SHA').loc[:, 'stock'].tolist()
        result = self.sd.stock_filter(stock_pool, filter_date, filter_type=filter_type)
        assert len(result) <= len(stock_pool)
        assert isinstance(result, pd.DataFrame)

    def test_get_factors_info(self):
        """
        测试get_factors_info获取tquant所有因子的信息
        :return:
        """
        factors_info = self.sd.get_factors_info()
        assert len(factors_info) > 0
        assert isinstance(factors_info, dict)


if __name__ == "__main__":
    pytest.main(["-v"])
