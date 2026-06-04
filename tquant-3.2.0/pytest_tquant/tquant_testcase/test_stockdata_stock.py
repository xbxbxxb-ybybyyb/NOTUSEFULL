import os
from tquant.stock_data import StockData
from tquant.basic_data import BasicData
import pytest
import pandas as pd


class TestStockData(object):
    """
    测试StockData股票数据接口
    """
    @classmethod
    def setup_class(cls):
        cls.sd1 = StockData(data_source="finchina", use_cache=False)
        cls.bd = BasicData()

    @pytest.mark.parametrize('trading_codes', [['300707.SZ', '300705.SZ', '601658.SH'], '300726.SZ'])
    @pytest.mark.parametrize('date_list', [['20180102', '20180103'], '20180102', ('20180102', '20180105')])
    @pytest.mark.parametrize('factor_list', [['pre_close', 'open', 'high'], 'high'])
    @pytest.mark.parametrize('fill_na', [None, True, False])
    def test_get_factor_price_daily(self, trading_codes, date_list, factor_list, fill_na):
        """
        测试get_factor_price_daily日行情
        :param trading_codes:股票代码
        :param date_list:日期
        :param factor_list:因子
        :param fill_na:填充NAN
        :return:
        """
        if fill_na is None:
            result = self.sd1.get_factor_price_daily(trading_codes, date_list, factor_list)
        else:
            result = self.sd1.get_factor_price_daily(trading_codes, date_list, factor_list, fill_na=fill_na)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('trading_codes', [['300707.SZ'], []])
    @pytest.mark.parametrize('date_list', [('20180103', '20180102'), {'20180103', '20180102'}, '201801031'])
    @pytest.mark.parametrize('factor_list', ['high', None, 'ev'])
    def test_get_factor_price_daily_exe(self, trading_codes, date_list, factor_list):
        with pytest.raises(Exception) as exe_info:
            self.sd1.get_factor_price_daily(trading_codes, date_list, factor_list)
        if type(date_list) not in [list, str, tuple]:
            assert "【date_list】参数为str或list类型，请重新输入！" in str(exe_info.value)
        else:
            if type(date_list) in [list, tuple] and date_list[0] > date_list[-1]:
                assert "开始日期大于结束日期，请重新输入！" in str(exe_info.value)
            elif date_list == '201801031':
                assert "【date_list】的日期为YYYYMMDD格式" in str(exe_info.value)
            else:
                if trading_codes is []:
                    assert "股票不能为空或None！" in str(exe_info.value)
                elif factor_list in [None, 'ev']:
                    if factor_list is None:
                        assert "因子不能为空或None！" in str(exe_info.value)
                    else:
                        assert "只支持查询日行情因子数据！" in str(exe_info.value)

    @pytest.mark.parametrize('trading_codes', (['002302.SZ', '002372.SZ', '601658.SH'], '002302.SZ'))
    @pytest.mark.parametrize('date_list', [['20180102', '20180103'], '20180102', ('20180102', '20180105')])
    @pytest.mark.parametrize('factor_list', [['ev', 'mkt_cap_ard', 'pe_ttm', 'ev1', 'ev2'], 'mkt_cap_ard'])
    @pytest.mark.parametrize('fill_na', [None, True, False])
    @pytest.mark.parametrize('sort_option', [None, True, False])
    def test_get_factor_valuation_metrics(self, trading_codes, date_list, factor_list, fill_na, sort_option):
        """
        测试get_factor_valuation_metrics获取股票估值指标
        :param trading_codes:股票代码
        :param date_list:日期
        :param factor_list:因子
        :param fill_na:填充NAN
        :return:
        """
        if fill_na is None:
            if sort_option is None:
                result = self.sd1.get_factor_valuation_metrics(trading_codes, date_list, factor_list)
            else:
                result = self.sd1.get_factor_valuation_metrics(trading_codes, date_list, factor_list,
                                                               sort_option=sort_option)
        else:
            if sort_option is None:
                result = self.sd1.get_factor_valuation_metrics(trading_codes, date_list, factor_list,
                                                               fill_na=fill_na)
            else:
                result = self.sd1.get_factor_valuation_metrics(trading_codes, date_list, factor_list,
                                                               fill_na=fill_na, sort_option=sort_option)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('trading_codes', [['002302.SZ'], []])
    @pytest.mark.parametrize('date_list', [('20180103', '20180102'), {'20180103', '20180102'}, '201801031'])
    @pytest.mark.parametrize('factor_list', ['open', None, 'ev'])
    def test_get_factor_valuation_metrics_exe(self, trading_codes, date_list, factor_list):
        with pytest.raises(Exception) as exe_info:
            self.sd1.get_factor_valuation_metrics(trading_codes, date_list, factor_list)
        if type(date_list) not in [list, str, tuple]:
            assert "【date_list】参数为str或list类型，请重新输入！" in str(exe_info.value)
        else:
            if type(date_list) in [list, tuple] and date_list[0] > date_list[-1]:
                assert "开始日期大于结束日期，请重新输入！" in str(exe_info.value)
            elif date_list == '201801031':
                assert "【date_list】的日期为YYYYMMDD格式" in str(exe_info.value)
            else:
                if trading_codes is []:
                    assert "股票不能为空或None！" in str(exe_info.value)
                else:
                    if factor_list is None:
                        assert "因子不能为空或None！" in str(exe_info.value)
                    elif factor_list is 'ev':
                        assert "只支持查询日行情因子数据！" in str(exe_info.value)
                    elif factor_list is 'open':
                        assert "只支持查询估值指标与风险指标的因子数据！" in str(exe_info.value)

    @pytest.mark.parametrize('trading_codes', [['600373.SH', '600395.SH', '601658.SH'], ['600373.SH']])
    @pytest.mark.parametrize('date_list', [['20180105', '20180112'], '20180112', ('20180105', '20180112')])
    @pytest.mark.parametrize('factor_list', [['annualyeild_100w', 'beta_100w', 'beta_60m'], 'annualyeild_100w'])
    @pytest.mark.parametrize('fill_na', [None, True, False])
    @pytest.mark.parametrize('sort_option', [None, True, False])
    def test_get_factor_risk_analysis(self, trading_codes, date_list, factor_list, fill_na, sort_option):
        """
        测试get_factor_risk_analysis获取股票风险指标
        :param trading_codes:股票代码
        :param date_list:日期
        :param factor_list:因子
        :param fill_na:填充NAN
        :return:
        """
        if fill_na is None:
            if sort_option is None:
                result = self.sd1.get_factor_risk_analysis(trading_codes, date_list, factor_list)
            else:
                result = self.sd1.get_factor_risk_analysis(trading_codes, date_list, factor_list,
                                                           sort_option=sort_option)
        else:
            if sort_option is None:
                result = self.sd1.get_factor_risk_analysis(trading_codes, date_list, factor_list,
                                                           fill_na=fill_na)
            else:
                result = self.sd1.get_factor_risk_analysis(trading_codes, date_list, factor_list,
                                                           fill_na=fill_na, sort_option=sort_option)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('trading_codes', [['600395.SH'], []])
    @pytest.mark.parametrize('date_list', [('20180103', '20180102'), {'20180103', '20180102'}, '201801031'])
    @pytest.mark.parametrize('factor_list', ['open', None, 'beta_100w'])
    def test_get_factor_risk_analysis_exe(self, trading_codes, date_list, factor_list):
        with pytest.raises(Exception) as exe_info:
            self.sd1.get_factor_risk_analysis(trading_codes, date_list, factor_list)
        if type(date_list) not in [list, str, tuple]:
            assert "【date_list】参数为str或list类型，请重新输入！" in str(exe_info.value)
        else:
            if type(date_list) in [list, tuple] and date_list[0] > date_list[-1]:
                assert "开始日期大于结束日期，请重新输入！" in str(exe_info.value)
            elif date_list == '201801031':
                assert "【date_list】的日期为YYYYMMDD格式" in str(exe_info.value)
            else:
                if trading_codes is []:
                    assert "股票不能为空或None！" in str(exe_info.value)
                else:
                    if factor_list is None:
                        assert "因子不能为空或None！" in str(exe_info.value)
                    elif factor_list is 'ev':
                        assert "只支持查询日行情因子数据！" in str(exe_info.value)

    @pytest.mark.parametrize('date_list', [['20180331', '20180630'], '20180630', ('20180331', '20180630')])
    @pytest.mark.parametrize('trading_codes', [['002314.SZ', '600422.SH', '601658.SH'], '002314.SZ'])
    @pytest.mark.parametrize('factor_list', [['eps_basic', 'eps_diluted', 'roa_ttm'], 'eps_diluted',
                                             ["profit_ttm", "grossmargin_ttm", "or_ttm"]])
    @pytest.mark.parametrize('fill_na', [None, True, False])
    @pytest.mark.parametrize('sort_option', [None, True, False])
    def test_get_factor_financial_analysis(self, trading_codes, date_list, factor_list, fill_na, sort_option):
        if fill_na is None:
            if sort_option is None:
                result = self.sd1.get_factor_financial_analysis(trading_codes, date_list, factor_list)
            else:
                result = self.sd1.get_factor_financial_analysis(trading_codes, date_list, factor_list,
                                                                sort_option=sort_option)
        else:
            if sort_option is None:
                result = self.sd1.get_factor_financial_analysis(trading_codes, date_list, factor_list,
                                                                fill_na=fill_na)
            else:
                result = self.sd1.get_factor_financial_analysis(trading_codes, date_list, factor_list,
                                                                fill_na=fill_na, sort_option=sort_option)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('trading_codes', [['600422.SH'], []])
    @pytest.mark.parametrize('date_list', [('20180103', '20180102'), {'20180103', '20180102'}, '201801031'])
    @pytest.mark.parametrize('factor_list', ['open', None, 'eps_diluted'])
    def test_get_factor_financial_analysis_exe(self, trading_codes, date_list, factor_list):
        """
        异常测试get_factor_financial_analysis获取股票财务分析指标
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd1.get_factor_financial_analysis(trading_codes, date_list, factor_list)
        if type(date_list) not in [list, str, tuple]:
            assert "【date_list】参数为str或list类型，请重新输入！" in str(exe_info.value)
        else:
            if type(date_list) in [list, tuple] and date_list[0] > date_list[-1]:
                assert "开始日期大于结束日期，请重新输入！" in str(exe_info.value)
            elif date_list == '201801031':
                assert "【date_list】的日期为YYYYMMDD格式" in str(exe_info.value)
            else:
                if trading_codes is []:
                    assert "股票不能为空或None！" in str(exe_info.value)
                else:
                    if factor_list is None:
                        assert "因子不能为空或None！" in str(exe_info.value)
                    elif factor_list is 'open':
                        assert "只支持查询财务分析因子数据！" in str(exe_info.value)

    @pytest.mark.parametrize('trading_codes', [['300397.SZ', '002594.SZ', '601658.SH'], '300397.SZ'])
    @pytest.mark.parametrize('date_list', [['20180331', '20180630'], '20180630', ('20180331', '20180630')])
    @pytest.mark.parametrize('factor_list', [['monetary_cap', 'notes_rcv', 'dvd_rcv'], 'tot_oper_rev', 'rdexpense'])
    @pytest.mark.parametrize('statement_type', ['102', '108'])
    @pytest.mark.parametrize('fill_na', [None, True, False])
    @pytest.mark.parametrize('sort_option', [None, True, False])
    def test_get_factor_financial_report(self, trading_codes, date_list, factor_list, statement_type, fill_na, sort_option):
        """
        测试get_factor_financial_report获取股票财务报表指标
        :param trading_codes:股票代码
        :param date_list:日期
        :param factor_list:因子
        :param fill_na:填充NAN
        :return:
        """
        if fill_na is None:
            if sort_option is None:
                result = self.sd1.get_factor_financial_report(trading_codes, date_list, factor_list,
                                                              statement_type=statement_type)
            else:
                result = self.sd1.get_factor_financial_report(trading_codes, date_list, factor_list,
                                                              statement_type=statement_type, sort_option=sort_option)
        else:
            if sort_option is None:
                result = self.sd1.get_factor_financial_report(trading_codes, date_list, factor_list,
                                                                statement_type=statement_type, fill_na=fill_na)
            else:
                result = self.sd1.get_factor_financial_report(trading_codes, date_list, factor_list,
                                                              statement_type=statement_type, fill_na=fill_na,
                                                              sort_option=sort_option)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('trading_codes', ['300397.SZ', []])
    @pytest.mark.parametrize('date_list', [('20180103', '20180102'), {'20180103', '20180102'}, '201801031'])
    @pytest.mark.parametrize('factor_list', ['open', None, 'dvd_rcv'])
    def test_get_factor_financial_report_exe(self, trading_codes, date_list, factor_list):
        """
        异常测试get_factor_financial_report获取股票财务报表指标
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd1.get_factor_financial_report(trading_codes, date_list, factor_list)
        if type(date_list) not in [list, str, tuple]:
            assert "【date_list】参数为str或list类型，请重新输入！" in str(exe_info.value)
        else:
            if type(date_list) in [list, tuple] and date_list[0] > date_list[-1]:
                assert "开始日期大于结束日期，请重新输入！" in str(exe_info.value)
            elif date_list == '201801031':
                assert "【date_list】的日期为YYYYMMDD格式" in str(exe_info.value)
            else:
                if trading_codes is []:
                    assert "股票不能为空或None！" in str(exe_info.value)
                else:
                    if factor_list is None:
                        assert "因子不能为空或None！" in str(exe_info.value)
                    elif factor_list is 'open':
                        assert " 只支持查询财务报告的因子数据！" in str(exe_info.value)

    @pytest.mark.parametrize('trading_codes', [['600728.SH', '600340.SH', '002016.SZ'],  '002016.SZ'])
    @pytest.mark.parametrize('date_list', [['20180630', '20190930'], '20180630'])
    @pytest.mark.parametrize('factor_list', [['per_div_trans', 'per_cashpaidbeforetax', 'ex_dt', 'dvd_payout_dt'],
                                             'dvd_payout_dt'])
    @pytest.mark.parametrize('fill_na', [None, True, False])
    @pytest.mark.parametrize('sort_option', [None, True, False])
    def test_get_factor_dividend(self, trading_codes, date_list, factor_list, fill_na, sort_option):
        if fill_na is None:
            if sort_option is None:
                result = self.sd1.get_factor_dividend(trading_codes, date_list, factor_list)
            else:
                result = self.sd1.get_factor_dividend(trading_codes, date_list, factor_list,
                                                                sort_option=sort_option)
        else:
            if sort_option is None:
                result = self.sd1.get_factor_dividend(trading_codes, date_list, factor_list,
                                                                fill_na=fill_na)
            else:
                result = self.sd1.get_factor_dividend(trading_codes, date_list, factor_list,
                                                                fill_na=fill_na, sort_option=sort_option)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    """
    @pytest.mark.parametrize('t_data, expect', [(('600728.SH', ('20180103', '20180106'), 'ex_dt'), 'date_list'),
                                                (('600728.SH', '201801031', 'ex_dt'), '格式'),
                                                (('600728.SH', '20180103', 'open'), '分红指标')])
    """

    @pytest.mark.parametrize('trading_codes', ['600728.SZ', []])
    @pytest.mark.parametrize('date_list', [['20180103', '20180104'], ('20180103', '20180102'), {'20180103', '20180102'}, '201801031'])
    @pytest.mark.parametrize('factor_list', ['open', None, 'ex_dt'])
    def test_get_factor_dividend_exe(self, trading_codes, date_list, factor_list):
        """
        异常测试get_factor_dividend获取股票分红指标（缺少因子或者标的未空或者None的情况）
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        try:
            self.sd1.get_factor_dividend(trading_codes, date_list, factor_list)
        except Exception as exe_info:
            if type(date_list) not in [list, str]:
                assert "【date_list】参数为str或list类型，请重新输入！" in str(exe_info)
            else:
                if type(date_list) in [list, tuple] and date_list[0] > date_list[-1]:
                    assert "开始日期大于结束日期，请重新输入！" in str(exe_info)
                elif date_list == '201801031':
                    assert "【date_list】的日期为YYYYMMDD格式" in str(exe_info)
                else:
                    if trading_codes is []:
                        assert "股票不能为空或None！" in str(exe_info)
                    else:
                        if factor_list is None:
                            assert "'NoneType' object is not iterable" in str(exe_info)
                        elif factor_list is 'open':
                            assert "因子 open 不属于分红指标，请重新输入！" in str(exe_info)
        else:
            pass


    @pytest.mark.parametrize('fill_na', [True, False])
    @pytest.mark.parametrize('t_factor', [['short_name', 'con_sector', 'listing_place'], 'listing_place'])
    @pytest.mark.parametrize('t_stock', [['600077.SH', '002236.SZ', '600373.SH', '688016.SH'],  ['600373.SH']])
    def test_get_factor_newsmsg(self, t_stock, t_factor, fill_na):
        """
        测试get_factor_newsmsg获取股票最新信息
        :param t_stock:股票代码
        :param t_factor:因子
        :param fill_na:填充NAN
        :return:
        """
        result = self.sd1.get_factor_newsmsg(t_stock, t_factor, fill_na=fill_na)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('t_data, expect', [(('', 'listing_place'), '股票不能'),
                                                (('600728.SH', None), '因子不能'),
                                                (('600728.SH', 'listing_place1'), '无此因子'),
                                                (('600728.SH', 'open'), '只支持')])
    def test_get_factor_newsmsg_exe(self, t_data, expect):
        """
        异常测试get_factor_newsmsg获取股票最新信息
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd1.get_factor_newsmsg(*t_data)
        assert expect in str(exe_info.value)

    @pytest.mark.parametrize('fill_na', [True, False])
    @pytest.mark.parametrize('block_type', [2, 4])
    @pytest.mark.parametrize('stock_type', [0, 1, 2])
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
        result = self.sd1.get_factor_conforecast(*t_data, stock_type=stock_type,
                                                block_type=block_type, fill_na=fill_na)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('fill_na', [True, False])
    @pytest.mark.parametrize('t_factor', [['alpha1', 'alpha2', 'alpha120'], 'alpha1'])
    @pytest.mark.parametrize('t_date', [['20191112', '20191113'], '20191112'])
    @pytest.mark.parametrize('t_stock', [['601998.SH', '002007.SZ', '600369.SH', '601658.SH'],  '601658.SH'])
    def test_get_factor_alpha191(self, t_stock, t_date, t_factor, fill_na):
        """
        测试get_factor_alpha191获取alpha因子数据
        :param t_stock: 股票代码
        :param t_date: 日期
        :param t_factor: 因子
        :param fill_na: 填充NAN
        :return:
        """
        result = self.sd1.get_factor_alpha191(t_stock, t_date, t_factor, fill_na=fill_na)
        if fill_na is False and t_stock == '601658.SH':
            assert len(result) == 0
        else:
            assert len(result) > 0
            assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('t_data, expect', [(('601998.SH', ('20191112', '20191111'), 'alpha1'), '元组'),
                                                (('600728.SH', {'20191112'}, 'alpha1'), 'date_list'),
                                                (('600728.SH', '201911121', 'alpha1'), '格式'),
                                                (('', '20191112', 'alpha1'), '股票不能'),
                                                (('600728.SH', '20191112', None), '因子不能'),
                                                (('600728.SH', '20191112', '1alpha1'), '无此因子'),
                                                (('600728.SH', '20191112', 'open'), '只支持')])
    def test_get_factor_alpha191_exe(self, t_data, expect):
        """
        异常测试get_factor_alpha191获取alpha因子数据
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd1.get_factor_alpha191(*t_data)
        assert expect in str(exe_info.value)

    @pytest.mark.parametrize('fill_na', [True, False])
    @pytest.mark.parametrize('t_factor', [['barra_cne5_residualvolatility_dastd', 'barra_cne5_size'],
                                          'barra_cne5_residualvolatility_dastd'])
    @pytest.mark.parametrize('t_date', [['20191112', '20191113'], '20191112'])
    @pytest.mark.parametrize('t_stock', [['601998.SH', '002007.SZ', '600369.SH', '601658.SH'],  '601658.SH'])
    def test_get_factor_barra(self, t_stock, t_date, t_factor, fill_na):
        """
        测试get_factor_barra获取barra因子数据
        :param t_stock: 股票代码
        :param t_date: 日期
        :param t_factor: 因子
        :param fill_na: 填充NAN
        :return:
        """
        result = self.sd1.get_factor_barra(t_stock, t_date, t_factor, fill_na=fill_na)
        assert len(result) > 0

    @pytest.mark.parametrize('t_data, expect', [(('601998.SH', ('20191112', '20191111'), 'barra_cne5_size'), '元组'),
                                                (('600728.SH', {'20191112'}, 'barra_cne5_size'), 'date_list'),
                                                (('600728.SH', '201911121', 'barra_cne5_size'), '格式'),
                                                (('600728.SH', '20191112', '1alpha1'), '无此因子'),
                                                (('600728.SH', '20191112', 'open'), '只支持')])
    def test_get_factor_barra_exe(self, t_data, expect):
        """
        异常测试get_factor_barra获取barra因子数据
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd1.get_factor_barra(*t_data)
        assert expect in str(exe_info.value)

    @pytest.mark.parametrize('fill_na', [True, False])
    @pytest.mark.parametrize('t_factor', [['coskew', 'ema_crossover', 'tskew'], 'tskew'])
    @pytest.mark.parametrize('t_date', [['20191112', '20191113'], '20191112'])
    @pytest.mark.parametrize('t_stock', [['601998.SH', '002007.SZ', '600369.SH', '601658.SH'],  '601658.SH'])
    def test_get_factor_technical_analysis(self, t_stock, t_date, t_factor, fill_na):
        """
        测试get_factor_technical_analysis获取技术面因子数据
        :param t_stock: 股票代码
        :param t_date: 日期
        :param t_factor: 因子
        :param fill_na: 填充NAN
        :return:
        """
        result = self.sd1.get_factor_technical_analysis(t_stock, t_date, t_factor, fill_na=fill_na)
        if fill_na is False and t_stock == '601658.SH':
            assert len(result) == 0
        else:
            assert len(result) > 0
            assert isinstance(result, pd.DataFrame)
            assert 'mddate' in str(result.index) and 'stock' in str(result.index)

    @pytest.mark.parametrize('t_data, expect', [(('601998.SH', ('20191112', '20191111'), 'tskew'), '元组'),
                                                (('600728.SH', {'20191112'}, 'tskew'), 'date_list'),
                                                (('600728.SH', '201911121', 'tskew'), '格式'),
                                                (('600728.SH', '20191112', '1alpha1'), '无此因子'),
                                                (('600728.SH', '20191112', 'open'), '只支持')])
    def test_get_factor_technical_analysis_exe(self, t_data, expect):
        """
        异常测试get_factor_technical_analysis获取技术面因子数据
        :param t_data:测试数据
        :param expect:期望现象
        :return:
        """
        with pytest.raises(Exception) as exe_info:
            self.sd1.get_factor_technical_analysis(*t_data)
        assert expect in str(exe_info.value)

    @pytest.mark.parametrize('pdatetype', ['ACCOUNTINGDAY', 'PUBLISHDAY', 'TTM'])
    @pytest.mark.parametrize('factor_list', [['net_profit_excl_min_int_inc', 'oper_rev'],
                                             ['net_profit_excl_min_int_inc']])
    @pytest.mark.parametrize('date_list', [["20190630", "20190701", "20190702"], ["20190630"]])
    @pytest.mark.parametrize('trading_codes', [['000001.SZ', '000002.SZ', '000004.SZ'], ['000001.SZ']])
    def test_get_finicial_cross_section_data(self, trading_codes, date_list, factor_list, pdatetype):
        """
        测试get_finicial_cross_section_data查询财务因子数据
        :param trading_codes: 股票代码
        :param date_list: 数据日期
        :param factor_list: 因子名称
        :param pdatetype:匹配日期类型
        :return:
        """
        result = self.sd1.get_finicial_cross_section_data(trading_codes, date_list, factor_list,
                                                         publishDateType=pdatetype)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)
        assert 'mddate' in str(result.index) and 'stock' in str(result.index)

    @pytest.mark.skipif(os.environ.get("DSWMAP_envTag") != 'prd', reason="生产环境条件下测试")
    @pytest.mark.parametrize('stock_list', [[]])
    @pytest.mark.parametrize('date_start, date_end', [("20201220", "20210120")])
    @pytest.mark.parametrize('factor_list, table_name', [([["S_EST_EPSINSTNUM", "S_EST_ROEINSTNUM", "S_EST_MAINBUSINCINSTNUM",
                                                            "S_EST_NETPROFITINSTNUM", "S_EST_CPSINSTNUM", "S_EST_DPSINSTNUM",
                                                            "S_EST_BPSINSTNUM", "S_EST_EBITINSTNUM", "S_EST_EBITDAINSTNUM",
                                                            "MAIN_BUS_INC_UPGRADE", "MAIN_BUS_INC_DOWNGRADE", "MAIN_BUS_INC_MAINTAIN",
                                                            "NET_PROFIT_UPGRADE", "NET_PROFIT_DOWNGRADE", "NET_PROFIT_MAINTAIN"],
                                                           ["EST_EPS", "EST_ROE", "NET_PROFIT", "EST_OPER_REVENUE", "EST_CFPS",
                                                            "EST_DPS", "EST_BPS", "EST_EBIT", "EST_EBITDA", "EST_TOTAL_PROFIT",
                                                            "EST_OPER_PROFIT"],
                                                           ["S_WRATING_AVG", "S_WRATING_INSTNUM", "S_WRATING_UPGRADE",
                                                            "S_WRATING_DOWNGRADE", "S_WRATING_MAINTAIN", "S_WRATING_NUMOFBUY",
                                                            "S_WRATING_NUMOFOUTPERFORM", "S_WRATING_NUMOFHOLD", "S_WRATING_NUMOFUNDERPERFORM",
                                                            "S_WRATING_NUMOFSELL", "S_EST_PRICE", "S_EST_PRICEINSTNUM"]], None)])
    @pytest.mark.parametrize('ROLLING_TYPE', [['CAGR', 'FY2'], [], ['CAGR']])
    @pytest.mark.parametrize('CONSEN_DATA_CYCLE_TYP', [["263003000"]])
    @pytest.mark.parametrize('S_EST_YEARTYPE', [["FY2"]])
    @pytest.mark.parametrize('S_WRATING_CYCLE', [["263003000"]])
    def test_get_source_factor_value(self, stock_list, date_start, date_end, factor_list, ROLLING_TYPE,
                                             CONSEN_DATA_CYCLE_TYP, S_EST_YEARTYPE, S_WRATING_CYCLE, table_name):
        date_list = self.bd.get_trading_day(date_start, date_end)

        for factors in factor_list:
            df = self.sd1.get_source_factor_value(stock_list, date_list, factors, ROLLING_TYPE=ROLLING_TYPE,
                                                  CONSEN_DATA_CYCLE_TYP=CONSEN_DATA_CYCLE_TYP, S_EST_YEARTYPE=S_EST_YEARTYPE,
                                                  S_WRATING_CYCLE=S_WRATING_CYCLE, table_name=table_name)
            assert len(df) > 0
            assert isinstance(df, pd.DataFrame)

    @pytest.mark.skipif(os.environ.get("DSWMAP_envTag") != 'prd', reason="生产环境条件下测试")
    @pytest.mark.parametrize('factor_lists, table_name', [([['ANN_DATE', 'F_PRT_ENDDATE']], 'ChinaMutualFundStockPortfolio'),
                                                          ([['ANN_DATE', 'PRICE_DATE']], 'ChinaMutualFundNAV'),
                                                          ([['ANN_DT', 'S_SURVEYDATE', 'S_SURVEYTIME']], 'AshareISActivity'),
                                                          ([['F_PRT_ENDDATE', 'F_ANN_DATE']], 'ChinaMutualFundAssetPortfolio'),
                                                          ([['F_ISSUE_DATE', 'F_INFO_SETUPDATE', 'F_INFO_MATURITYDATE',
                                                             'F_INFO_LISTDATE', 'F_PCH_STARTDATE', 'F_REDM_STARTDATE',
                                                             'F_ISSUE_STARTDATEIND', 'F_ISSUE_ENDDATEIND']],
                                                           'ChinaMutualFundIssue'),
                                                          ([['RATING_DT'], ['END_DT', 'COLLECT_DT']], 'AShareIndusRating'),
                                                          ([['EST_DT', 'EST_MAIN_BUS_INC'], ['REPORTING_PERIOD', 'S_EST_ENDDATE',
                                                             'COLLECT_TIME', 'FIRST_OPTIME', 'EST_MAIN_BUS_INC']], 'AShareEarningEst'),
                                                          ([['EST_DT', 'EST_REPORT_DT']], 'AIndexConsensusData'),
                                                          ([['FINANCIAL_TRADE_DT', 'TOT_SHR_TODAY']], 'HKShareEODDerivativeIndex'),
                                                          ([['S_CON_INDATE', 'S_INFO_WINDCODE'], ['S_CON_OUTDATE', 'S_CON_WINDCODE']],
                                                           'AIndexMembers'),
                                                          ([['S_ENDDATE', 'S_PLEDGE_NUM']], 'ASharePledgeproportion'),
                                                          ([['CHANGE_DATE'], ['CHANGE_DATE', 'F_INFO_WINDCODE']], 'ChinaMutualFundShare'),
                                                          ([['S_EST_ESTNEWTIME_INST', 'S_RATING_VALIDENDDT']],
                                                           'AShareStockRating'),
                                                          ([['TRADE_DT'], ['S_DQ_LOW', 'S_DQ_OPEN', 'S_INFO_WINDCODE']],
                                                           'HKshareEODPrices'),
                                                          ([['S_INFO_WINDCODE', 'TRADE_DT', 'S_DQ_LOW', 'S_DQ_OPEN', 'TRADES_COUNT']],
                                                           'ChinaClosedFundEODPrice'),
                                                          ([['TRADE_DT']], 'CBONDIBRMBMONDMARQUOTATION'),
                                                          ([['S_EVENT_HAPDATE', 'S_EVENT_CONTENT']], 'AShareMajorEvent'),
                                                          ([['TRADE_DT', 'S_INFO_WINDCODE', 'MARGINRATIO']],
                                                           'CFUTURESMARGINRATIO'),
                                                          ([['TRADE_DT','S_INFO_WINDCODE', 'CB_ANAL_PTM']],'CCbondValuation'),
                                                          ([['S_INFO_WINDCODE','S_INFO_ENDDATE','B_INFO_ANNOUNCEMENTDATE']],'CBONDCONVPRICE')
                                                         ])
    @pytest.mark.parametrize('date_start, date_end', [('20210820', '20210825')])
    def test_get_source_table_value_day1(self, factor_lists, table_name, date_start, date_end):
        date_list = self.bd.get_trading_day(date_start, date_end)
        for factor_list in factor_lists:
            df = self.sd1.get_source_table_value(table_name, factor_list, date_list)
            assert len(df) > 0
            assert isinstance(df, pd.DataFrame)

    @pytest.mark.skipif(os.environ.get("DSWMAP_envTag") != 'prd', reason="生产环境条件下测试")
    @pytest.mark.parametrize('factor_list', [['S_INFO_WINDCODE', 'TRADE_DT', 'S_DQ_LOW', 'S_DQ_OPEN', 'TRADES_COUNT']])
    @pytest.mark.parametrize('table_name', ['ChinaClosedFundEODPrice'])
    @pytest.mark.parametrize('date_start, date_end', [('20210820', '20210825')])
    @pytest.mark.parametrize('S_DQ_LOW', [['<1', '>2'], ['>1', '<2']])
    @pytest.mark.parametrize('TRADES_COUNT', ['is null', 'is not null', [24, 12, 2]])
    def test_get_source_table_value_day2(self, factor_list, table_name, date_start, date_end, S_DQ_LOW, TRADES_COUNT):
        date_list = self.bd.get_trading_day(date_start, date_end)
        if S_DQ_LOW is ['>1', '<2']:
            df = self.sd1.get_source_table_value(table_name, factor_list, date_list,
                                                 S_DQ_LOW=S_DQ_LOW, TRADES_COUNT=TRADES_COUNT)
        else:
            df = self.sd1.get_source_table_value(table_name, factor_list, date_list,
                                                 S_DQ_LOW=S_DQ_LOW, OR='S_DQ_LOW')
        assert len(df) > 0
        assert isinstance(df, pd.DataFrame)

    @pytest.mark.skipif(os.environ.get("DSWMAP_envTag") != 'prd', reason="生产环境条件下测试")
    @pytest.mark.parametrize('factor_lists, table_name', [([['ANN_DT', 'REPORT_PERIOD']], 'AshareTaxespayable'),
                                                          ([['DEADLINE', 'ANN_DATE']], 'AshareGuaranteestatistics'),
                                                          ([['PRICE_DATE', 'F_NAV_UNIT']], 'AEquFroPleInfoRepperend'),
                                                          ([['S_INFO_COMPCODE'], ['STATEMENT_TYPE', 'OPDATE']], 'Asharenonprofitloss'),
                                                          ([['S_REPORT_PERIOD', 'S_INFO_COMPCODE', 'S_SEGMENT_SALES']],
                                                           'CBONDSALESSEGMENT'),
                                                          ([['REPORT_PERIOD']], 'CBONDINVENTORYDETAILS')
                                                         ])
    @pytest.mark.parametrize('date_start, date_end', [('20210520', '20210825')])
    def test_get_source_table_value_quarter(self, factor_lists, table_name, date_start, date_end):
        date_list = self.bd.get_trading_day(date_start, date_end)
        for factor_list in factor_lists:
            if table_name is 'Asharenonprofitloss':
                df = self.sd1.get_source_table_value(table_name, factor_list, date_list, OPDATE=">20190620110318")
            else:
                df = self.sd1.get_source_table_value(table_name, factor_list, date_list)
            assert len(df) > 0
            assert isinstance(df, pd.DataFrame)

    @pytest.mark.skipif(os.environ.get("DSWMAP_envTag") != 'prd', reason="生产环境条件下测试")
    @pytest.mark.parametrize('factor_lists, table_name', [([['ENTRYDATE'], ['STATUS']], 'CHANGE_EVENT'),
                                                          ([['CURRENT_CREATE_DATE'], ['TMSTAMP', 'ENTRYDATE']], 'CMB_REPORT_SCORE_ADJUST'),
                                                          ([['create_date'], ['into_date', 'EntryDate', 'EntryTime']],
                                                           'CMB_REPORT_RESEARCH'),
                                                          ([['EntryDate'], ['EntryTime', 'time_year']], 'CMB_REPORT_SUBTABLE'),
                                                          ([['create_date'], ['into_date', 'EntryDate', 'EntryTime']],
                                                           'DER_REPORT_RESEARCH'),
                                                          ([['EntryDate'], ['EntryDate', 'EntryTime', 'time_year']],
                                                           'DER_REPORT_SUBTABLE'),
                                                          ([['EntryTime'], ['EntryTime', 'EntryDate', 'tmstamp']], 'GG_ORG_LIST'),
                                                          ([['EntryTime'], ['EntryDate', 'EntryTime', 'remark']], 'I_ORGAN_SCORE'),
                                                          ([['EntryTime'], ['EntryDate', 'EntryTime', 'author_id']], 'REPORT_AUTHOR'),
                                                          ([['EntryDate'], ['entrydate', 'EntryTime']], 'I_SYS_CLASS'),
                                                          ([['EntryDate'], ['EntryTime', 'EntryTime']], 'I_REPORT_TYPE'),
                                                          ([['entrydate'], ['entrydate', 'entrytime']], 'T_PRE_RELIABILITY'),

                                                          ])
    def test_get_source_table_value_all1(self, factor_lists, table_name):
        for factor_list in factor_lists:
            if table_name in ['I_SYS_CLASS', 'I_REPORT_TYPE']:
                df = self.sd1.get_source_table_value(table_name, factor_list, entrydate=['>20071101'])
            else:
                df = self.sd1.get_source_table_value(table_name, factor_list, entrydate=['>20210604'])
            assert len(df) > 0
            assert isinstance(df, pd.DataFrame)

    @pytest.mark.skipif(os.environ.get("DSWMAP_envTag") != 'prd', reason="生产环境条件下测试")
    @pytest.mark.parametrize('factor_lists, table_name', [([['ENTRY_DT'], ['REMOVE_DT']], 'AShareIndustriesClassCITICS'),
                                                          ([['CHANGE_NAME'], ['TEXT3']], 'CHANGE_TYPE'),
                                                          ([['y1'], ['y1', 'y2']], 'RESEARCHER_INFO')
                                                         ])
    def test_get_source_table_value_all2(self, factor_lists, table_name):
        for factor_list in factor_lists:
            df = self.sd1.get_source_table_value(table_name, factor_list)
            assert len(df) > 0
            assert isinstance(df, pd.DataFrame)

    @pytest.mark.skipif(os.environ.get("DSWMAP_envTag") != 'prd', reason="生产环境条件下测试")
    @pytest.mark.parametrize('factor_lists, table_name', [([['RPTDATE'], ['S_INFO_WINDCODE', 'RPTDATE']], 'CMFundThirdPartyRating'),
                                                          ([['REPORT_ID'], ['YEAR', 'CAPITAL']], 'CMB_CAPITAL'),
                                                          ([['S_INFO_WINDCODE', 'S_INFO_COMPNAME', 'INDEX_INTRO']], 'AIndexDescription'),
                                                          ([['Current_Create_Date'], ['Previous_Create_Date', 'Into_Date']],
                                                           'CMB_REPORT_ADJUST')
                                                          ])
    def test_get_source_table_value_all3(self, factor_lists, table_name):
        for factor_list in factor_lists:
            if table_name == 'CMFundThirdPartyRating':
                df = self.sd1.get_source_table_value(table_name, factor_list, OPDATE=">20210730")
            elif table_name == 'CMB_CAPITAL':
                df = self.sd1.get_source_table_value(table_name, factor_list, YEAR="2021")
            elif table_name == 'AIndexDescription':
                df = self.sd1.get_source_table_value(table_name, factor_list, date_list=[])
            else:
                df = self.sd1.get_source_table_value(table_name, factor_list, Forecast_Year='2004',
                                                     Current_Forecast_Profit=[">100000", "<105000"])
            assert len(df) > 0
            assert isinstance(df, pd.DataFrame)

    @pytest.mark.skipif(os.environ.get("DSWMAP_envTag") != 'prd', reason="生产环境条件下测试")
    @pytest.mark.parametrize('factor_lists, table_name',  [([['S_INFO_WINDCODE', 'S_INFO_NAME','S_INFO_EXCHMARKET','S_INFO_LISTDATE']], 'CFUTURESDESCRIPTION'),
                                                         ([['OBJECT_ID','S_INFO_WINDCODE', 'S_INFO_RALATEDCODE','S_RELATION_TYPCODE']], 'CFUTURESARBITRAGECONTRACT'),
                                                         ([['S_INFO_WINDCODE', 'START_DT','END_DT','PERIOD']], 'CCBondConversionreset')])
    def test_get_source_table_value_all4(self, factor_lists, table_name):
        date_list=['20220208','20220225']
        for factor_list in factor_lists:
            df = self.sd1.get_source_table_value(table_name, factor_list, date_list)
            assert len(df) > 0
            assert isinstance(df, pd.DataFrame)

