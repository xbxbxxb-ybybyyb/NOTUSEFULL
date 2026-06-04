from tquant.basic_data import BasicData
import pytest
import pandas as pd
import os
os.environ['exec_env'] = ''

class TestBasicData(object):
    @classmethod
    def setup_class(cls):
        cls.bd = BasicData()

    @pytest.mark.parametrize('t_type', ['US', 'HK', 'CN'])
    @pytest.mark.parametrize('start_time, end_time', [(20180101, 20200501)])
    def test_get_trading_day_basic(self, start_time, end_time, t_type):
        result = self.bd.get_trading_day(start_time, end_time, location=t_type)
        assert isinstance(result, list)
        assert len(result) > 0
        if t_type == 'US':
            assert len(result) == 587
        elif t_type == 'HK':
            assert len(result) == 573
        else:
            assert len(result) == 566

    @pytest.mark.parametrize('start_time', ["20180101"])
    @pytest.mark.parametrize('end_time', [10, -20, 10001, -10001, "20200501"])
    @pytest.mark.parametrize('frequency', [None, "DAY", "WEEK", "MONTH", "QUARTER", "HALFYEAR", "YEAR"])
    @pytest.mark.parametrize('day_type', [None, "MONDAY", "FIRSTDAY", "LASTDAY", "ALLDAYS"])
    @pytest.mark.smoke
    def test_tradingday_extend(self, start_time, end_time, frequency, day_type):
        """
        测试tradingday获取交易日
        :return:
         startTime, endTime, frequency='DAY', dayType=None, dateType='TRADINGDAYS', location='CN'
        """
        if not frequency:
            result = self.bd.get_trading_day(start_time, end_time)
            assert isinstance(result, list)
            assert len(result) > 0
        elif frequency != "DAY" and type(end_time) == int:
            pass
        else:
            if not day_type:
                result = self.bd.get_trading_day(start_time, end_time, frequency)
                assert isinstance(result, list)
                if os.environ.get("DSWMAP_envTag") == 'prd':
                    assert len(result) > 0
            else:
                if(frequency != "DAY" or frequency != "WEEK") and (day_type != "FIRSTDAY" or day_type != "LASTDAY"):
                    pass
                else:
                    result = self.bd.get_trading_day(start_time, end_time, frequency, day_type)
                    assert isinstance(result, list)
                    assert len(result) > 0

    @pytest.mark.parametrize('start_time', ["20110102"])
    @pytest.mark.parametrize('end_time', ["20190110"])
    @pytest.mark.parametrize('frequency', ["DAY", "YEAR"])
    @pytest.mark.parametrize('day_type', [None, "MONDAY"])
    @pytest.mark.parametrize('date_type', ["TRADINGDAYS", "TRADINGDAYS1"])
    @pytest.mark.parametrize('t_type', ["CN", "CN1"])
    def test_tradingday_exe(self, start_time, end_time, frequency, day_type, date_type, t_type):
        """
        测试tradingday异常测试
        :param t_data: 测试数据
        :param expect: 异常
        :return:
        """
        t_type_check = t_type in ['US', 'HK', 'CN']
        date_type_check = date_type in ["TRADINGDAYS"]
        frequency_check = (frequency in ["MONTH", "QUARTER", "HALFYEAR", "YEAR"]) \
                          and (day_type not in [None, "FIRSTDAY", "LASTDAY"])
        date_check = (len(start_time) == 8) or (len(end_time) == 8)
        if not t_type_check:
            with pytest.raises(Exception) as exe_info:
                self.bd.get_trading_day(start_time, end_time, frequency, day_type, date_type, t_type)
            assert "参数支持'CN':国内A股，'HK':港股，'US':美股，请重新输入！" in str(exe_info.value)
        else:
            if frequency_check:
                with pytest.raises(Exception) as exe_info:
                    self.bd.get_trading_day(start_time, end_time, frequency, day_type, date_type, t_type)
                assert "frequency取值MONTH,QUARTER,HALFYEAR,YEAR时，dayType仅支持FIRSTDAY、LASTDAY" in str(exe_info.value)

            else:
                if not date_type_check:
                    with pytest.raises(Exception) as exe_info:
                        self.bd.get_trading_day(start_time, end_time, frequency, day_type, date_type, t_type)
                    assert "dateType 取值TRADINGDAYS 交易日、ALLDAYS 日历日，默认TRADINGDAYS" in str(exe_info.value)
                else:
                    if not date_check:
                        with pytest.raises(Exception) as exe_info:
                            self.bd.get_trading_day(start_time, end_time, frequency, day_type, date_type, t_type)
                        assert "日期格式" in str(exe_info.value)


    @pytest.mark.parametrize('industry_type', ['CSRC', 'CITICS', 'SW', 'CS'])
    @pytest.mark.parametrize('level', [0, 1, 2, 3, 4])
    @pytest.mark.smoke
    def test_get_industry(self, industry_type, level):
        """
        测试get_industry获取行业分类
        :param industry_type:行业类型
        :param level:级别
        :return:
        """
        if industry_type == 'CS':
            df = self.bd.get_industry(industry_type, level)
            assert isinstance(df, pd.DataFrame)
            assert 'industry_code' in df.columns and 'industry_name' in df.columns
            assert len(df) > 0
        elif industry_type == 'CSRC':
            if level > 2:
                try:
                    df = self.bd.get_industry(industry_type, level)
                except Exception as e:
                    assert (e, "证监会行业只有两级行业分类取值[0,2]之间的整数，请重新输入！")
            else:
                df = self.bd.get_industry(industry_type, level)
                assert isinstance(df, pd.DataFrame)
                assert 'industry_code' in df.columns and 'industry_name' in df.columns
                assert len(df) > 0

        else:
            if level >3:
                try:
                    df = self.bd.get_industry(industry_type, level)
                except Exception as e:
                    assert (e, "只有中证行业分类取值[0,4]之间的整数，请重新输入！")
            else:
                df = self.bd.get_industry(industry_type, level)
                assert isinstance(df, pd.DataFrame)
                assert 'industry_code' in df.columns and 'industry_name' in df.columns
                assert len(df) > 0

    @pytest.mark.parametrize('industry_type', ['SW2021'])
    @pytest.mark.parametrize('level', [1, 2, 3, 4])
    @pytest.mark.smoke
    def test_get_industry_sw2021(self, industry_type, level):
        """
        测试get_industry获取行业分类
        :param industry_type:行业类型
        :param level:级别
        :return:
        """
        if level > 3:
            try:
                df = self.bd.get_industry(industry_type, level)
            except Exception as e:
                assert (e, "申万行业分类(2021)取值1~3之间的整数，请重新输入！")
        else:
            df = self.bd.get_industry(industry_type, level)
            assert isinstance(df, pd.DataFrame)
            assert 'industry_code' in df.columns and 'industry_name' in df.columns
            assert len(df) > 0

    @pytest.mark.parametrize("industry_type", ["CSRC", "CSRC111"])
    @pytest.mark.parametrize("level", [-1, 2, 4])
    def test_get_industry_exe(self, industry_type, level):
        """
        测试get_industry
        :param level:
        :return:
        """
        ErrorStr1 = '只有中证行业分类取值[0,4]之间的整数，请重新输入！'
        ErrorStr2 = '[level]行业级别，取值[0,4]之间的整数，默认0，请重新输入！'
        ErrorStr3 = "[industryType]行业类型：'CSRC' 为证监会行业分类，'CITICS' 为中信行业分类，'SW' 为申万行业分类，'CS'为中证行业，'SW2021'为申万行业分类(2021)，请重新输入！"
        if level not in [0, 1, 2, 3, 4]:
            with pytest.raises(Exception) as exe_info:
                self.bd.get_industry(industry_type, level)
            assert ErrorStr2 in str(exe_info.value)
        else:
            if level == 4 and industry_type != 'CS':
                with pytest.raises(Exception) as exe_info:
                    self.bd.get_industry(industry_type, level)
                assert ErrorStr1 in str(exe_info.value)
            elif industry_type not in ['CSRC', 'CITICS', 'SW', 'CS', 'SW2021']:
                with pytest.raises(Exception) as exe_info:
                    self.bd.get_industry(industry_type, level)
                assert ErrorStr3 in str(exe_info.value)

    @pytest.mark.parametrize('trading_code', ['603766.SH', '000001.SZ'])
    def test_get_conception(self, trading_code):
        df = self.bd.get_conception(trading_code)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'CONCEPTTYPECODE' in df.columns and 'EXCHANGENAME' in df.columns


if __name__ == "__main__":
    pytest.main(["-v"])


