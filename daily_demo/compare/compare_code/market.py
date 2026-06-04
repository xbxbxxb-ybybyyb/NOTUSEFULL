# _*_ coding:utf-8 _*_
import pandas as pd
import os
from compare_func import list2df, compare, get_relative_day
from xquant.factordata import FactorData
from xquant.marketdata import MarketData as MDC
from xquant.thirdpartydata.marketdata import MarketData
import time


mdc = MDC()
ma = MarketData()
s = FactorData()
# 交易日列表
tradingdays = s.tradingday(20190101, 20191014)[::7]

df_result = pd.DataFrame(columns=['date', 'stock', 'factors', 'true_num', 'false_num'])
df_result.set_index(['date', 'stock','factors'], inplace=True)
data_type = "Stock"
root_path = './'+data_type

tradingdays = ['20200416']
stocks = ['000056.SZ']
for date in tradingdays:
    start_date = date + ' 000000000'
    end_date = date + ' 230000000'

    for stock in stocks:
        new_df = mdc.get_data_by_time_frame('kline1m4zt',stock, start_date, end_date)
        old_df = ma.getKLine4ZTDataFrame(stock, start_date.replace(" ", ""), end_date.replace(" ", ""), 10, 20, True)   

        print(new_df)
        print(old_df)
				        
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


            print(time.time()-t1)
            true_num = len(merge_df[merge_df.result == True])
            false_num = len(merge_df[merge_df.result == False])
            dataset = [true_num, false_num]
            print("date {}, stock {}: factor_name {}, true {}, false {}".format(date, stock, col, true_num, false_num))
            df_result.loc[(date, stock, col), :] = dataset
            if false_num!=0:
                merge_df.to_csv(os.path.join(csv_path, csv_name), index=False)

df_result.to_csv(os.path.join(root_path, 'result.csv'))

