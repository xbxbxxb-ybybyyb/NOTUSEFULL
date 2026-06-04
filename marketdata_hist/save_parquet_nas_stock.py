# -*- coding: utf-8 -*-
import ray
import os
from xquant.marketdata import MarketData
from xquant.factordata import FactorData
import pandas as pd
import time
import os
import pyarrow.parquet as pq
import pyarrow as pa
import time

os.environ['ARROW_LIBHDFS_DIR'] = '/opt/cloudera/parcels/CDH/lib64'
os.environ['HADOOP_CONF_DIR'] = '/etc/hadoop/conf'
os.environ['HADOOP_USER_NAME'] = 'xquant'

#hadoopfs = fs.HadoopFileSystem(\"168.9.65.61\", 8020,user=\"xquant\", kerb_ticket = \"/tmp/krb5cc_1000\")"


ray.init(num_cpus=10)

s = FactorData()

stock_list = s.hset("MARKET", "20201009", "ALLA_HIS")["stock"].to_list()


@ray.remote
def store_data(stock, start_date, end_date):
    mdp = MarketData()

    df = mdp.get_data_by_time_frame("Stock", stock, "{} 073000000".format(start_date), "{} 170000250".format(end_date))
    if df.empty:
        return
    t1 = time.time()
    table = pa.Table.from_pandas(df, preserve_index=False, nthreads=16)
    print("from_pandas:", time.time()-t1, df.shape)
    t1 = time.time()
    try:
        pq.write_to_dataset(table, '/app/data/013150/mkt_test1', partition_cols=['HTSCSecurityID', 'MDDate'],
                            partition_filename_cb=lambda x: '-'.join(
                                list(map(str, x))) + '.parquet')
    except Exception as e:
        print(e)
        pq.write_to_dataset(table, '/app/data/013150/mkt_test1', partition_cols=['HTSCSecurityID', 'MDDate'],
                            partition_filename_cb=lambda x: '-'.join(
                                list(map(str, x))) + '.parquet')
    print("write_to_dataset nas:", time.time()-t1, df.shape)



if __name__ == "__main__":
    for month in range(0,12):
        start_date = str(int('20200101')+100*month)
        end_date = str(int('20200131')+100*month)
        end_date = s.tradingday(start_date, end_date, frequency='MONTH', dayType='LASTDAY', dateType='TRADINGDAYS', location='CN')[0]
        tasks = [store_data.remote(stock, start_date, end_date) for stock in stock_list]
        ray.get(tasks)
        
