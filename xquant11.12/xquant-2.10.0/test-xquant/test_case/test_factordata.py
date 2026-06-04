import time
import unittest
import pandas as pd
from version_control import version_number

from xquant.factordata import FactorData

if version_number == 0:
    try:
        from xquant.factor.FactorEnum import *
        from xquant.factordata.factorenum import *
    except:
        pass
else:
    from xquant.factordata.factorenum import *


class TestFactorData(unittest.TestCase):
    def setUp(self):
        self.fd = FactorData()
        self.low_library_name = 'a' + str(20180808)
        self.high_library_name = 'b' + str(20180808)
        self.low_list = []
        self.high_list = []
        for i in range(1, 5):
            self.low_list.append("low" + str(i))
            self.high_list.append("high" + str(i))

        try:
            self.fd.add_factor(self.low_library_name, ["low1"])
        except:
            pass

    def test_create_add(self):
        with self.assertRaises(Exception) as context:
            abnormal_return = self.fd.create_factor_library(self.low_library_name, "Alpha")
        self.assertTrue('The library name already exists' in str(context.exception))

        with self.assertRaises(Exception) as context:
            abnormal_return = self.fd.create_factor_library(self.high_library_name, "T+0")
        self.assertTrue('The library name already exists' in str(context.exception))

        with self.assertRaises(Exception) as context:
            abnormal_return = self.fd.add_factor(self.low_library_name, self.low_list)
        self.assertTrue('已存在' in str(context.exception))

        with self.assertRaises(Exception) as context:
            abnormal_return = self.fd.add_factor(self.high_library_name, self.high_list)
        self.assertTrue('已存在' in str(context.exception))

        self.fd.remove_factor(self.low_library_name, ["low1"])

        self.fd.add_factor(self.low_library_name, ["low1"])

        with self.assertRaises(Exception) as context:
            self.fd.remove_factor(self.low_library_name, ["xuxiang"])
        self.assertTrue('不存在' in str(context.exception))


    def test_update(self):
        df1 = pd.DataFrame([["20190328", 1, 1, 1, 1]], columns=["time", "high1", "high2", "high3", "high4"])
        df2 = pd.DataFrame(
            [["sz.001", "20190403", 123, 123, 123],
             ["sz.001", "20190404", 345, 345, 345],
             ["sz.001", "20190405", 567, 567, 567],
             ["sz.002", "20190406", 456, 456, 456],
             ["sz.002", "20190407", 567, 567, 567],
             ["sz.002", "20190408", 890, 890, 890]],
            columns=["stock", "mddate", "low2", "low3", "low4"])
        df1.set_index("time", inplace=True)
        df2.set_index(["stock", "mddate"], inplace=True)
        print(self.fd.update_factor_value(self.low_library_name, df2))
        # True
        print(self.fd.update_factor_value(self.high_library_name, df1, "SH.001", "20190325"))

    def test_get_personal(self):
        low_df = self.fd.get_factor_value(self.low_library_name, ["sz.001", "sz.002"], ["20190404", "20190405"],
                                          self.low_list[1:])
        print(low_df.head())

        high_df = self.fd.get_factor_value(self.high_library_name, "SH.001", "20190325", self.high_list)
        print(high_df.head())

    def test_get_market(self):
        # 行情指标
        df1 = self.fd.get_factor_value("Basic_factor", ['300161.SZ', '300135.SZ'], ['20180808', '20180809'],
                                       ['pre_close', 'open', 'high'])
        print(df1.head())
        df1 = self.fd.get_factor_value("Basic_factor", ['300161.SZ', '300135.SZ'], ['20180808', '20180809'],
                                       ['pre_close', 'open', 'high'], fill_na=True)
        print(df1.head())
        df1 = self.fd.get_factor_value("Basic_factor", ['002139.SZ'], mddate=['20180808', '20180809'],
                                       factor_names=['pre_close', 'open', 'high'])
        print(df1.head())

    def test_get_finance(self):
        # 获取估值\财务因子
        df2 = self.fd.get_factor_value("Basic_factor", ['600369.SH', '600373.SH', '603169.SH', '603611.SH'],
                                       ['20180102', '20180131'], ['pe_ttm', 'annualyeild_24m'])
        print(df2.head())
        df2 = self.fd.get_factor_value("Basic_factor", ['600369.SH', '600373.SH', '603169.SH', '603611.SH'],
                                       ['20180102', '20180131'], ['pe_ttm', 'annualyeild_24m'], fill_na=True)
        print(df2.head())
        df2 = self.fd.get_factor_value("Basic_factor", ['002139.SZ'], mddate=['20180102', '20180131'],
                                       factor_names=['pe_ttm', 'annualyeild_24m'])
        print(df2.head())

    def test_financial_analysis(self):
        # 财务分析
        df3 = self.fd.get_factor_value("Basic_factor", ['002139.SZ', '000657.SZ'], ['20180331', '20180630'],
                                       ['eps_basic', 'eps_diluted'])
        print(df3.head())
        df3 = self.fd.get_factor_value("Basic_factor", ['002139.SZ', '000657.SZ'], ['20180331', '20180630'],
                                       ['eps_basic', 'eps_diluted'], fill_na=True)
        print(df3.head())
        df3 = self.fd.get_factor_value("Basic_factor", ['002139.SZ'], mddate=['20180331', '20180630'],
                                       factor_names=['eps_basic', 'eps_diluted'])
        print(df3.head())

    def test_financial_reports(self):
        # 财务报告
        df5 = self.fd.get_factor_value("Basic_factor", ['000671.SZ', '603179.SH', '002271.SZ'],
                                       ['20180630', '20180331'],
                                       ['tradable_fin_assets', 'notes_rcv'], statement_type=STYPE.COMBINED)
        print(df5.head())
        df5 = self.fd.get_factor_value("Basic_factor", ['000671.SZ', '603179.SH', '002271.SZ'],
                                       ['20180630', '20180331'],
                                       ['tradable_fin_assets', 'notes_rcv'], statement_type=STYPE.COMBINED,
                                       fill_na=True)
        print(df5.head())
        df5 = self.fd.get_factor_value("Basic_factor", ['002139.SZ'], mddate=['20180630', '20180331'],
                                       factor_names=['tradable_fin_assets', 'notes_rcv'], statement_type=STYPE.COMBINED)
        print(df5.head())

    def test_dividend(self):
        # 分红
        df6 = self.fd.get_factor_value("Basic_factor", ['000001.SZ', '603179.SH', '002271.SZ'], ['20171231'],
                                       ['div_aualaccmdiv'])
        print(df6.head())
        df6 = self.fd.get_factor_value("Basic_factor", ['000001.SZ', '603179.SH', '002271.SZ'], ['20171231'],
                                       ['div_aualaccmdiv'], fill_na=True)
        print(df6.head())
        df6 = self.fd.get_factor_value("Basic_factor", ['002139.SZ'], mddate=['20171231'],
                                       factor_names=['div_aualaccmdiv'])
        print(df6.head())

    def test_information(self):
        # 最新信息,注意日期传空列表
        df4 = self.fd.get_factor_value("Basic_factor", ['600077.SH', '002236.SZ', '600373.SH'], [],
                                       ['short_name', 'listing_place'])
        print(df4.head())
        df4 = self.fd.get_factor_value("Basic_factor", ['600077.SH', '002236.SZ', '600373.SH'], [],
                                       ['short_name', 'listing_place'], fill_na=True)
        print(df4.head())
        df4 = self.fd.get_factor_value("Basic_factor", ['002139.SZ'], mddate=[],
                                       factor_names=['short_name', 'listing_place'])
        print(df4.head())

    def test_con_forecast(self):
        # 一致预期(st)
        df5 = self.fd.get_factor_value("Basic_factor", ['000001', '000002', '000004', '000005', '000006'],
                                       ['20180102', '20180103', '20180104'],
                                       ["cfs_score_type", "cfs_target_price", "sell_number7"])
        print(df5.head())
        df5 = self.fd.get_factor_value("Basic_factor", ['000001', '000002', '000004', '000005', '000006'],
                                       ['20180102', '20180103', '20180104'],
                                       ["cfs_score_type", "cfs_target_price", "sell_number7"], fill_na=True)
        print(df5.head())
        df5 = self.fd.get_factor_value("Basic_factor", ['000001'],
                                       mddate=['20180102', '20180103', '20180104'],
                                       factor_names=["cfs_score_type", "cfs_target_price", "sell_number7"])
        print(df5.head())

        # 一致预期
        df11 = self.fd.get_factor_value("Basic_factor", ['4510', '000002', '3510', '2540'],
                                        ['20160104', '20160105', '20160106'],
                                        ["diversity", "pb_deviation75", "pb_deviation5"])
        print(df11.head())
        df11 = self.fd.get_factor_value("Basic_factor", ['4510', '000002', '3510', '2540'],
                                        ['20160104', '20160105', '20160106'],
                                        ["diversity", "pb_deviation75", "pb_deviation5"], fill_na=True)
        print(df11.head())
        df11 = self.fd.get_factor_value("Basic_factor", ['000002'],
                                        mddate=['20160104', '20160105', '20160106'],
                                        factor_names=["diversity", "pb_deviation75", "pb_deviation5"])
        print(df11.head())

    def test_get_wind(self):
        date_list = self.fd.tradingday(20190701, 20190801)
        df = self.fd.get_factor_value("Wind_vip", ["000001.SZ", "000002.SZ"], date_list,
                                      ['share_pledgeda_pct_holder'], 408001000)
        print(df.head())
        df = self.fd.get_factor_value("Wind_vip", ["000001.SZ", "000002.SZ"], date_list,
                                      ['stmnote_salestop5_pct'], 408001000)
        print(df.head())

        df13 = self.fd.get_factor_value("Wind_vip", ["000001.SZ", "000004.SZ"], ["20190630", "20190711"],
                                        ['fa_retainedearn_ttm', 'fa_roc_ttm', 'fa_protocost_ttm', 'fa_ebittogr_ttm',
                                         'fa_acca_ttm', 'share_pledgeda_pct_holder'])
        print(df13.head())

        df = self.fd.get_factor_value("Wind_vip", ["000001.SZ", "000004.SZ"], ["20190630", "20190711"],
                ['eps_diluted','eps_exdiluted2'])
        print(df.head())

        df = self.fd.get_factor_value("Wind_vip", ["000001.SZ", "000004.SZ"], ["20190630", "20190711"],
                                      ['eps_basic', 'roe_basic'])
        print(df.head())

        df = self.fd.get_factor_value("Wind_vip", ["000001.SZ", "000004.SZ"], ["20190630", "20190711"],
                                      ['tot_assets', 'tot_liab'],statement_type=408006000)
        print(df.head())

        df = self.fd.get_factor_value("Wind_vip", ["000001.SZ", "000004.SZ"], ["20190630", "20190711"],
                                          ['eps_basic', 'yoyeps_basic',"eps_diluted"])
        print(df.head())

        with self.assertRaises(Exception) as context:
            df = self.fd.get_factor_value("Wind_vip", ["000001.SZ", "000004.SZ"], ["20190630", "20190711"],
                                          ['eps_basic', 'yoyeps_basic', "tot_assets"])
        self.assertTrue('请分开查询' in str(context.exception))

        with self.assertRaises(Exception) as context:
            df = self.fd.get_factor_value("Wind_vip", ["000001.SZ", "000004.SZ"], ["20190630", "20190711"],
                                          ['eps_basic', 'yoyeps_basic', "fa_retainedearn_ttm"])
        self.assertTrue('请分开查询' in str(context.exception))

    def test_get_operation(self):
        # # 运营数据查询
        # stock_click_num:股票点击数;stay_time_avg:客户停留时间
        df12 = self.fd.get_factor_value("operation_data", ["000002", "000001"], ["20190618", "20190619"],
                                        ["stay_time_avg", "stock_click_num"])
        print(df12.head())

    def test_get_wind_us(self):
        df = self.fd.get_factor_value("Wind_vip_us", ['A.N', 'AA.N'], ['20190828'], ['close', 'adjfactor', 'industry'])
        print(df.head())

    def test_get_wind_commodity(self):
        df = self.fd.get_factor_value("Wind_vip_commodity", ['涤纶POY_山东昌邑', '涤纶FDY_钱清轻纺原料'], ['20190828'], ['close'])
        print(df.head())

    def test_basic_factor(self):
        stocks = self.fd.hset("MARKET", 20190701, "ALLA")["stock"].to_list()
        days = self.fd.tradingday("20160101", "20171231")
        days = [day for day in days]
        print(stocks)
        print(days)
        t1 = time.time()
        print(self.fd.get_factor_value("Basic_factor", stocks, days, ['open', 'close']))
        print(time.time() - t1)

    def test_remove(self):
        print(self.fd.remove_factor_value(self.low_library_name, "sz.001", "20190405", ["low2"]))

    def test_search(self):
        factor_list = self.fd.search_by_stock_date(self.high_library_name, "SH.001", "20190325", ["high2"])
        print(factor_list)

        tdate_two = self.fd.search_by_stock_factor(self.high_library_name, "SH.001", "high2", ["20190325"])
        print(tdate_two)

        date_list = self.fd.search_by_stock(self.high_library_name, "SH.001",
                                            ["20190326", "20190327", "20190328", "20190325"])
        print(date_list)

        stock_list = self.fd.search_by_date(self.high_library_name, "20190325", ["SH.001", "SH.002"])
        print(stock_list)

    def test_get_info(self):
        library_info = self.fd.get_library_info()
        print(library_info)

    def test_tradingday(self):
        result1 = self.fd.tradingday(20180101, 20181204)
        print(result1)

        result2 = self.fd.tradingday(20180101, 20181204, dayType='MONDAY')
        print(result2)

        result3 = self.fd.tradingday(20180101, 20181204, dayType='MONDAY', dateType='ALLDAYS')
        print(result3)

        result4 = self.fd.tradingday(20180101, 20181204, 'WEEK')
        print(result4)

        result5 = self.fd.tradingday(20180101, 20181204, 'WEEK', 'SUNDAY')
        print(result5)

        result6 = self.fd.tradingday(20180101, 20181204, 'WEEK', 'SUNDAY', dateType='ALLDAYS')
        print(result6)

        result7 = self.fd.tradingday(20180101, 20181204, 'MONTH', 'LASTDAY', 'ALLDAYS')
        print(result7)

        result8 = self.fd.tradingday(20180101, 20181204, 'MONTH', 'FIRSTDAY', 'TRADINGDAYS')
        print(result8)

        result9 = self.fd.tradingday(20180101, 20181204, 'YEAR', 'FIRSTDAY', 'TRADINGDAYS')
        print(result9)

        result10 = self.fd.tradingday(20180501, 10)
        print(result10)

        result11 = self.fd.tradingday(20180501, -10)
        print(result11)

        result12 = self.fd.tradingday(20180101, 20181001, frequency='YEAR', dayType='LASTDAY')
        print(result12)

        result13 = self.fd.tradingday(20180101, 20181231, frequency='HALFYEAR', dayType='FIRSTDAY')
        print(result13)

        result14 = self.fd.tradingday(20180101, 20181231, frequency='QUARTER', dayType='LASTDAY')
        print(result14)

        result15 = self.fd.tradingday(20180101, 20181231, frequency='MONTH', dayType='LASTDAY')
        print(result15)

        result16 = self.fd.tradingday(20180101, 20181231, frequency='WEEK', dayType='SUNDAY', dateType="ALLDAYS")
        print(result16)

    def test_hset(self):
        result1 = self.fd.hset('INDUSTRY', '20030101', 'CITICS.b1')
        print(result1)

        result5 = self.fd.hset('INDUSTRY', '20070702', 'SW.61')
        print(result5)

        result9 = self.fd.hset('INDUSTRY', '20121231', 'CSRC.12')
        print(result9)

        # 指数 沪深300
        result12 = self.fd.hset('INDEX', '20110309', 'HS300')
        print(result12)

        # 市场板块 全部A股
        result7_14 = self.fd.hset('MARKET', 20110309, 'ALLA')
        print(result7_14)

        # 市场板块 创业板
        result7_15 = self.fd.hset('MARKET', 20110309, 'GEM')
        print(result7_15)

        # 市场板块 中小板
        result7_16 = self.fd.hset('MARKET', 20110309, 'SME')
        print(result7_16)

        # 市场板块 上海A股
        result7_17 = self.fd.hset('MARKET', 20110309, 'SHA')
        print(result7_17)

        # 市场板块 深圳A股
        result7_18 = self.fd.hset('MARKET', 20110309, 'SZA')
        print(result7_18)

    def test_hind(self):
        # 证监会行业
        result1 = self.fd.hind('CSRC', 1)
        print(result1)

        # 中信行业
        result4 = self.fd.hind('CITICS', 1)
        print(result4)

        # 申万行业
        result8 = self.fd.hind('SW', 1)
        print(result8)

    def test_hsi(self):
        # CSRC 证监会一级行业 switchFlag默认不过滤NAN值
        result1 = self.fd.hsi(['000100.SZ', '000807.SZ', '1111.SZ'], "20121231", 'CSRC', 1)
        print(result1)

        # industryType 默认全部行业 ，industryLevel默认3级分类
        result12 = self.fd.hsi(['000001.SZ', '000002.SZ', '000009.SZ'], '20121231', industryLevel=2)
        print(result12)

        # industryType 默认全部行业 ，industryLevel默认3级分类 switchFlag过滤空值
        result13 = self.fd.hsi(['000001.SZ', '000002.SZ', '000009.SZ'], '20121231', industryLevel=2, switchFlag='ON')
        print(result13)

        # 单支股票测试 industryType 默认全部行业 ，industryLevel默认3级分类 switchFlag过滤空值
        result14 = self.fd.hsi('000001.SZ', '20121231', industryLevel=2, switchFlag='ON')
        print(result14)

    def test_stockfilter(self):
        stockPool = self.fd.hset('INDEX', '20110309', 'ZZ500')['stock'].tolist()
        # STPT
        result1 = self.fd.stock_filter(stockPool, "20180104", 'STPT')
        print(result1)

    def test_signal(self):
        signal_name = 'c' + str(int(time.time()))
        print(self.fd.create_signal_library(signal_name))

        high_list = ["high1", "high2", "high3"]
        print(self.fd.add_signal(signal_name, high_list))

        print(self.fd.remove_signal(signal_name, ["high1"]))
        print(self.fd.add_signal(signal_name, ["high1"]))

        high_list = ["high1", "high2", "high3"]
        d1 = {
            "time": ["20190328"],
        }
        for i in high_list:
            d1[i] = [1]
        df1 = pd.DataFrame(d1)
        df1.set_index("time", inplace=True)
        print(self.fd.update_signal(signal_name, "SH.001", "20190325", df1))

        print(self.fd.get_signal(signal_name, "SH.001", "20190325", high_list))
        
    def test_hdf(self):
        stocks = self.fd.hset("MARKET",20190701, "ALLA")['stock'].tolist()
        df = self.fd.hdf(stocks, ["20190630", "20190701", "20190702"], ["net_profit_excl_min_int_inc"])
        print(df)

    def tearDown(self):
        self.fd.remove_factor(self.low_library_name, ["low1"])