class TestStockData2(object):
    """
    测试StockData股票数据接口
    """

    @classmethod
    def setup_class(cls):
        cls.sd2 = StockData(data_source="wind", use_cache=False)

    @pytest.mark.parametrize('stock_list', [
        ['300707.SZ', '300726.SZ', '300705.SZ', '601658.SH'], '300707.SZ', ['300707.SZ']])
    @pytest.mark.parametrize('date_list', [('20200101', '20200630'), '20200106', ['20200106']])
    @pytest.mark.parametrize('factor_list', ['float_a_shr_today'])
    @pytest.mark.parametrize('fill_na', [True, False])
    def test_get_factor_price_daily(self, stock_list, date_list, factor_list, fill_na):
        result = self.sd2.get_factor_price_daily(stock_list, date_list,
                                                factor_list, fill_na=fill_na)
        print(result.head())
        assert isinstance(result, pd.DataFrame)
        if os.environ.get("DSWMAP_envTag") == 'prd':
            assert len(result) > 0

    @pytest.mark.parametrize('stock_list', [['603118.SH', '300044.SZ', '300555.SZ', '601658.SH']])
    @pytest.mark.parametrize('date_list', ([['20190630', '20190930']]))
    @pytest.mark.parametrize('factor_list', [['profitnotice_date', 'profitnotice_netprofitmin',
                                              'profitnotice_netprofitmax', 'profitnotice_changemin',
                                              'profitnotice_changemax', 'stmnote_finexp',"ann_dt_kb",
                                              "yoysales_kb", "yoyop_kb", "yoyebt_kb", "yoynetprofit_deducted_kb",
                                              "yoyeps_basic_kb", "roe_yearly_kb"]])
    @pytest.mark.parametrize('statement_type', ['408001000'])
    @pytest.mark.parametrize('fill_na', [True, False])
    def test_factor_financial_report(self, stock_list, date_list, factor_list, statement_type, fill_na):
        result = self.sd2.get_factor_financial_report(stock_list, date_list, factor_list,
                                                     statement_type=statement_type, fill_na=fill_na)
        print(result.head())
        assert isinstance(result, pd.DataFrame)
        if os.environ.get("DSWMAP_envTag") == 'prd':
            assert len(result) > 0

    @pytest.mark.parametrize('stock_list', [['002314.SZ', '600422.SH', '603369.SH', '601658.SH']])
    @pytest.mark.parametrize('date_list', ([('20190630', '20190930')]))
    @pytest.mark.parametrize('factor_list', [['roe', 'operateincome', 'stmnote_finexp_fa', 'stm_is',
                                              'exinterestdebt_current', 'exinterestdebt_noncurrent',
                                              'investcapital', 'ocftoprofit', 'cashtoliqdebtwithinterest',
                                              'fcff', 'ebit_fa', 'ebitda_fa']])
    def test_get_factor_financial_analysis(self, stock_list, date_list, factor_list):
        result = self.sd2.get_factor_financial_analysis(stock_list, date_list, factor_list)
        print(result.head())
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('stock_list', [['600138.SH', '000426.SZ', '600869.SH']])
    @pytest.mark.parametrize('date_list', [['20210331', '20210630']])
    @pytest.mark.parametrize('factor_list', [['ann_dt_gd', 'holder_enddate', 'holder_holdercategory', 'holder_name',
                                              'holder_quantity', 'holder_pct', 'holder_sharecategory', 'holder_restrictedquantity',
                                              'holder_aname', 'holder_sequence', 'holder_sharecategoryname', 'holder_memo',
                                              'info_compcode', 'holder_nat']])
    @pytest.mark.parametrize('fill_na', [True, False])
    def test_get_factor_insideholder(self, stock_list, date_list, factor_list, fill_na):
        result = self.sd2.get_factor_insideholder(stock_list, date_list, factor_list, fill_na=fill_na)
        print(result.head())
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)


