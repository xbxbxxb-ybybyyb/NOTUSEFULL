from tquant.basic_data import BasicData
import pytest
import pandas as pd


class TestBasicData(object):
    @classmethod
    def setup_class(cls):
        cls.bd = BasicData()

    @pytest.mark.parametrize('t_type', ('US', 'HK', 'CN'))
    @pytest.mark.parametrize('t_date', ((20180101, 20200501),))
    def test_get_trading_day_basic(self, t_date, t_type):
        result = self.bd.get_trading_day(*t_date, location=t_type)
        assert isinstance(result, list)
        assert len(result) > 0
        if t_type == 'US':
            assert len(result) == 587
        elif t_type == 'HK':
            assert len(result) == 573
        else:
            assert len(result) == 566

    @pytest.mark.parametrize('t_data', (('20180101', 10), ('20180101', -20), ('20180101', 10001), ('20180101', -10001),
                                        ('20180101', '20180501', 'DAY'), ('20180101', '20180501', 'WEEK'),
                                        ('20180101', '20200501', 'MONTH'), ('20180101', '20200501', 'QUARTER'),
                                        ('20180101', '20200501', 'HALFYEAR'), ('20180101', '20200501', 'YEAR'),
                                        ('20180101', '20180501', 'DAY', 'MONDAY'),
                                        ('20180101', '20180501', 'WEEK', 'MONDAY'),
                                        ('20180101', '20180501', 'WEEK', 'LASTDAY'),
                                        ('20180101', '20180501', 'MONTH', 'LASTDAY'),
                                        ('20180101', '20200501', 'YEAR', 'FIRSTDAY'),
                                        ('20180101', '20200501', 'QUARTER', 'LASTDAY'),
                                        ('20180101', '20200501', 'QUARTER', 'FIRSTDAY'),
                                        ('20180101', '20200501', 'HALFYEAR', 'LASTDAY'),
                                        ('20180101', '20200501', 'HALFYEAR', 'FIRSTDAY', 'ALLDAYS')))
    @pytest.mark.smoke
    def test_tradingday_extend(self, t_data):
        """
        测试tradingday获取交易日
        :return:
         startTime, endTime, frequency='DAY', dayType=None, dateType='TRADINGDAYS', location='CN'
        """
        result = self.bd.get_trading_day(*t_data)
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.parametrize('t_data, expect', ((('20110102', '20190110', 'DAY', None, 'TRADINGDAYS', 'CN1'), '参数支持'),
                                                (('20110102', '20190110', 'YEAR', 'MONDAY', 'TRADINGDAYS', 'CN'), '仅支持'),
                                                (('20110102', '20190110', 'DAY', None, 'TRADINGDAYS1', 'CN'), '重新输入'),
                                                (('2011013', '20190110', 'DAY', None, 'TRADINGDAYS', 'CN'), '日期格式')))
    def test_tradingday_exe(self, t_data, expect):
        """
        测试tradingday异常测试
        :param t_data: 测试数据
        :param expect: 异常
        :return:
        """
        with pytest.raises(Exception) as exec_info:
            self.bd.get_trading_day(*t_data)
        assert expect in str(exec_info.value)

    @pytest.mark.parametrize("industry_type, level", (('CSRC', 0), ('CSRC', 1), ('CSRC', 2),
                                                      ('CITICS', 0), ('CITICS', 1), ('CITICS', 2), ('CITICS', 3),
                                                      ('SW', 0), ('SW', 1), ('SW', 2), ('SW', 3)))
    @pytest.mark.smoke
    def test_get_industry(self, industry_type, level):
        """
        测试get_industry获取行业分类
        :param industry_type:行业类型
        :param level:级别
        :return:
        """
        df = self.bd.get_industry(industry_type, level)
        assert isinstance(df, pd.DataFrame)
        assert 'industry_code' in df.columns and 'industry_name' in df.columns
        assert len(df) > 0

    @pytest.mark.parametrize("industry_type, level", (('CSRC', -1), ('CSRC', 4)))
    def test_get_industry_exe(self, industry_type, level):
        """
        测试get_industry
        :param level:
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.bd.get_industry(industry_type, level)
        assert '取值[0,3]' in str(exe_info.value)

    @pytest.mark.parametrize('trading_code', ('603766.SH', '000001.SZ'))
    def test_get_conception(self, trading_code):
        df = self.bd.get_conception(trading_code)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'CONCEPTTYPECODE' in df.columns and 'EXCHANGENAME' in df.columns


if __name__ == "__main__":
    pytest.main(["-v"])


