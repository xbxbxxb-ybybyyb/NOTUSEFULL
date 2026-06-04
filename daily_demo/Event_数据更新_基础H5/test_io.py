print('test')
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
import pandas as pd
from xquant.factordata import FactorData
from xquant.thirdpartydata.marketdata import MarketData
from update_wind import MD
# import os
s = FactorData()
# ma = MarketData()
# date = 20161231
# df = s.get_factor_value('WIND_AShareANNFinancialIndicator',report_period=[str(date)])
# print(df)
# df.to_csv('/data/user/015623/code.csv',encoding='gbk')
# df1 = s.get_factor_value('Basic_factor', stock = ['000001.SZ'], mddate = ['20180808', '20180809'], factor_names = ['numtrade_minute'])
# print(df1)
# dates = s.tradingday('20150101','20191231',frequency='QUARTER',dateType='ALLDAYS')
# df = s.get_factor_value("Basic_factor", [], dates, ['stm_issuingdate'] )# date_test = 20181228
# df = df.unstack()
# print(dates)
# print(df)
# print(dates)
# path_test = '/data/user/015518/quant_data/qualified_factor/x_day_lib/20190630'
# data = pd.read_parquet(path_test,columns=['mddate','stock','MinuteIlliqVwapClose5d','GTJA_007'])
# data.set_index(['mddate','stock'],inplace=True)
# print(data)
# data.to_csv('/data/user/015623/test.csv')

 
dat_uni = IO.read_data(["20250221", "20250221"], columns=['amt', 'total_shares'], alt = '/data/group/800080/warehouse/prod/MD/CHINA_STOCK/DAILY/WIND/MD_CHINA_STOCK_DAILY_WIND.h5')
print(dat_uni)

# file_path = '/data/group/800080/warehouseJG/prod/MD/CHINA_STOCK/DAILY/WIND/MD_CHINA_STOCK_DAILY_WIND.h5'
file_path = '/data/group/800080/warehouse/prod/MD/CHINA_STOCK/DAILY/WIND/MD_CHINA_STOCK_DAILY_WIND.h5'
with pd.HDFStore(file_path,'r') as h5:
    for key in ['adjfactor', 'amt', 'close', 'free_float_shares', 'high', 'low', 'mkt_cap_ard', 'open', 'pct_chg', 'pre_close', 'total_shares', 'turn', 'volume', 'vwap']:
        try:
            print(key, end = ",")
            df = h5[key].loc[pd.Timestamp("20250220")]
            all_shape = df.shape[0]
            print(df.shape)
        except Exception as e:
            print(e)
# def cronb(self):
#     # self.retriever()
#     self.csv_to_database()

# MD.cronb = cronb
# md = MD(20250220, 20250220)
# md.cronb()
