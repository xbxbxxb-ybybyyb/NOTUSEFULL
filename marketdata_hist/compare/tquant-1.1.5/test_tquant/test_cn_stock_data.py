from tquant import StockData
import unittest


class TestCnStockData(unittest.TestCase):

    def setUp(self):
        self.sd = StockData()

    def test_get_stock_basics(self):
        # 查询单个股票的基本信息
        df1_1 = self.sd.get_stock_basics('000990.SZ')
        self.assertFalse(df1_1.empty)
        self.assertTrue(len(df1_1.columns) == 17)

        # 查询列表中只有一个股票的基本信息
        df1_2 = self.sd.get_stock_basics(['000990.SZ'])
        self.assertFalse(df1_2.empty)
        self.assertTrue(len(df1_2.columns) == 17)

        # 查询列表中多支股票的基本信息
        df1_3 = self.sd.get_stock_basics(['000990.SZ', '900936.SH', '002160.SZ'])
        self.assertTrue(len(df1_3) == 3)
        self.assertTrue(len(df1_3.columns) == 17)

    def test_get_stock_price_daily(self):
        # 多支 股票 日期 因子 fill_na = True
        df2_1 = self.sd.get_stock_price_daily(['300707.SZ', '300726.SZ', '300705.SZ', '601658.SH'],
                                              ['20191213', '20191215'],
                                              ['pre_close', 'open', 'high'], fill_na=True)
        self.assertTrue(len(df2_1) == 8)

        #  单个日期，fill_na默认False
        df2_2 = self.sd.get_stock_price_daily(['300707.SZ', '300726.SZ', '601658.SH'], '20191213', ['pre_close', 'open', 'high'])
        self.assertTrue(len(df2_2) == 3)

        # 单个股票、日期、因子的字符串
        df2_3 = self.sd.get_stock_price_daily('300707.SZ', '20191113', 'high')
        self.assertFalse(df2_3.empty)

        # 列表中只有一个股票、日期、因子
        df2_4 = self.sd.get_stock_price_daily(['300707.SZ'], ['20191213'], ['high'])
        self.assertFalse(df2_4.empty)

    def test_get_stock_valuation_metrics(self):
        # 多支 股票 日期 因子 fill_na = True
        df3_1 = self.sd.get_stock_valuation_metrics(['002302.SZ', '002372.SZ', '300240.SZ', '601658.SH'],
                                                    ['20191008', '20191009'],
                                                    ['ev', 'mkt_cap_ard', 'pe_ttm'], fill_na=True)
        self.assertTrue(len(df3_1) == 8)

        #  单个日期，fill_na默认False
        df3_2 = self.sd.get_stock_valuation_metrics(['002302.SZ', '002372.SZ', '601658.SH'], '20191008',
                                                    ['ev', 'mkt_cap_ard', 'pe_ttm'])
        self.assertTrue(len(df3_2) == 2)

        # 单个股票、日期、因子的字符串
        df3_3 = self.sd.get_stock_valuation_metrics('002302.SZ', '20191008', 'mkt_cap_ard')
        self.assertFalse(df3_3.empty)

        # 列表中只有一个股票、日期、因子
        df3_4 = self.sd.get_stock_valuation_metrics(['002302.SZ'], ['20191008'], ['mkt_cap_ard'])
        self.assertFalse(df3_4.empty)

    def test_get_stock_risk_analysis(self):
        # 多支 股票 日期 因子 fill_na = True
        df4_1 = self.sd.get_stock_risk_analysis(['600373.SH', '600395.SH', '600318.SH', '601658.SH'],
                                                ['20191008', '20191009'],
                                                ['annualyeild_100w', 'beta_100w', 'beta_60m'], fill_na=True)
        self.assertTrue(len(df4_1) == 8)

        #  单个日期，fill_na默认False
        df4_2 = self.sd.get_stock_risk_analysis(['600373.SH', '600395.SH', '601658.SH'], '20191008',
                                                ['annualyeild_100w', 'beta_100w', 'beta_60m'])
        self.assertTrue(len(df4_2) == 2)

        # 单个股票、日期、因子的字符串
        df4_3 = self.sd.get_stock_risk_analysis('600373.SH', '20191008', 'annualyeild_100w')
        self.assertFalse(df4_3.empty)

        # 列表中只有一个股票、日期、因子
        df4_4 = self.sd.get_stock_risk_analysis(['600373.SH'], ['20191008'], ['beta_100w'])
        self.assertFalse(df4_4.empty)

    def test_get_stock_financial_analysis(self):
        # 多支 股票 日期 因子 fill_na = True
        df5_1 = self.sd.get_stock_financial_analysis(['002314.SZ', '600422.SH', '603369.SH', '601658.SH'], ['20190131', '20190930'],
                                        ['eps_basic', 'eps_diluted', 'roa_ttm'], fill_na=True)
        self.assertTrue(len(df5_1) == 8)

        #  单个日期，fill_na默认False
        df5_2 = self.sd.get_stock_financial_analysis(['002314.SZ', '600422.SH', '601658.SH'], '20190930',
                                                     ['orps', 'retainedps', 'cfps'])
        self.assertFalse(df5_2.empty)
        self.assertTrue(len(df5_2) == 3)

        # 单个股票、日期、因子的字符串
        df5_3 = self.sd.get_stock_financial_analysis('600422.SH', '20190930', 'roe_ttm')
        self.assertFalse(df5_3.empty)

        # 列表中只有一个股票、日期、因子
        df5_4 = self.sd.get_stock_financial_analysis(['600422.SH'], ['20190930'], ['roe_ttm'])
        self.assertFalse(df5_4.empty)

    def test_get_stock_financial_report(self):
        # 多支 股票 日期 因子 fill_na = True statement_type默认408001000(合并报表)
        df6_1 = self.sd.get_stock_financial_report(['300397.SZ', '002594.SZ', '600533.SH', '601658.SH'],
                                                   ['20190930', '20190630'],
                                                   ['monetary_cap', 'notes_rcv', 'dvd_rcv'], fill_na=True)
        self.assertTrue(len(df6_1) == 8)

        #  单个日期，fill_na默认False
        df6_2 = self.sd.get_stock_financial_report(['300397.SZ', '002594.SZ', '601658.SH'], '20190930',
                                                   ['settle_rsrv', 'prem_rcv', 'tot_oper_rev'],
                                                   statement_type='408002000')
        self.assertFalse(df6_2.empty)
        self.assertTrue(len(df6_2) == 3)

        # 单个股票、日期、因子的字符串
        df6_3 = self.sd.get_stock_financial_report('300397.SZ', '20190930', 'tot_oper_rev')
        self.assertFalse(df6_3.empty)

        # 列表中只有一个股票、日期、因子
        df6_4 = self.sd.get_stock_financial_report(['300397.SZ'], ['20190930'], ['tot_oper_rev'],
                                                   statement_type='408002000')
        self.assertFalse(df6_4.empty)

    def test_get_stock_dividend(self):
        import pandas as pd
        # 分红因子由多个主键来确定一条数据，所以把所有列打印出来
        pd.set_option('display.max_columns', None)
        # 多支股票 日期 因子 fill_na=True
        df7_1 = self.sd.get_stock_dividend(['600728.SH', '600340.SH', '002016.SZ'], ['20190630', '20190930'],
                                           ['per_div_trans', 'per_cashpaidbeforetax', 'ex_dt', 'dvd_payout_dt'],
                                           fill_na=True)
        self.assertFalse(df7_1.empty)

        # 列表只有一个元素
        df7_2 = self.sd.get_stock_dividend(['600728.SH'], ['20190630'], ['per_div_trans'])
        self.assertFalse(df7_2.empty)

        # 单支股票 日期 因子的字符串
        df7_3 = self.sd.get_stock_dividend('600728.SH', '20190630', 'per_div_trans')
        self.assertFalse(df7_3.empty)

    def test_get_stock_newsmsg(self):
        # 多支股票 因子
        df8_1 = self.sd.get_stock_newsmsg(['600077.SH', '002236.SZ', '600373.SH', '688016.SH'],
                                          ['short_name', 'con_sector', 'listing_place'])
        self.assertFalse(df8_1.empty)

        # 单支股票、因子
        df8_2 = self.sd.get_stock_newsmsg(['600077.SH'], ['con_sector'])
        self.assertFalse(df8_2.empty)

        # 单支股票、因子的列表
        df8_3 = self.sd.get_stock_newsmsg('600077.SH', 'con_sector')
        self.assertFalse(df8_3.empty)

    def test_get_stock_conforecast(self):
        # stock_type block_type取值详见参数说明
        df9_1 = self.sd.get_stock_conforecast(['603506', '601828', '600775'], ['20180102', '20180103'],
                                 ['rating_up_number7', 'report_number30'], stock_type=1, block_type=2)
        self.assertFalse(df9_1.empty)

    def test_get_md_transaction(self):
        df10_1 = self.sd.get_md_transaction('900957.SH', '20190709 090000000', '20190710 080000000')
        self.assertFalse(df10_1.empty)

    def test_get_md_order(self):
        df11_1 = self.sd.get_md_order('000001.SZ', '20190709 090000000', '20190710 080000000')
        self.assertFalse(df11_1.empty)

    def test_get_md_kline(self):
        df12_1 = self.sd.get_md_kline('000001.SZ', '20190709 090000000', '20190710 080000000')
        self.assertFalse(df12_1.empty)

    def test_get_md_tick(self):
        df13_1 = self.sd.get_md_tick('000001.SZ', '20190709 090000000', '20190710 080000000')
        self.assertFalse(df13_1.empty)

    def test_get_plate_info(self):
        # 中信行业全部
        df14_1 = self.sd.get_plate_info('INDUSTRY', '20030101', 'CITICS.b1')
        self.assertFalse(df14_1.empty)
        self.assertTrue(len(df14_1.columns) == 4)

        # 中信一级行业
        df14_2 = self.sd.get_plate_info('INDUSTRY', '20180108', 'CITICS.b101')
        self.assertFalse(df14_2.empty)
        self.assertTrue(len(df14_2.columns) == 4)

        # 中信二级行业
        df14_3 = self.sd.get_plate_info('INDUSTRY', '20030101', 'CITICS.b10102')
        self.assertFalse(df14_3.empty)
        self.assertTrue(len(df14_3.columns) == 4)

        # 中信三级行业
        df14_4 = self.sd.get_plate_info('INDUSTRY', '20030101', 'CITICS.b1010201')
        self.assertFalse(df14_4.empty)
        self.assertTrue(len(df14_4.columns) == 4)

        # 申万行业全部
        df14_5 = self.sd.get_plate_info('INDUSTRY', '20070702', 'SW.61')
        self.assertFalse(df14_5.empty)
        self.assertTrue(len(df14_5.columns) == 4)

        # 申万一级行业
        df14_6 = self.sd.get_plate_info('INDUSTRY', '20070702', 'SW.6102')
        self.assertFalse(df14_6.empty)
        self.assertTrue(len(df14_6.columns) == 4)

        # 申万二级行业
        df14_7 = self.sd.get_plate_info('INDUSTRY', '20070702', 'SW.610102')
        self.assertFalse(df14_7.empty)
        self.assertTrue(len(df14_7.columns) == 4)

        # 申万三级行业
        df14_8 = self.sd.get_plate_info('INDUSTRY', '20070702', 'SW.61010201')
        self.assertFalse(df14_8.empty)
        self.assertTrue(len(df14_8.columns) == 4)

        # 证监会行业全部
        df14_9 = self.sd.get_plate_info('INDUSTRY', '20121231', 'CSRC.12')
        self.assertFalse(df14_9.empty)
        self.assertTrue(len(df14_9.columns) == 4)

        # 证监会一级行业
        df14_10 = self.sd.get_plate_info('INDUSTRY', '20121231', 'CSRC.1202')
        self.assertFalse(df14_10.empty)
        self.assertTrue(len(df14_10.columns) == 4)

        # 证监会二级行业
        df14_11 = self.sd.get_plate_info('INDUSTRY', '20121231', 'CSRC.120102')
        self.assertFalse(df14_11.empty)
        self.assertTrue(len(df14_11.columns) == 4)

        # 市场板块 全部A股
        df14_12 = self.sd.get_plate_info('MARKET', 20180309, 'ALLA')
        self.assertFalse(df14_12.empty)
        self.assertTrue(len(df14_12.columns) == 2)

        # 市场板块 上海A股
        df14_13 = self.sd.get_plate_info('MARKET', 20180309, 'SHA')
        self.assertFalse(df14_13.empty)
        self.assertTrue(len(df14_13.columns) == 2)

        # 市场板块 上海A股 use_prev_name=False为最新的股票名称，默认True为指定日期时的股票名称
        df14_14 = self.sd.get_plate_info('MARKET', 20180309, 'SHA', use_prev_name=False)
        self.assertFalse(df14_14.empty)
        self.assertTrue(len(df14_14.columns) == 2)

        # 市场板块 深圳A股
        df14_15 = self.sd.get_plate_info('MARKET', 20180309, 'SZA')
        self.assertFalse(df14_15.empty)
        self.assertTrue(len(df14_15.columns) == 2)

        # 市场板块 中小板
        df14_16 = self.sd.get_plate_info('MARKET', 20180309, 'SME')
        self.assertFalse(df14_16.empty)
        self.assertTrue(len(df14_16.columns) == 2)

        # 市场板块 创业板
        df14_17 = self.sd.get_plate_info('MARKET', 20180309, 'GEM')
        self.assertFalse(df14_17.empty)
        self.assertTrue(len(df14_17.columns) == 2)

    def test_get_stock_industry(self):
        trading_codes = ['600000.SH', '600004.SH', '600006.SH', '600007.SH', '600008.SH']

        # CSRC 证监会行业只有两级所以不能用industry_level的默认值3，需要指定值
        df15_1 = self.sd.get_stock_industry(trading_codes, '20190916', 'CSRC', industry_level=2)

        self.assertFalse(df15_1.empty)
        self.assertTrue(len(df15_1.columns) == 4)

        # CITICS 中信行业 industry_level默认3级行业分类
        df15_2 = self.sd.get_stock_industry(trading_codes, '20190516', 'CITICS')
        self.assertFalse(df15_2.empty)
        self.assertTrue(len(df15_2.columns) == 4)

        # SW 申万行业
        df15_3 = self.sd.get_stock_industry(trading_codes, '20190516', 'SW', industry_level=2)
        self.assertFalse(df15_3.empty)
        self.assertTrue(len(df15_3.columns) == 4)

        # industry_type不指定行业时 返回全部3个行业的信息
        df15_4 = self.sd.get_stock_industry(trading_codes, '20190516', industry_level=2)
        self.assertTrue(len(df15_4.columns) == 4)
        self.assertTrue(len(df15_4) == len(trading_codes) * 3)

    def test_stock_filter(self):
        # filter_type默认'SSO',过滤过滤掉STPT+停牌+开盘涨停的股票
        stock_pool1 = self.sd.get_plate_info('MARKET', '20180309', 'SHA').loc[:, 'stock'].tolist()
        df16_1 = self.sd.stock_filter(stock_pool1, '20180516')
        self.assertTrue(len(df16_1) < len(stock_pool1))

        # 过滤开盘跌停
        stock_pool2 = self.sd.get_plate_info('MARKET', '20180309', 'SHA').loc[:, 'stock'].tolist()
        df16_2 = self.sd.stock_filter(stock_pool2, '20180516', filter_type='OPENDOWNLIMIT')
        self.assertTrue(len(df16_2) < len(stock_pool2))

    def tearDown(self):
        pass
