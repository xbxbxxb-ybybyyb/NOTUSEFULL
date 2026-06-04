from tquant.option_data import OptionData
import pytest
import pandas as pd
import os
import configparser


class TestOptionData(object):
    """
    测试获取期权数据
    """
    conn = configparser.ConfigParser()
    # 加载现有配置文件
    conn.read(r"/opt/anaconda3/lib/python3.6/site-packages/MDCDataProvider/conf/DXPDataProvider.ini",
              encoding="utf-8-sig")
    file_type = conn.get('task', 'file.type')

    @classmethod
    def setup_class(cls):
        cls.od = OptionData()

    @pytest.mark.parametrize('symbol', ['10003736.SH'])
    @pytest.mark.parametrize('start_time, end_time', [('20211201 090000000', '20211213 200000000')])
    def test_get_option_tick(self, symbol, start_time, end_time):
        """
        测试获取期权行情Tick数据
        TODO 异常测试需添加
        :param symbol:期权代码
        :param t_date:测试时间
        :return:
        """
        result = self.od.get_option_tick(symbol, start_time, end_time)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0


if __name__ == '__main__':
    pytest.main(['-v'])