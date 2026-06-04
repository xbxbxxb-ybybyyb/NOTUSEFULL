import time
import unittest
import pandas as pd

from xquant.factordata import FactorData
from xquant.factordata.factorenum import *


class TestFactorDataWindDb(unittest.TestCase):

    def setUp(self):
        self.fd = FactorData()
        self.dt_str = '20190813'

    def test_normal(self):
        normal_return = self.fd.get_factor_value('WIND_AShareEODPrices', TRADE_DT=self.dt_str)
        self.assertTrue(normal_return.shape[0] > 0)
        self.assertEqual(normal_return.shape[1], 23)
        self.assertTrue(all([i == self.dt_str for i in normal_return['TRADE_DT'].tolist()]))

    def test_library_name_with_upper_lower_case(self):
        normal_return = self.fd.get_factor_value('WIND_ashareeodprices', TRADE_DT=self.dt_str)
        self.assertTrue(normal_return.shape[0] > 0)
        self.assertEqual(normal_return.shape[1], 23)
        self.assertTrue(all([i == self.dt_str for i in normal_return['TRADE_DT'].tolist()]))

        normal_return = self.fd.get_factor_value('WIND_ASHAREEODPRICES', TRADE_DT=self.dt_str)
        self.assertTrue(normal_return.shape[0] > 0)
        self.assertEqual(normal_return.shape[1], 23)
        self.assertTrue(all([i == self.dt_str for i in normal_return['TRADE_DT'].tolist()]))

    def test_param_key_with_upper_lower_case(self):
        normal_return = self.fd.get_factor_value('WIND_AShareEODPrices', trade_dt=self.dt_str)
        self.assertTrue(normal_return.shape[0] > 0)
        self.assertEqual(normal_return.shape[1], 23)
        self.assertTrue(all([i == self.dt_str for i in normal_return['TRADE_DT'].tolist()]))

        normal_return = self.fd.get_factor_value('WIND_AShareEODPrices', TraDe_dt=self.dt_str)
        self.assertTrue(normal_return.shape[0] > 0)
        self.assertEqual(normal_return.shape[1], 23)
        self.assertTrue(all([i == self.dt_str for i in normal_return['TRADE_DT'].tolist()]))

    def test_dt_wrong_format(self):
        normal_return = self.fd.get_factor_value('WIND_AShareEODPrices', TRADE_DT='2019-08-13')
        self.assertTrue(normal_return.shape[0] == 0)

    def test_param_key_not_exist(self):
        # abnormal_return = self.fd.get_factor_value('WIND_AShareEODPrices', idonotexist='123')
        # self.assertTrue(abnormal_return is None)
        with self.assertRaises(Exception):
            abnormal_return = self.fd.get_factor_value('WIND_AShareEODPrices', idonotexist='123')

    def test_library_name_wrong(self):
        with self.assertRaises(Exception):
            abnormal_return = self.fd.get_factor_value('wind_AShareEODPrices', trade_dt=self.dt_str)

        with self.assertRaises(Exception):
            abnormal_return = self.fd.get_factor_value('wINd_AShareEODPrices', trade_dt=self.dt_str)

    def test_table_not_exist(self):
        # abnormal_return = self.fd.get_factor_value('WIND_Abcdefg')
        # self.assertTrue(abnormal_return is None)
        with self.assertRaises(Exception):
            abnormal_return = self.fd.get_factor_value('WIND_Abcdefg')

    def test_data_exceed(self):
        with self.assertRaises(Exception) as context:
            abnormal_return = self.fd.get_factor_value('WIND_AShareEODPrices')
        self.assertTrue('50W' in str(context.exception))

    def test_and_null(self):
        df_wind1 = self.fd.get_factor_value("WIND_AsHAREPREVIOUSNAME",
                                            factors=['S_INfo_WINDCODE', 'begindate', 'enddate', 'opdate'],
                                            OPDATE=['>=20090525', '<=20090530'], enddate='is not null')
        self.assertTrue(df_wind1.shape[0] > 0)

    def test_like(self):
        df = self.fd.get_factor_value("WIND_AShareAnnInf", factors=['S_INfo_WINDCODE', 'ann_dt'],
                                      ann_dt=['20190118', '20180102'], S_INfo_WINDCODE="like'300%'",
                                      n_info_title="like '%凯发电气%'")
        stock_code = df['S_INFO_WINDCODE'].values
        self.assertTrue(all(i[:3] == '300' for i in stock_code))

    def test_OR(self):
        df = self.fd.get_factor_value("WIND_AShareAnnInf", factors=['S_INfo_WINDCODE', 'ann_dt'],
                                      ann_dt=['<=19931027', '>=20191027'], OR='ann_dt')
        dt_list = list(set(df['ANN_DT'].values))
        self.assertTrue('2000-08-01 00:00:00' in dt_list)
        self.assertTrue('2018-01-03 00:00:00' not in dt_list)
        self.assertTrue('2019-07-31 00:00:00' not in dt_list)
        self.assertTrue('2019-08-08 00:00:00' in dt_list)

    def test_gogoal_basic1(self):
        df = self.fd.get_factor_value("GOGOAL_cmb_report_adjust",

                                      factors=['stock_code', 'current_create_date', 'Current_Forecast_Profit'],
                                      into_date=['20171207', '20171208'])
        df_len = len(df)
        self.assertTrue(df_len > 0)

    def test_gogoal_basic2(self):
        df = self.fd.get_factor_value("GOGOAL_stock_order3", factors=['stock_code', 'tdate', 'forward_pe'],
                                      tdate=['>=20120528', '<=20120529'])
        df_len = len(df)
        self.assertTrue(df_len > 0)

    def test_gogoal_OR(self):
        df = self.fd.get_factor_value("GOGOAL_stock_order3", factors=['stock_code', 'tdate', 'forward_pe'],
                                      tdate=['>=20191029', '<=19930104'], OR='tdate')
        df_len = len(df)
        self.assertTrue(df_len > 0)

    def test_gogoal_not_null(self):
        df = self.fd.get_factor_value("GOGOAL_cmb_report_adjust", factors=['stock_code', 'PREVIOUS_CREATE_DATE'],
                                      into_date=['20171207', '20171208'], PREVIOUS_CREATE_DATE="is not null")
        df_len = len(df)
        self.assertTrue(df_len > 0)
        df_null = df[df['PREVIOUS_CREATE_DATE'].isnull()]
        self.assertTrue(len(df_null) == 0)

    def test_gogoal_like(self):
        df = self.fd.get_factor_value("GOGOAL_cmb_report_adjust", factors=['stock_code', 'PREVIOUS_CREATE_DATE'],
                                      into_date=['20171207', '20171208'], PREVIOUS_CREATE_DATE="is not null",
                                      stock_code="like '600%'")
        stock_code = df['stock_code'].values
        self.assertTrue(all(i[:3] == '600' for i in stock_code))

    # 直连mysql
    # def test_wind_mysql_0(self):
    #     df = self.fd.get_factor_value("WIND_aindexeodprices", factors=['opdate'], s_info_windcode="133333.CSI",
    #                                   s_dq_preclose=[">3000"])
    #     df_len = len(df)
    #     self.assertTrue(df_len > 0)
    #
    # def test_wind_mysql_1(self):
    #     df = self.fd.get_factor_value("WIND_asharemoneyflow",
    #                                   factors=["TRADE_DT", "S_INFO_WINDCODE", "BUY_VALUE_EXLARGE_ORDER"],
    #                                   S_INFO_WINDCODE="603777.SH")
    #     df_len = len(df)
    #     self.assertTrue(df_len > 0)
    #
    # def test_wind_mysql_2(self):
    #     df = self.fd.get_factor_value("WIND_asharemoneyflow",
    #                                   factors=["TRADE_DT", "S_INFO_WINDCODE", "SELL_VALUE_LARGE_ORDER"],
    #                                   SELL_VALUE_LARGE_ORDER=['<=500', '!=0'])
    #     df_len = len(df)
    #     self.assertTrue(df_len > 0)
    #     df1 = df[df['SELL_VALUE_LARGE_ORDER'] > 500]
    #     self.assertTrue(df1.empty)
    #     df2 = df[df['SELL_VALUE_LARGE_ORDER'] == 0]
    #     self.assertTrue(df2.empty)
    #
    # def test_wind_mysql_3(self):
    #     df = self.fd.get_factor_value("WIND_AsHAREPREVIOUSNAME",
    #                                   factors=['S_INfo_WINDCODE', 'begindate', 'enddate', 'opdate'],
    #                                   OPDATE=['>=20090525', '<=20090530'], enddate='is not null')
    #     self.assertTrue(len(df) > 0)
    #     df1 = df[df['enddate'].isnull()]
    #     self.assertTrue(df1.empty)
    #
    # def test_wind_mysql_4(self):
    #     df = self.fd.get_factor_value("WIND_ashareeodprices", factors=['S_INfo_WINDCODE', 'trade_dt'],
    #                                   trade_dt=['20180104', '20180103'], S_INfo_WINDCODE="like '300%'")
    #     self.assertTrue(len(df) > 0)
    #     stock_code = df['S_INfo_WINDCODE'].values
    #     self.assertTrue(all(i[:3] == '300' for i in stock_code))
    #
    # def test_wind_mysql_5(self):
    #     df = self.fd.get_factor_value("GOGOAL_con_forecast_stk",
    #                                   factors=["Tdate", "sTOCK_CODE", "STOCK_NAME", "C1"],
    #                                   con_date=20180102)
    #     self.assertTrue(len(df) > 0)
    #
    # def test_wind_mysql_6(self):
    #     df = self.fd.get_factor_value("GOGOAL_con_forecast_stk",
    #                                   factors=["Tdate", "sTOCK_CODE", "STOCK_NAME", "C1"],
    #                                   stock_name='江南水务')
    #     self.assertTrue(len(df) > 0)
    #
    # def test_wind_mysql_7(self):
    #     df = self.fd.get_factor_value("GOGOAL_con_forecast_stk",
    #                                   factors=["Tdate", "sTOCK_CODE", "STOCK_NAME", "C1"],
    #                                   c1=['>=0.5', '<=1.5'])
    #     self.assertTrue(len(df) > 0)
    #     df1 = df[df['C1'] < 0.5]
    #     self.assertTrue(df1.empty)
    #     df2 = df[df['C1'] > 1.5]
    #     self.assertTrue(df2.empty)
    #
    # def test_wind_mysql_8(self):
    #     df = self.fd.get_factor_value("GOGOAL_con_forecast_stk",
    #                                   factors=["Tdate", "sTOCK_CODE", "STOCK_NAME", "C1"],
    #                                   c1=['<=0.5', '>=1.5'], OR='C1')
    #     self.assertTrue(len(df) > 0)
    #     df1 = df[(df['C1'] > 0.5) & (df['C1'] < 1.5)]
    #     self.assertTrue(df1.empty)
    #
    # def test_wind_mysql_9(self):
    #     df = self.fd.get_factor_value("GOGOAL_con_forecast_stk",
    #                                   factors=["Tdate", "sTOCK_CODE", "STOCK_NAME", "C1"],
    #                                   c1=['<=0.5', '>=1.5'], OR='C1', stock_name="like '江南%'")
    #     self.assertTrue(len(df) > 0)
    #     df1 = df[(df['C1'] > 0.5) & (df['C1'] < 1.5)]
    #     self.assertTrue(df1.empty)
    #     stock_name = df['STOCK_NAME'].values
    #     self.assertTrue(all(i[:2] == '江南' for i in stock_name))
    #
    # def test_wind_mysql_10(self):
    #     df = self.fd.get_factor_value("GOGOAL_con_forecast_stk",
    #                                   factors=["Tdate", "sTOCK_CODE", "STOCK_NAME", "C1", "con_hisdate"],
    #                                   c1=['>=0.5', '<=1.5'], con_hisdate=['!=20171115', 'is not null'],
    #                                   stock_name="like '江南%'")
    #     self.assertTrue(len(df) > 0)
    #     df1 = df[df['con_hisdate'].isnull()]
    #     self.assertTrue(df1.empty)
    #     stock_name = df['STOCK_NAME'].values
    #     self.assertTrue(all(i[:2] == '江南' for i in stock_name))

    def tearDown(self):
        pass
