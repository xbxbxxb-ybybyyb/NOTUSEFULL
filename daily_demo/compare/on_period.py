# _*_ coding:utf-8 _*_
import pandas as pd
import os
from compare_func import list2df, compare, get_relative_day
from xquant.factordata import FactorData
from xquant.marketdata import MarketData as MDC
from MDCDataProvider.HBaseProvider import  HBaseProvider  as MHP
from xquant.thirdpartydata.marketdata import MarketData
import time
import random


mdc = MDC()
mhp = MHP()
ma = MarketData()
s = FactorData()
# 交易日列表
tradingdays = s.tradingday(20190101, 20191014)[::7]

df_result = pd.DataFrame(columns=['date', 'stock', 'factors', 'true_num', 'false_num'])
df_result.set_index(['date', 'stock','factors'], inplace=True)
data_type = "onPeriod"
root_path = './'+data_type

tradingdays = ['20200713']
stocks = s.hset('MARKET', '20200713', 'ALLA')['stock'].to_list()
random.shuffle(stocks)
print(stocks)
for date in tradingdays[:1]:
    start_date = date + ' 000000000'
    end_date = date + ' 160000000'
    print(start_date,end_date)

    for stock in stocks[:1]:
        new_df = pd.read_csv('/home/appadmin/onPeriod.csv')
        old_df =pd.read_csv('/home/appadmin/amKline.csv')
        #new_df = new_df.rename(columns = {'OpenPx':'open', 'ClosePx':'close', 'HighPx':'high', 'LowPx':'low', 'NumTrades':'numtrade', 'TotalVolumeTrade':'volume', 'TotalValueTrade':'amt'})
        #old_df['mdtime'] = old_df['mdtime'].apply(lambda x: str(pd.to_datetime(x, format='%Y-%m-%d %H:%M:%S').strftime('%H%M%S'))+'000')
        #old_df['mdtime'] = old_df['mdtime'].astype('float')

        print(new_df['mdtime'])
        print(old_df['mdtime'])

        a = list(new_df.columns)
        b = list(old_df.columns)
        print(set(b)-set(a))
        print("===")
        print(set(a)-set(b))
        #old_df = mdp.get_data_by_date(data_type, stock, date,  sort_by_receive_time=True)
        csv_path = os.path.join(root_path, date, stock)
        if not os.path.exists(csv_path):
            os.makedirs(csv_path)
        for col in old_df.columns:
            print(col)
            if col in ["mdtime","stock", "industry_type"]:
                continue
            csv_name = col + '.csv'
            t1 = time.time()
            if True:
                merge_df = compare(new_df, old_df, ["stock", "mdtime"], [col], ["stock", "mdtime"], [col], sample_ratio = 0.1)

            print(time.time()-t1)
            true_num = len(merge_df[merge_df.result == True])
            false_num = len(merge_df[merge_df.result == False])
            dataset = [true_num, false_num]
            print("date {}, stock {}: factor_name {}, true {}, false {}".format(date, stock, col, true_num, false_num))
            df_result.loc[(date, stock, col), :] = dataset
            if false_num!=0:
                merge_df.to_csv(os.path.join(csv_path, csv_name), index=False)

df_result.to_csv(os.path.join(root_path, 'result.csv'))

