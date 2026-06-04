# _*_ coding:utf-8 _*_
import pandas as pd
import os
from compare_func import list2df, compare, get_relative_day
from xquant.factordata import FactorData
from xquant.marketdata import MarketData as MDC
from MDCDataProvider.HBaseProvider_to_MDC import  HBaseProvider_to_MDC  as MHP
from xquant.thirdpartydata.marketdata import MarketData
import time
import random


mdc = MDC()
mhp = MHP()
ma = MarketData()
s = FactorData()
df_result = pd.DataFrame(columns=['date', 'stock', 'factors', 'true_num', 'false_num'])
df_result.set_index(['date', 'stock','factors'], inplace=True)

data_type = "Stock"; root_path = './'+data_type
tradingdays = s.tradingday(20211101, 20211120)
stocks = s.hset('MARKET', '20200713', 'ALLA')['stock'].to_list()
stocks = ['600104.SH']
tradingdays = ["20220406"]
random.shuffle(stocks)
print(stocks)
for date in tradingdays:
    start_date = date + ' 000000000'
    end_date = date + ' 160000000'
    print(start_date,end_date)

    for stock in stocks[:200]:
        new_df = mdc.get_data_by_time_frame(data_type, stock, start_date, end_date)
        print(new_df["ReceiveDateTime"])
        #old_df = mhp.get_data_by_time_frame('Kline1M4ZT', stock, start_date, end_date)
        #old_df = ma.getMDOrderDataFrame(stock, start_date.replace(' ', ''), end_date.replace(' ', ''))
        old_df = mhp.get_data_by_time_frame(data_type, stock, start_date, end_date)


        print(new_df.to_csv('new.csv'))
        print(old_df.to_csv('old.csv'))
        a = list(new_df.columns)
        b = list(old_df.columns)
        print(set(b)-set(a))
        print("===")
        print(set(a)-set(b))
        csv_path = os.path.join(root_path, date, stock)
        if not os.path.exists(csv_path):
            os.makedirs(csv_path)
        for col in old_df.columns:
            if col in ["MDDate", "MDTime", "TradeIndex", "OrderIndex", "HTSCSecurityID","stock", "industry_type", "ApplSeqNum"]:
                continue
            csv_name = col + '.csv'
            t1 = time.time()
            if data_type == "Stock" or data_type == "Index" or data_type == 'Tick':
                merge_df = compare(new_df, old_df, ["MDDate", "MDTime"], [col], ["MDDate", "MDTime"], [col], sample_ratio = 1)
            elif data_type == "Transaction":
                merge_df = compare(new_df, old_df, ["TradeIndex"], [col], ["TradeIndex"], [col], sample_ratio = 0.05)
            elif data_type == "Order":
                if stock.endswith(".SH"):
                    merge_df = compare(new_df, old_df, ["ApplSeqNum"], [col], ["ApplSeqNum"], [col], sample_ratio = 1)
                else:
                    merge_df = compare(new_df, old_df, ["OrderIndex"], [col], ["OrderIndex"], [col], sample_ratio = 1)



            print(time.time()-t1)
            true_num = len(merge_df[merge_df.result == True])
            false_num = len(merge_df[merge_df.result == False])
            dataset = [true_num, false_num]
            print("date {}, stock {}: factor_name {}, true {}, false {}".format(date, stock, col, true_num, false_num))
            df_result.loc[(date, stock, col), :] = dataset
            if false_num!=0:
                merge_df.to_csv(os.path.join(csv_path, csv_name), index=False)

df_result.to_csv(os.path.join(root_path, 'result.csv'))

