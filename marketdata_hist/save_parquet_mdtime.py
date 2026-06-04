# -*- coding: utf-8 -*-
from xquant.marketdata import MarketData
from xquant.factordata import FactorData
import pandas as pd
import numpy as np
import time
import os
import pyarrow.parquet as pq
import pyarrow as pa
import shutil
import time

s = FactorData()
mdp = MarketData()

# stock_list = ['000001.SZ', '000002.SZ', '000004.SZ', '000007.SZ', '002693.SZ', '002694.SZ', '002715.SZ']
# stock_dict = {'000001.SZ': '0', '000002.SZ': '1', '000004.SZ': '2', '002693.SZ': '3', '002694.SZ': '4', '002715.SZ': '5'}
stock_list = s.hset("MARKET", "20201009", "ALLA_HIS")["stock"].to_list()
stock_dict = dict(zip(stock_list, [str(i) for i in list(range(len(stock_list)))]))


def get_data(stock_dict, start_date, end_date):
    if not os.path.exists('/app/data/013150/tmp_pickle'):
        os.mkdir('/app/data/013150/tmp_pickle')

    stocks = []
    
    for stock, idx in stock_dict.items():
        stocks.append(stock)
        # tmp_data(stock, start_date, end_date)
    store_data(stocks, start_date, end_date)


def tmp_data(stock, start_date, end_date):
    mdp = MarketData()
    df = mdp.get_data_by_time_frame("Stock", stock, "{} 093000000".format(start_date), "{} 150000250".format(end_date))
    df.to_pickle('/app/data/013150/tmp_pickle/{}.pickle'.format(stock))


def store_data(stocks, start_date, end_date):
    date_list = s.tradingday(start_date, end_date)
    root_path = '/app/data/013150/mkt_monthly_test'
    df_dict = {}
    t1 = time.time()
    tmp_stock = None
    for sidx, stock in enumerate(stocks[:2000]):
        df = pd.read_pickle('/app/data/013150/tmp_pickle/{}.pickle'.format(stock))
        if not df.empty and not tmp_stock:
            tmp_stock = stock
        df_dict[stock] = df
        print(sidx)
    print("stock read pickle: ", time.time()-t1)
    
    columns = []
    df = df_dict[tmp_stock]
    for col in df.columns:
        if col in ['MDDate', 'SecurityID', 'MDtime']:
            continue
        try:
            df[col].astype(float)
            columns.append(col)
        except Exception as e:
            print(df.shape,e)
            print("【not float】：{}".format(col)) 
            continue


    for date in date_list:
        for col in columns:

            t1 = time.time()
            # result_df = pd.DataFrame(columns=['Factor', 'MDDate'] + [str(i) for i in range(5000)])
            # print('create_df:',time.time() - t1)
            result_df_list = []
            longest_row = 0
            t1 = time.time()
            for stock in stocks[:2000]:
                # df = pd.read_pickle('/app/data/013150/tmp_pickle/{}.pickle'.format(stock))
                df = df_dict[stock]
                if df.empty:
                    continue
                df = df[df['MDDate'] == date]
                df = df.set_index("MDTime")
                tmp_df = df.loc[:, ['MDDate', 'SecurityID', col]]  # loc约3秒
                tmp_df["Factor"] = col
                tmp_df = tmp_df.rename(columns={col: "value"})
                tmp_df["value"] = tmp_df["value"].astype(float)
                values = tmp_df.iloc[:, 2]
                # if len(values) > longest_row:
                #     t1 = time.time()
                #     longest_row = len(tmp_df["value"])
                #     add_rows_length = longest_row - len(result_df)
                #     new_row = pd.Series({"MDDate": date, 'Factor': col})
                #     new_rows = [new_row for i in range(add_rows_length)]
                #     result_df = result_df.append(new_rows, ignore_index=True)
                #     print('append_rows:',time.time() - t1)
                # idx = stock_dict[stock]
                # result_df[idx] = values

                values.rename(columns = {"value":stock}, inplace= True)
                result_df_list.append(values)
            print("for stock:", time.time()-t1)
            t1 = time.time()
            result_df_final = pd.concat(result_df_list, axis = 1)
            result_df_final["Factor"] = col
            result_df_final["MDDate"] = date
            print('{} concat:'.format(col), time.time() - t1, result_df_final.shape)
            # print(result_df.head())
            # print(col, result_df.shape, result_df.columns)
            t1 = time.time()
            table = pa.Table.from_pandas(result_df_final, preserve_index=True,
                                         nthreads=16)
            pq.write_to_dataset(table, root_path,
                                partition_cols=['Factor', 'MDDate'],
                                partition_filename_cb=lambda x: '-'.join(
                                    list(map(str, x))) + '.parquet')
            print("write_to_dataset:", time.time()-t1)

if __name__ == "__main__":
    start_date = '20190801'
    end_date = '20190831'
    get_data(stock_dict, start_date, end_date)

