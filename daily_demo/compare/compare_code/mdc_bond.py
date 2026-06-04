# _*_ coding:utf-8 _*_
import pandas as pd
import os
from compare_func import list2df, compare, get_relative_day
from MDCDataProvider.DataProvider import DataProvider
from xquant.thirdpartydata.marketdata import MarketData
from xquant.factordata import FactorData
from xquant.bonddata import BondData
import time


type2table = {'STOCK': 'MDStockRecord',
              'INDEX': 'MDIndexRecord',
              'TRANSACTION': 'MDTransactionRecord',
              'ORDER': 'MDOrderRecord',
              'KLINE1M4ZT': 'MDKLine1M4ZT',
              }

# 新增期货表名
type2future = {
    'FUTURETICK': 'MDFutureTickRecord',
    'FUTUREKLINE1M': 'MDFutureKLine1M',
    'FUTUREKLINE1D': 'MDFutureKLine1D'
}

# 新增债券表名
type2bond = {
    'BONDTICK': 'MDBondTickRecord',
    'BONDKLINE1M': 'MDBondKLine1M',
    'BONDKLINE1D': 'MDBondKLine1D',
    'BONDORDER': 'MDBondOrderRecord',
    'BONDTRANSACTION': 'MDBondTransactionRecord',
}
# 新增基金
type2fund = {
    'FUNDTICK': 'MDFundTickRecord',
    'FUNDKLINE1M': 'MDFundKLine1M',
    'FUNDKLINE1D': 'MDFundKLine1D',
}

# 新增基金月数据表
type2fund1 = {
   'FUNDORDER': 'MDFundOrderRecord',
    'FUNDTRANSACTION': 'MDFundTransactionRecord',
}

mdc = DataProvider()
ma = MarketData()
fa = FactorData()
bd = BondData()

root_path = './Bond'
df_result = pd.DataFrame(columns=['date', 'stock', 'factors', 'true_num', 'false_num'])
df_result.set_index(['date', 'stock','factors'], inplace=True)

dates = fa.tradingday(20200101, 20200202)
stocks = bd.get_bond_set('20200415', 'kzz')

#dates = ['20190628','20191226', '20191227','20191230', '20200102', '20200103', '20191226']
#dates = ['20200415']
#stocks = ["110060.SH"]
for date in dates:
    start_date = date + ' 000000000'
    end_date = date + ' 230000000'
    for stock in stocks:
        print(stock)
        csv_path = os.path.join(root_path, date, stock)
        if not os.path.exists(csv_path):
            os.makedirs(csv_path)

        new_df = mdc.get_data_by_time_frame('BONDKLINE1M', stock, start_date, end_date)
        #old_df = ma.getMDSecurityKLineDataFrame (stock, start_date.replace(" ",""), end_date.replace(" ",""), 10,20)
        old_df = ma.getKLine4ZTDataFrame(stock, start_date.replace(" ",""), end_date.replace(" ",""), 10,20)

        if new_df.empty and old_df.empty:
            continue
        print(new_df.shape, old_df.shape)
        
        a = list(new_df.columns)
        b = list(old_df.columns)
        print("new df lack:", set(b)-set(a))
 
        print("===")
        print("old df lack:", set(a)-set(b))
        
        for col in old_df.columns:
            if col in ["MDDate", "MDTime", "TradeIndex", "OrderIndex", "HTSCSecurityID"]:
                continue
            csv_name = col + '.csv'
            t1 = time.time()
            merge_df = compare(new_df, old_df, ["MDDate", "MDTime"], [col], ["MDDate", "MDTime"], [col], sample_ratio = 1)


            print(time.time()-t1)
            true_num = len(merge_df[merge_df.result == True])
            false_num = len(merge_df[merge_df.result == False])
            dataset = [true_num, false_num]
            print("date {}, stock {}: factor_name {}, true {}, false {}".format(date, stock, col, true_num, false_num))
            df_result.loc[(date, stock, col), :] = dataset
            if false_num!=0:
                merge_df.to_csv(os.path.join(csv_path, csv_name), index=False)

df_result.to_csv(os.path.join(root_path, 'result.csv'))

