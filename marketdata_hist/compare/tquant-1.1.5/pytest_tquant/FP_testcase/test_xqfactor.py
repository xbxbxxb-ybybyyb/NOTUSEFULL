from FactorProvider.factordata.xqfactor import *
import pytest
import pandas as pd


class TestXqfactor(object):
    @classmethod
    def setup_class(cls):
        pass

    @pytest.mark.parametrize('date_list', ('20200506', 20200506, ['20200506'], ['20200506', '20200507', '20200508']))
    @pytest.mark.parametrize('factor_list', (['pre_close', 'open', 'high', "stpt", "rel_ipo_pct_chg_badj",
                                              "re_ipo_chg_badj", "share_totala", "maxupordown", "susp_reason"],
                                             ['pre_close', 'open', 'high']))
    def test_get_market_price(self, date_list, factor_list):
        """
        1.日行情指标
        :return:
        """
        result = get_market_price(['000300.SH', '600094.SH', '000822.SZ'], date_list, factor_list)
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize("date_list", ('20200506', ['20200506'], 20200506, ['20200506', '20200507', '20200508']))
    def test_get_factor_idct(self, date_list):
        """
        2、同时包含估值与风险因子
        :return:
        """
        result = get_factor_idct(['600720.SH', '000756.SZ', '600711.SH'], date_list,
                                 ['dyr_12', 'a_mkt_cap', 'annualyeild_100w', 'annualyeild_24m'])
        assert isinstance(result, pd.DataFrame)
        #assert result.iloc[0][0] === 36.68

    @pytest.mark.parametrize("date_list", (['20190630', '20190930', '20191231', '20200331'], ['20190630'], '20190630'))
    def test_get_finance_idct(self, date_list):
        """
        3、财务分析 5个因子对应5个part
        :return:
        """
        result = get_finance_idct(['002615.SZ', '300330.SZ', '000755.SZ'], date_list,
                                  ['eps_basic', 'gctogr_ttm', 'tltota_ttm', 'yoy_tr', 'ocftointerest'])
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize("factor_list", (["short_name", "listing_date", "listing_place", "listing_board",
                       "currency", "delisting_date","con_sector", "key_indices_con", "shhk_stk_conn"], ['con_sector']))
    @pytest.mark.parametrize("trading_codes", (['600077.SH', '002236.SZ', '600652.SH', '688016.SH'], ['600077.SH']))
    def test_get_stock_info(self, factor_list, trading_codes):
        """
        4.测试最新消息
        :return:
        """
        result = get_stock_info(trading_codes, factor_list)
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize("date_list", (['20190930'], '20190930', ['20190630', '20190930', '20191231', '20200331'],
                                           ['20190630', '20200331']))
    def test_get_finance_report(self, date_list):
        """
        财务报告
        :return:
        """
        result = get_finance_report(['000999.SZ', '001896.SZ','002792.SZ'], date_list,
                                    ['monetary_cap', 'tradable_fin_assets'], statement_type='102')
        assert isinstance(result, pd.DataFrame)


if __name__ == "__main__":
    pytest.main(["-v"])




