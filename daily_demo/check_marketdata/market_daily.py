import ray
ray.init(num_cpus = 10)
import pandas as pd
#pd.set_option('display.max_columns', None)
from MDCDataProvider import DataProvider as MarketData
from MDCDataProvider import HBaseProvider_to_MDC as MarketData1
from xquant.factordata import FactorData
from xquant.bonddata import BondData
from xquant.xqutils.xqlog.logger import setup_logging
import time
import datetime
from retrying import retry

#ma = MarketData()
#ma1 = MarketData1()
fa = FactorData()
bd = BondData()

today = '20210326'#datetime.datetime.now().strftime('%Y%m%d')
start_date = today
end_date = today


month_days = fa.tradingday(start_date, end_date, frequency = 'MONTH')
days = fa.tradingday(start_date, end_date)
stocks = fa.hset('MARKET', end_date, "ALLA_HIS")['stock'].tolist()
bonds = bd.get_bond_set(end_date, 'kzz')
#print('bonds: ', bonds)
table_types = ['STOCK','INDEX','TRANSACTION','ORDER','KLINE1M4ZT','BONDTICK','BONDKLINE1M','BONDORDER','BONDTRANSACTION']#,'FUTURETICK','FUTUREKLINE1M','FUTUREKLINE1D', 'BONDKLINE1D']


@ray.remote
@retry(stop_max_attempt_number=5, wait_fixed=2000)
def check_hdfs_data(stock, table, month_days, idx):
    ma = MarketData()
    ma1 = MarketData1()
    fa = FactorData()
    bd = BondData()

    for month in month_days:
        df_hdfs = ma.get_data_by_year_month(table, stock, month[:-2])
       
        #print(df_hdfs)
        for day in days:
            if day[:-2]!=month[:-2]:
                continue
            df_hbase = ma1.get_data_by_date(table, stock, day)
            print('df_hbase',df_hbase.shape)
            if df_hbase.empty:
                continue
            if df_hdfs.empty:
                if not len(df_hbase)<500 and table=='STOCK':
                    print('{} {} {} data not consist: hdfs {} vs hbase {}!'.format(day, table, stock, 0, len(df_hbase)), idx)
                continue
            tmp_df_hdfs = df_hdfs[df_hdfs['MDDate']==day]
            if tmp_df_hdfs.empty:
                if not len(df_hbase)<500 and tbble =='STOCK':
                    print('{} {} {} data not consist: hdfs {} vs hbase {}!'.format(day, table, stock, 0, len(df_hbase)), idx)
                continue
            df_hbase = df_hbase[(df_hbase['MDTime']>='093000000') & (df_hbase['MDTime']<='150000000')]
            df_hbase = df_hbase[(df_hbase['MDValidType']=='Valid') | (pd.isnull(df_hbase['MDValidType']))]
            tmp_df_hdfs = tmp_df_hdfs[(tmp_df_hdfs['MDTime']>='093000000') & (tmp_df_hdfs['MDTime']<='150000000')]
            
            #print(df_hbase)
            if len(df_hbase) <= len(tmp_df_hdfs):#df_hbase['MDTime'].iloc[0] == tmp_df_hdfs['MDTime'].iloc[0]:
                continue
                #print('ok')
            else:
                if len(df_hbase) == len(tmp_df_hdfs)+1 or len(df_hbase)<500:
                    continue
                #print(tmp_df_hdfs)
                df_hbase.to_csv("df_hbase_{}_{}_{}.csv".format(day, table, stock))
                tmp_df_hdfs.to_csv('df_hdfs_{}_{}_{}.csv'.format(day, table, stock))
                #raise Exception()
                print('{} {} {} data not consist: hdfs {} vs hbase {}!'.format(day, table, stock, len(tmp_df_hdfs), len(df_hbase)), idx)
                #print(df_hbase)


for table in table_types[2:]:
    print('table:', table)
    if table in ['STOCK','INDEX','TRANSACTION','ORDER','KLINE1M4ZT']:
        securities = stocks
    elif table in ['BONDTICK','BONDKLINE1M','BONDORDER','BONDTRANSACTION']:
        securities = bonds
    elif table in ['FUTURETICK','FUTUREKLINE1M']:
        securities = None
    else:
        raise Exception('no securities!')
    
    tasks = [check_hdfs_data.remote(secu, table, month_days, sidx) for sidx,secu  in enumerate(securities)] 
    ray.get(tasks)





