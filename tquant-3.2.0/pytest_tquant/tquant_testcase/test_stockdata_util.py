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

    @pytest.mark.parametrize('date_time', ['20191231', '20180108'])
    @pytest.mark.parametrize('plate_id', ['CITICS.b1', 'CITICS.b101', 'CITICS.b10102', 'CITICS.b106040700',
                                          'SW.61', 'SW.6102', 'SW.610102', 'SW.61010201', 'CSRC.12', 'CSRC.1202',
                                          'CSRC.120102', 'CS.72', 'CS.7202', 'CS.720201', 'CS.72020102',
                                          'CS.7201010101', 'CITICS.b10t'])
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

    @pytest.mark.parametrize('date_time', ['20211222'])
    @pytest.mark.parametrize('plate_id', ['SW2021.46', 'SW2021.46620306'])
    def test_get_plate_info_industry_sw2021(self, date_time, plate_id):
        """
        测试get_plate_info获取行业板块成分股信息(新增SW2021)
        :param date_time:
        :param plate_id:
        :return:
        """
        result = self.sd.get_plate_info('INDUSTRY', date_time, plate_id)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('date_time', ('20191231',))
    @pytest.mark.parametrize('plate_id', ('ALLA', 'SHA', 'SZA',  'GEM', 'ALLA_HIS', 'STI', 'MBA'))
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

    @pytest.mark.parametrize('date_time', ('20191011', '20201012'))
    @pytest.mark.parametrize('plate_id', ['00030142'])
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

    @pytest.mark.parametrize('switch_flag', ['ON', 'OFF'])
    @pytest.mark.parametrize('industry_type', ['CSRC', 'CITICS', 'SW', 'CS'])
    @pytest.mark.parametrize('level', [1, 2, 3, 4])
    def test_get_stock_industry(self, industry_type, level, switch_flag):
        """
        测试get_stock_industry股票行业信息
        :param industry_type:行业类型
        :param level:行业级别
        :return:
        """
        trading_codes = self.sd.get_plate_info('MARKET', '20180309', 'SHA').loc[:, 'stock'].tolist()[:100]
        if (industry_type == 'CS'):
            result = self.sd.get_stock_industry(trading_codes, '20180516', industry_type,
                                                industry_level=level, switch_flag=switch_flag)
            assert len(result) > 0
            assert isinstance(result, pd.DataFrame)
        elif(industry_type == 'CSRC'):
            if(level<3):
                result = self.sd.get_stock_industry(trading_codes, '20180516', industry_type,
                                                    industry_level=level, switch_flag=switch_flag)
                assert len(result) > 0
                assert isinstance(result, pd.DataFrame)
            else:
                try:
                    result = self.sd.get_stock_industry(trading_codes, '20180516', industry_type,
                                                        industry_level=level, switch_flag=switch_flag)
                except Exception as e:
                    assert (e, "证监会只有两级分类，取[1,2]的整数！")
        else:
            if (level < 4):
                result = self.sd.get_stock_industry(trading_codes, '20180516', industry_type,
                                                    industry_level=level, switch_flag=switch_flag)
                assert len(result) > 0
                assert isinstance(result, pd.DataFrame)
            else:
                try:
                    result = self.sd.get_stock_industry(trading_codes, '20180516', industry_type,
                                                        industry_level=level, switch_flag=switch_flag)
                except Exception as e:
                    assert (e, "中信行业、申万行业只有三级分类，取[1,3]的整数！")

    @pytest.mark.parametrize('switch_flag', ['ON', 'OFF'])
    @pytest.mark.parametrize('industry_type', ['SW2021'])
    @pytest.mark.parametrize('level', [1, 2, 3, 4])
    def test_get_stock_industry_sw2021(self, industry_type, level, switch_flag):
        """
        测试get_stock_industry股票行业信息
        :param industry_type:行业类型
        :param level:行业级别
        :return:
        """
        trading_codes = ['000100.SZ', '000807.SZ']
        if (level < 4):
            result = self.sd.get_stock_industry(trading_codes, '20211222', industry_type,
                                                industry_level=level, switch_flag=switch_flag)
            assert len(result) > 0
            assert isinstance(result, pd.DataFrame)
        else:
            try:
                result = self.sd.get_stock_industry(trading_codes, '20211222', industry_type,
                                                    industry_level=level, switch_flag=switch_flag)
            except Exception as e:
                assert (e, "申万行业(2021)只有三级分类，取[1,3]的整数！")

    @pytest.mark.parametrize('filter_date', ['20180516', '20191231'])
    @pytest.mark.parametrize('filter_type', ['STPT', 'SUSPEND', 'OPENUPLIMIT', 'OPENDOWNLIMIT', 'SSO',
                                             'STSPEND', 'STUP', 'STDOWN', 'UPSPEND', 'DNSPWND', 'DELIST'])
    def test_stock_filter(self, filter_date, filter_type):
        """
        测试stock_filter股票池过滤
        :param filter_date:查询日期
        :param filter_type:过滤类型
        :return:
        """
        if filter_type == 'DELIST':
            stock_pool = self.sd.get_plate_info('MARKET', '20200601', 'ALLA')
            after_filter = self.sd.stock_filter(stock_pool=stock_pool['stock'].tolist(), filter_date = filter_date, filter_type = filter_type)
            dif = pd.concat([stock_pool, after_filter], ignore_index=True).drop_duplicates(keep=False)
            st = dif[dif['stock_name'].str.contains('ST')]
            delist = dif[dif['stock_name'].str.contains('退')]
            assert isinstance(after_filter, pd.DataFrame)
            assert len(st) + len(delist)>0

        else:
            stock_pool = self.sd.get_plate_info('MARKET', '20180309', 'SHA').loc[:, 'stock'].tolist()
            result = self.sd.stock_filter(stock_pool, filter_date, filter_type=filter_type)
            assert len(result) <= len(stock_pool)
            assert isinstance(result, pd.DataFrame)

    @pytest.mark.skip
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