@pytest.mark.skipif(os.environ.get("DSWMAP_envTag") != 'prd', reason="生产环境条件下测试")
class TestBaseFactor3(object):

    @classmethod
    def setup_class(cls):
        cls.sd3 = StockData(data_source="wind", use_cache=True)

    @pytest.mark.parametrize('stock_list', [['300707.SZ', '300726.SZ', '300705.SZ', '601658.SH'],
                                            '300707.SZ', ['300707.SZ']])
    @pytest.mark.parametrize('date_list', [('20200101', '20200630'), '20200106', ['20200107']])
    @pytest.mark.parametrize('factor_list', [['pre_close', 'open', 'high'], 'high', ['high']])
    @pytest.mark.parametrize('fill_na', [True, False])
    def test_get_factor_price_daily(self, stock_list, date_list, factor_list, fill_na):
        result = self.sd3.get_factor_price_daily(stock_list, date_list,
                                                factor_list, fill_na=fill_na)
        print(result.head())
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('stock_list', [['002302.SZ', '002372.SZ', '601658.SH'], '002302.SZ', ['002302.SZ']])
    @pytest.mark.parametrize('date_list', [('20200101', '20200630'), '20200104', ['20200104']])
    @pytest.mark.parametrize('factor_list', [['ev', 'mkt_cap_ard', 'pe_ttm'], 'mkt_cap_ard', ['mkt_cap_ard']])
    @pytest.mark.parametrize('fill_na', [True, False])
    def test_get_factor_valuation_metrics(self, stock_list, date_list, factor_list, fill_na):
        result = self.sd3.get_factor_valuation_metrics(stock_list, date_list, factor_list, fill_na=fill_na)
        print(result.head())
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('stock_list', [['600712.SH', '002037.SZ', '600321.SH', '600225.SH']])
    @pytest.mark.parametrize('date_list', ([('20200101', '20200630')]))
    @pytest.mark.parametrize('factor_list', [['annualyeild_100w', 'beta_100w', 'beta_60m']])
    def test_get_factor_risk_analysis(self, stock_list, date_list, factor_list):
        result = self.sd3.get_factor_risk_analysis(stock_list, date_list, factor_list)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('stock_list', [['002314.SZ', '600422.SH', '603369.SH', '601658.SH']])
    @pytest.mark.parametrize('date_list', ([('20190901', '20190930')]))
    @pytest.mark.parametrize('factor_list', [['eps_basic', 'eps_diluted', 'roa_ttm']])
    def test_get_factor_financial_analysis(self, stock_list, date_list, factor_list):
        result = self.sd3.get_factor_financial_analysis(stock_list, date_list, factor_list)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('stock_list', [['603118.SH', '300044.SZ', '300555.SZ', '601658.SH']])
    @pytest.mark.parametrize('date_list', ([('20190901', '20190930')]))
    @pytest.mark.parametrize('factor_list', [['monetary_cap', 'notes_rcv', 'dvd_rcv']])
    @pytest.mark.parametrize('statement_type', ('102', '108'))
    @pytest.mark.parametrize('fill_na', (True, False))
    def test_factor_financial_report(self, stock_list, date_list, factor_list, fill_na, statement_type):
        result = self.sd3.get_factor_financial_report(stock_list, date_list, factor_list,
                                                     statement_type=statement_type, fill_na=fill_na)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('stock_list', [['603113.SH', '002299.SZ', '600738.SH']])
    @pytest.mark.parametrize('date_list', ([('20190901', '20190930')]))
    @pytest.mark.parametrize('factor_list', [['per_div_trans', 'per_cashpaidbeforetax', 'ex_dt', 'dvd_payout_dt']])
    def test_get_factor_dividend(self, stock_list, date_list, factor_list):
        result = self.sd3.get_factor_dividend(stock_list, date_list, factor_list)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('stock_list', [['300564.SZ', '300800.SZ', '688139.SH', '688098.SH']])
    @pytest.mark.parametrize('factor_list', [
        ['short_name', 'con_sector', 'listing_place']])
    def test_get_factor_newsmsg(self, stock_list, factor_list):
        result = self.sd3.get_factor_newsmsg(stock_list, factor_list)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('stock_list', [['603506', '601828', '600775']])
    @pytest.mark.parametrize('date_list', ([('20200101', '20200630')]))
    @pytest.mark.parametrize('factor_list', [['rating_up_number7', 'report_number30']])
    @pytest.mark.parametrize('stock_type', [0, 1])
    @pytest.mark.parametrize('block_type', [2, 4])
    def test_get_factor_conforecast(self, stock_list, date_list, factor_list, stock_type, block_type):
        result = self.sd3.get_factor_conforecast(stock_list, date_list, factor_list,
                                                stock_type=stock_type, block_type=block_type)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('stock_list',[['601998.SH', '002007.SZ', '600369.SH', '601658.SH']])
    @pytest.mark.parametrize('date_list', ([('20200101', '20200630')]))
    @pytest.mark.parametrize('factor_list', [['alpha1', 'alpha2', 'alpha120']])
    def test_get_factor_alpha191(self, stock_list, date_list, factor_list):
        result = self.sd3.get_factor_alpha191(stock_list, date_list, factor_list)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('stock_list', [['601998.SH', '002007.SZ', '600369.SH']])
    @pytest.mark.parametrize('date_list', ([('20200101', '20200630')]))
    @pytest.mark.parametrize('factor_list', [['barra_cne5_residualvolatility_dastd', 'barra_cne5_size']])
    def test_get_factor_barra(self, stock_list, date_list, factor_list):
        result = self.sd3.get_factor_barra(stock_list, date_list, factor_list)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('stock_list', [['601998.SH', '002007.SZ', '600369.SH', '601658.SH']])
    @pytest.mark.parametrize('date_list', ([('20200101', '20200630')]))
    @pytest.mark.parametrize('factor_list', [['coskew', 'ema_crossover', 'tskew']])
    def test_get_factor_technical_analysis(self, stock_list, date_list, factor_list):
        result = self.sd3.get_factor_technical_analysis(stock_list, date_list, factor_list)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('stock_list', [['000001.SZ', '000002.SZ', '000004.SZ']])
    @pytest.mark.parametrize('date_list', ([('20200101', '20200630')]))
    @pytest.mark.parametrize('factor_list', [["net_profit_excl_min_int_inc"]])
    @pytest.mark.parametrize('publishDateType', ['ACCOUNTINGDAY', 'PUBLISHDAY', 'TTM'])
    def test_get_finicial_cross_section_data(self, stock_list, date_list, factor_list, publishDateType):
        result = self.sd3.get_finicial_cross_section_data(stock_list, date_list, factor_list, publishDateType)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('stock_list', [['600329.SH', '000996.SZ', '000400.SZ']])
    @pytest.mark.parametrize('date_list', ([('20210101', '20210630')]))
    @pytest.mark.parametrize('factor_list', [['risk_universe', 'alpha_universe']])
    def test_get_factor_evaluation(self, stock_list, date_list, factor_list):
        result = self.sd3.get_factor_evaluation(stock_list, date_list, factor_list)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('stock_list', [['601998.SH', '002007.SZ', '600369.SH']])
    @pytest.mark.parametrize('date_list', ([('20200101', '20200630')]))
    @pytest.mark.parametrize('factor_list', [['relative_vol_updown', 'cv_turn']])
    def test_get_factor_emotion(self, stock_list, date_list, factor_list):
        result = self.sd3.get_factor_emotion(stock_list, date_list, factor_list)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('stock_list', [['601998.SH', '002007.SZ', '600369.SH']])
    @pytest.mark.parametrize('date_list', ([('20200101', '20200630')]))
    @pytest.mark.parametrize('factor_list', [['weighted_strength_2m', 'relative_strength_1m', 'halpha']])
    def test_get_factor_momentum(self, stock_list, date_list, factor_list):
        result = self.sd3.get_factor_momentum(stock_list, date_list, factor_list)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('stock_list', [['000001.SZ', '000002.SZ', '000005.SZ']])
    @pytest.mark.parametrize('date_list', ([('20211001', '20211030')]))
    @pytest.mark.parametrize('factor_list', [['barra_cne6_beta', 'barra_cne6_booktoprice']])
    def test_get_factor_barrarisk6(self, stock_list, date_list, factor_list):
        result = self.sd3.get_factor_barrarisk6(stock_list, date_list, factor_list)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

if __name__ == "__main__":
    pytest.main(["-v"])

