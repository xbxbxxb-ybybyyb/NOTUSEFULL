from tquant.SmartFactor.HFBaseFactor import HFBaseFactor
from tquant.SmartFactor import get_custom_factor_class
import pytest
import numpy as np


class Fund_Factor(HFBaseFactor):
    factor_type = "TICK"
    factor_name = 'Fund_Factor'
    security_type = 'fund'
    security_pool = ["515520.SH", "159968.SZ", "511660.SH"]

    def calc(self, price_data, factor_data, custom_params):
        res = np.log(price_data['LastPx'] / price_data['PreClosePx']) * 1000
        res.index = price_data["MDTime"]
        return res


class High_Factor(HFBaseFactor):
    factor_type = "TICK"
    factor_name = 'High_Factor'
    security_type = 'stock'
    security_pool = ['688001.SH']
    custom_params = {"interval_seconds": 50, "tick_interval_seconds": 3}

    def calc(self, price_data, factor_data, custom_params):
        interval_seconds = custom_params["interval_seconds"]
        tick_interval_seconds = custom_params["tick_interval_seconds"]
        n_tick = interval_seconds // tick_interval_seconds

        res = price_data['LastPx'].diff(n_tick) / price_data['LastPx'].shift(n_tick) * 1000
        res.index = price_data['MDTime']

        return res


class Test_high_FactorCalc(object):
    @classmethod
    def setup_class(cls):
        cls.hf = High_Factor()
        cls.ff = Fund_Factor()

    @pytest.mark.parametrize('factor_name, expect', (('%High_Factor', '不符合格式'),
                                                     ('High_Factor#', '不符合格式'),
                                                     (1, '字符串格式')))
    def test_highfactor_factor_name(self, factor_name, expect):
        with pytest.raises(Exception) as exe_info:
            self.hf.factor_name = factor_name
            self.hf.run_hfre_factor_value("20200901", "20200902")
        assert expect in str(exe_info.value)
        self.hf.factor_name = 'High_Factor'

    @pytest.mark.parametrize('factor_type, expect', (('DAY1', 'factor_type目前仅支持'),
                                                     ('TICK1', 'factor_type目前仅支持'),
                                                     (1, 'factor_type目前仅支持')))
    def test_highfactor_factor_type(self, factor_type, expect):
        with pytest.raises(Exception) as exe_info:
            self.hf.factor_type = factor_type
            self.hf.run_hfre_factor_value("20200901", "20200902")
        assert expect in str(exe_info.value)
        self.hf.factor_type = 'TICK'

    @pytest.mark.parametrize('security_type, expect', (('fund1', 'stock,fund的因子开发'),
                                                       ('FUND', 'stock,fund的因子开发'),
                                                       ('stock1', 'stock,fund的因子开发'),
                                                       ('STOCK', 'stock,fund的因子开发')))
    def test_highfactor_security_type(self, security_type, expect):
        with pytest.raises(Exception) as exe_info:
            self.hf.security_type = security_type
            self.hf.run_hfre_factor_value("20200901", "20200902")
        assert expect in str(exe_info.value)
        self.hf.security_type = 'stock'

    def test_stock_run_hfre_factor_value(self):
        df = self.hf.run_hfre_factor_value("20200901", "20200902")
        assert isinstance(df, dict)

    def test_fund_run_hfre_factor_value(self):
        df = self.ff.run_hfre_factor_value("20200512", "20200512")
        assert isinstance(df, dict)

    def test_get_custom_factor_class(self):
        pxchange = get_custom_factor_class(High_Factor, {"custom_params": {"interval_seconds": 70,
                                                                           "tick_interval_seconds": 7}})
        pxchange_ins = pxchange()
        df = pxchange_ins.run_hfre_factor_value("20200901", "20200902")
        assert isinstance(df, dict)


if __name__ == "__main__":
    pytest.main(['-v'])

