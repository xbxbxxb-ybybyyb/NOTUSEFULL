from tquant.stock_data import StockData
import pytest
import pandas as pd
from xquant.setXquantEnv import xquantEnv

class TestStockData(object):
    """
    测试StockData股票数据接口
    """
    @classmethod
    def setup_class(cls):
        cls.sd = StockData()

    @pytest.mark.parametrize('fill_na', (True, False))
    @pytest.mark.parametrize('t_factor', (['pre_close', 'open', 'high'], 'high'))
    @pytest.mark.parametrize('t_date', (['20180102', '20180103'], '20180102', ('20180102', '20180105')))
    @pytest.mark.parametrize('t_stock', (['300707.SZ', '300705.SZ', '601658.SH'], '300726.SZ'))
    def test_get_factor_price_daily(self, t_stock, t_date, t_factor, fill_na):
        """
        测试get_factor_price_daily日行情
        :param t_stock:股票代码
        :param t_date:日期
        :param t_factor:因子
        :param fill_na:填充NAN
        :return:
        """
        result = self.sd.get_factor_price_daily(t_stock, t_date, t_factor, fill_na=fill_na)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('t_data, expect', ((('300707.SZ', ('20180103', '20180102'), 'high'), '大于结束日期'),
                                                (('300707.SZ', {'20180103', '20180102'}, 'high'), 'date_list'),
                                                (('300707.SZ', '201801031', 'high'), '格式'),
                                                (([], '20180103', 'high'), '股票不能'),
                                                (('300707.SZ', '20180103', None), '因子不能'),
                                                (('300707.SZ', '20180103', 'ev'), '日行情因子')))
    def test_get_factor_price_daily_exe(self, t_data, expect):
        """
        异常测试get_factor_price_daily日行情
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd.get_factor_price_daily(*t_data)
        assert expect in str(exe_info.value)

    @pytest.mark.parametrize('fill_na', (True, False))
    @pytest.mark.parametrize('t_factor', (['ev', 'mkt_cap_ard', 'pe_ttm'], 'mkt_cap_ard'))
    @pytest.mark.parametrize('t_date', (['20180102', '20180103'], '20180102', ('20180102', '20180105')))
    @pytest.mark.parametrize('t_stock', (['002302.SZ', '002372.SZ', '601658.SH'], '002302.SZ'))
    def test_get_factor_valuation_metrics(self, t_stock, t_date, t_factor, fill_na):
        """
        测试get_factor_valuation_metrics获取股票估值指标
        :param t_stock:股票代码
        :param t_date:日期
        :param t_factor:因子
        :param fill_na:填充NAN
        :return:
        """
        result = self.sd.get_factor_valuation_metrics(t_stock, t_date, t_factor, fill_na=fill_na)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('t_data, expect', ((('002302.SZ', ('20180103', '20180102'), 'ev'), '大于结束日期'),
                                                (('002302.SZ', {'20180103', '20180102'}, 'ev'), 'date_list'),
                                                (('002302.SZ', '201801031', 'ev'), '格式'),
                                                (([], '20180103', 'ev'), '股票不能'),
                                                (('002302.SZ', '20180103', None), '因子不能'),
                                                (('002302.SZ', '20180103', 'open'), '估值指标')))
    def test_get_factor_valuation_metrics_exe(self, t_data, expect):
        """
        异常测试get_factor_valuation_metrics获取股票估值指标
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd.get_factor_valuation_metrics(*t_data)
        assert expect in str(exe_info.value)

    @pytest.mark.parametrize('fill_na', (True, False))
    @pytest.mark.parametrize('t_factor', (['annualyeild_100w', 'beta_100w', 'beta_60m'], 'annualyeild_100w'))
    @pytest.mark.parametrize('t_date', (['20180105', '20180112'], '20180112', ('20180105', '20180112')))
    @pytest.mark.parametrize('t_stock', (['600373.SH', '600395.SH', '601658.SH'], '600373.SH'))
    def test_get_factor_risk_analysis(self, t_stock, t_date, t_factor, fill_na):
        """
        测试get_factor_risk_analysis获取股票风险指标
        :param t_stock:股票代码
        :param t_date:日期
        :param t_factor:因子
        :param fill_na:填充NAN
        :return:
        """
        result = self.sd.get_factor_risk_analysis(t_stock, t_date, t_factor, fill_na=fill_na)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('t_data, expect', ((('600395.SH', ('20180103', '20180102'), 'beta_100w'), '大于结束日期'),
                                                (('600395.SH', {'20180103', '20180102'}, 'beta_100w'), 'date_list'),
                                                (('600395.SH', '201801031', 'beta_100w'), '格式'),
                                                (([], '20180103', 'beta_100w'), '股票不能'),
                                                (('600395.SH', '20180103', None), '因子不能'),
                                                (('600395.SH', '20180103', 'open'), '风险指标')))
    def test_get_factor_risk_analysis_exe(self, t_data, expect):
        """
        异常测试get_factor_risk_analysis获取股票风险指标
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd.get_factor_risk_analysis(*t_data)
        assert expect in str(exe_info.value)

    @pytest.mark.parametrize('fill_na', (True, False))
    @pytest.mark.parametrize('t_factor', (['eps_basic', 'eps_diluted', 'roa_ttm'], 'eps_diluted'))
    @pytest.mark.parametrize('t_date', (['20180331', '20180630'], '20180630', ('20180331', '20180630')))
    @pytest.mark.parametrize('t_stock', (['002314.SZ', '600422.SH', '601658.SH'], '002314.SZ'))
    def test_get_factor_financial_analysis(self, t_stock, t_date, t_factor, fill_na):
        """
        测试get_factor_financial_analysis获取股票财务分析指标
        :param t_stock:股票代码
        :param t_date:日期
        :param t_factor:因子
        :param fill_na:填充NAN
        :return:
        """
        result = self.sd.get_factor_financial_analysis(t_stock, t_date, t_factor, fill_na=fill_na)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('t_data, expect', ((('600422.SH', ('20180103', '20180102'), 'eps_diluted'), '大于结束日期'),
                                                (('600422.SH', {'20180103', '20180102'}, 'eps_diluted'), 'date_list'),
                                                (('600422.SH', '201801031', 'eps_diluted'), '格式'),
                                                (([], '20180103', 'eps_diluted'), '股票不能'),
                                                (('600422.SH', '20180103', None), '因子不能'),
                                                (('600422.SH', '20180103', 'open'), '财务分析因子')))
    def test_get_factor_financial_analysis_exe(self, t_data, expect):
        """
        异常测试get_factor_financial_analysis获取股票财务分析指标
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd.get_factor_financial_analysis(*t_data)
        assert expect in str(exe_info.value)

    @pytest.mark.parametrize('statement_type', ('102', '108'))
    @pytest.mark.parametrize('fill_na', (True, False))
    @pytest.mark.parametrize('t_factor', (['monetary_cap', 'notes_rcv', 'dvd_rcv'], 'tot_oper_rev'))
    @pytest.mark.parametrize('t_date', (['20180331', '20180630'], '20180630', ('20180331', '20180630')))
    @pytest.mark.parametrize('t_stock', (['300397.SZ', '002594.SZ', '601658.SH'], '300397.SZ'))
    def test_get_factor_financial_report(self, t_stock, t_date, t_factor, fill_na, statement_type):
        """
        测试get_factor_financial_report获取股票财务报表指标
        :param t_stock:股票代码
        :param t_date:日期
        :param t_factor:因子
        :param fill_na:填充NAN
        :return:
        """
        result = self.sd.get_factor_financial_report(t_stock, t_date, t_factor,
                                                     statement_type=statement_type, fill_na=fill_na)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('t_data, expect', ((('300397.SZ', ('20180103', '20180102'), 'dvd_rcv'), '大于结束日期'),
                                                (('300397.SZ', {'20180103', '20180102'}, 'dvd_rcv'), 'date_list'),
                                                (('300397.SZ', '201801031', 'dvd_rcv'), '格式'),
                                                (([], '20180103', 'dvd_rcv'), '股票不能'),
                                                (('300397.SZ', '20180103', None), '因子不能'),
                                                (('300397.SZ', '20180103', 'open'), '财务报告')))
    def test_get_factor_financial_report_exe(self, t_data, expect):
        """
        异常测试get_factor_financial_report获取股票财务报表指标
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd.get_factor_financial_report(*t_data)
        assert expect in str(exe_info.value)

    @pytest.mark.parametrize('fill_na', (True, False))
    @pytest.mark.parametrize('t_factor', (['per_div_trans', 'per_cashpaidbeforetax', 'ex_dt', 'dvd_payout_dt'], 'dvd_payout_dt'))
    @pytest.mark.parametrize('t_date', (['20180630', '20190930'], '20180630'))
    @pytest.mark.parametrize('t_stock', (['600728.SH', '600340.SH', '002016.SZ'],  '002016.SZ'))
    def test_get_factor_dividend(self, t_stock, t_date, t_factor, fill_na):
        """
        测试get_factor_dividend获取股票分红指标
        :param t_stock:股票代码
        :param t_date:日期
        :param t_factor:因子
        :param fill_na:填充NAN
        :return:
        """
        result = self.sd.get_factor_dividend(t_stock, t_date, t_factor, fill_na=fill_na)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('t_data, expect', ((('600728.SH', ('20180103', '20180106'), 'ex_dt'), 'date_list'),
                                                (('600728.SH', '201801031', 'ex_dt'), '格式'),
                                                (('600728.SH', '20180103', 'open'), '分红指标')))
    def test_get_factor_dividend_exe(self, t_data, expect):
        """
        异常测试get_factor_dividend获取股票分红指标（缺少因子或者标的未空或者None的情况）
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd.get_factor_dividend(*t_data)
        assert expect in str(exe_info.value)

    @pytest.mark.parametrize('fill_na', (True, False))
    @pytest.mark.parametrize('t_factor', (['short_name', 'con_sector', 'listing_place'], 'listing_place'))
    @pytest.mark.parametrize('t_stock', (['600077.SH', '002236.SZ', '600373.SH', '688016.SH'],  '600373.SH'))
    def test_get_factor_newsmsg(self, t_stock, t_factor, fill_na):
        """
        测试get_factor_newsmsg获取股票最新信息
        :param t_stock:股票代码
        :param t_factor:因子
        :param fill_na:填充NAN
        :return:
        """
        result = self.sd.get_factor_newsmsg(t_stock, t_factor, fill_na=fill_na)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('t_data, expect', ((('', 'listing_place'), '股票不能'),
                                                (('600728.SH', None), '因子不能'),
                                                (('600728.SH', 'listing_place1'), '无此因子'),
                                                (('600728.SH', 'open'), '只支持')))
    def test_get_factor_newsmsg_exe(self, t_data, expect):
        """
        异常测试get_factor_newsmsg获取股票最新信息
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd.get_factor_newsmsg(*t_data)
        assert expect in str(exe_info.value)

    @pytest.mark.parametrize('fill_na', (True, False))
    @pytest.mark.parametrize('block_type', (2, 4))
    @pytest.mark.parametrize('stock_type', (0, 1, 2))
    @pytest.mark.parametrize('t_data', ((['603506', '601828', '600775'], ['20180102', '20180103'],
                                         ['rating_up_number7', 'report_number30']),
                                        (['603506'], ['20180102', '20180103'],
                                         ['rating_up_number7'])))
    def test_get_factor_conforecast(self, t_data, stock_type, block_type, fill_na):
        """
        测试get_factor_conforecast获取股票一致预期指标
        :param t_data:测试数据
        :param stock_type:证券代码对应的代码类型
        :param block_type:组合类型
        :param fill_na:是否填充NAN
        :return:
        """
        result = self.sd.get_factor_conforecast(*t_data, stock_type=stock_type,
                                                block_type=block_type, fill_na=fill_na)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('fill_na', (True, False))
    @pytest.mark.parametrize('t_factor', (['alpha1', 'alpha2', 'alpha120'], 'alpha1'))
    @pytest.mark.parametrize('t_date', (['20191112', '20191113'], '20191112'))
    @pytest.mark.parametrize('t_stock', (['601998.SH', '002007.SZ', '600369.SH', '601658.SH'],  '601658.SH'))
    def test_get_factor_alph191(self, t_stock, t_date, t_factor, fill_na):
        """
        测试get_factor_alph191获取alpha因子数据
        :param t_stock: 股票代码
        :param t_date: 日期
        :param t_factor: 因子
        :param fill_na: 填充NAN
        :return:
        """
        result = self.sd.get_factor_alph191(t_stock, t_date, t_factor, fill_na=fill_na)
        if fill_na is False and t_stock == '601658.SH':
            assert len(result) == 0
        else:
            assert len(result) > 0
            assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('t_data, expect', ((('601998.SH', ('20191112', '20191111'), 'alpha1'), '元组'),
                                                (('600728.SH', {'20191112'}, 'alpha1'), 'date_list'),
                                                (('600728.SH', '201911121', 'alpha1'), '格式'),
                                                (('', '20191112', 'alpha1'), '股票不能'),
                                                (('600728.SH', '20191112', None), '因子不能'),
                                                (('600728.SH', '20191112', '1alpha1'), '无此因子'),
                                                (('600728.SH', '20191112', 'open'), '只支持')))
    def test_get_factor_alph191_exe(self, t_data, expect):
        """
        异常测试get_factor_alph191获取alpha因子数据
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd.get_factor_alph191(*t_data)
        assert expect in str(exe_info.value)

    @pytest.mark.parametrize('fill_na', (True, False))
    @pytest.mark.parametrize('t_factor', (['barra_cne5_residualvolatility_dastd', 'barra_cne5_size'],
                                          'barra_cne5_residualvolatility_dastd'))
    @pytest.mark.parametrize('t_date', (['20191112', '20191113'], '20191112'))
    @pytest.mark.parametrize('t_stock', (['601998.SH', '002007.SZ', '600369.SH', '601658.SH'],  '601658.SH'))
    def test_get_factor_barra(self, t_stock, t_date, t_factor, fill_na):
        """
        测试get_factor_barra获取barra因子数据
        :param t_stock: 股票代码
        :param t_date: 日期
        :param t_factor: 因子
        :param fill_na: 填充NAN
        :return:
        """
        result = self.sd.get_factor_barra(t_stock, t_date, t_factor, fill_na=fill_na)
        if fill_na is False and t_stock == '601658.SH' and xquantEnv == 0:
            assert len(result) == 0
        else:
            assert len(result) > 0
            assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('t_data, expect', ((('601998.SH', ('20191112', '20191111'), 'barra_cne5_size'), '元组'),
                                                (('600728.SH', {'20191112'}, 'barra_cne5_size'), 'date_list'),
                                                (('600728.SH', '201911121', 'barra_cne5_size'), '格式'),
                                                (('600728.SH', '20191112', '1alpha1'), '无此因子'),
                                                (('600728.SH', '20191112', 'open'), '只支持')))
    def test_get_factor_barra_exe(self, t_data, expect):
        """
        异常测试get_factor_barra获取barra因子数据
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd.get_factor_barra(*t_data)
        assert expect in str(exe_info.value)

    @pytest.mark.parametrize('fill_na', (True, False))
    @pytest.mark.parametrize('t_factor', (['coskew', 'ema_crossover', 'tskew'], 'tskew'))
    @pytest.mark.parametrize('t_date', (['20191112', '20191113'], '20191112'))
    @pytest.mark.parametrize('t_stock', (['601998.SH', '002007.SZ', '600369.SH', '601658.SH'],  '601658.SH'))
    def test_get_factor_technical_analysis(self, t_stock, t_date, t_factor, fill_na):
        """
        测试get_factor_technical_analysis获取技术面因子数据
        :param t_stock: 股票代码
        :param t_date: 日期
        :param t_factor: 因子
        :param fill_na: 填充NAN
        :return:
        """
        result = self.sd.get_factor_technical_analysis(t_stock, t_date, t_factor, fill_na=fill_na)
        if fill_na is False and t_stock == '601658.SH':
            assert len(result) == 0
        else:
            assert len(result) > 0
            assert isinstance(result, pd.DataFrame)
            assert 'mddate' in str(result.index) and 'stock' in str(result.index)

    @pytest.mark.parametrize('t_data, expect', ((('601998.SH', ('20191112', '20191111'), 'tskew'), '元组'),
                                                (('600728.SH', {'20191112'}, 'tskew'), 'date_list'),
                                                (('600728.SH', '201911121', 'tskew'), '格式'),
                                                (('600728.SH', '20191112', '1alpha1'), '无此因子'),
                                                (('600728.SH', '20191112', 'open'), '只支持')))
    def test_get_factor_technical_analysis_exe(self, t_data, expect):
        """
        异常测试get_factor_technical_analysis获取技术面因子数据
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd.get_factor_technical_analysis(*t_data)
        assert expect in str(exe_info.value)

    @pytest.mark.parametrize('pdatetype', ('ACCOUNTINGDAY', 'PUBLISHDAY', 'TTM'))
    @pytest.mark.parametrize('factor_list', (['net_profit_excl_min_int_inc', 'oper_rev'],
                                             ['net_profit_excl_min_int_inc']))
    @pytest.mark.parametrize('date_list', (["20190630", "20190701", "20190702"], ["20190630"]))
    @pytest.mark.parametrize('trading_codes', (['000001.SZ', '000002.SZ', '000004.SZ'], ['000001.SZ']))
    def test_get_finicial_cross_section_data(self, trading_codes, date_list, factor_list, pdatetype):
        """
        测试get_finicial_cross_section_data查询财务因子数据
        :param trading_codes: 股票代码
        :param date_list: 数据日期
        :param factor_list: 因子名称
        :param pdatetype:匹配日期类型
        :return:
        """
        result = self.sd.get_finicial_cross_section_data(trading_codes, date_list, factor_list,
                                                         publishDateType=pdatetype)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)
        assert 'mddate' in str(result.index) and 'stock' in str(result.index)


if __name__ == "__main__":
    pytest.main(["-v"])
