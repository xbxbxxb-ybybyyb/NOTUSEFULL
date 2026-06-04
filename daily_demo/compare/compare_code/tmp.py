# _*_ coding:utf-8 _*_
import pandas as pd
import os
from compare_func import list2df, compare, get_relative_day
from xquant.factordata import xqfactor
from xquant.factordata import xqfactor1
from xquant.factordata import FactorData
import time


s = FactorData()
# 交易日列表
tradingdays = s.tradingday(20190101, 20191014)[::7]

df_result = pd.DataFrame(columns=['date', 'stock', 'factors', 'true_num', 'false_num'])
df_result.set_index(['date', 'stock','factors'], inplace=True)
data_type = "hsi"
root_path = './'+data_type
for date in tradingdays:
    stocks = s.hset('MARKET', date, 'ALLA')["stock"].tolist()
    for stock in stocks:
        new_df = xqfactor1.hsi(stocks, date, industryLevel=2, industryType="SW")
        old_df = xqfactor.hsi(stocks, date, industryLevel=2, industryType="SW")
				        
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
            if col in ["MDDate", "MDTime", "TradeIndex", "OrderIndex", "HTSCSecurityID","stock", "industry_type"]:
                continue
            csv_name = col + '.csv'
            t1 = time.time()
            if data_type == "Stock" or data_type == "Index":
                merge_df = compare(new_df, old_df, ["MDDate", "MDTime"], [col], ["MDDate", "MDTime"], [col], sample_ratio = 0.01)
            elif data_type == "Transaction":
                merge_df = compare(new_df, old_df, ["TradeIndex"], [col], ["TradeIndex"], [col], sample_ratio = 0.05)
            else:
                merge_df = compare(new_df, old_df, ["stock", "industry_type"], [col], ["stock", "industry_type"], [col], sample_ratio = 1)


            print(time.time()-t1)
            true_num = len(merge_df[merge_df.result == True])
            false_num = len(merge_df[merge_df.result == False])
            dataset = [true_num, false_num]
            print("date {}, stock {}: factor_name {}, true {}, false {}".format(date, stock, col, true_num, false_num))
            df_result.loc[(date, stock, col), :] = dataset
            if false_num!=0:
                merge_df.to_csv(os.path.join(csv_path, csv_name), index=False)

df_result.to_csv(os.path.join(root_path, 'result.csv'))

