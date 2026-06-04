# -*- coding: utf-8 -*-
import ray
from xquant.marketdata import MarketData
from xquant.factordata import FactorData
import sys

s = FactorData()
mdp = MarketData()

stock_list = s.hset("MARKET", "20180808","ALLA")["stock"]

ray.init(num_cpus=20, object_store_memory=100*1000000000)
@ray.remote
def ray_get_data(stock,date):
    mdp = MarketData()
    df = mdp.get_data_by_time_frame("Stock", stock,"20180301 093000000", "20180410 150000250")
    #df.to_pickle("new_tmp/{}.pkl".format(stock))a
    import time
    import pyarrow as pa
    import pyarrow.parquet as pq
    for col in df.columns:
        if col in ['MDDate', 'SecurityID']:
            continue
        tmp_df = df.loc[:,['MDDate', 'SecurityID', col]]#loc约3秒
        tmp_df["col"] = col
        tmp_df = tmp_df.rename(columns = {col:"value"})
        print(col, tmp_df.shape, tmp_df.columns)
        t1 = time.time()
        #%time table = pa.Table.from_pandas(tmp_df, preserve_index= False, nthreads = 16)#pyarrow1.0.1，约10s。约两分半钟
        #%time pq.write_to_dataset(table, "/data/user/013150/marketdata_hist/mkt_test16", partition_cols=['MDDate', 'SecurityID','col'])#pyarrow1.0.1，约80秒
    
        tmp_df.to_parquet("/app/data/013150/marketdata_hist/mkt_all_tmp", partition_cols=['MDDate', 'SecurityID','col'], engine='pyarrow')
        print(time.time()-t1)
    
if __name__=="__main__":
    tasks_id = [ray_get_data.remote(i,"20190701") for i in stock_list]
    ray.get(tasks_id)

