# -*- coding: utf-8 -*-
# import ray
# from xquant.marketdata import MarketData
from xquant.factordata import FactorData
import pandas as pd
import time
import os
import pyarrow.parquet as pq
import pyarrow as pa
from pyarrow import fs
import pyarrow.dataset as ds

os.environ['ARROW_LIBHDFS_DIR'] = '/opt/cloudera/parcels/CDH/lib64'
os.environ['HADOOP_CONF_DIR'] = '/etc/hadoop/conf'
os.environ['HADOOP_USER_NAME'] = 'xquant'
s = FactorData()
all_stocks = s.hset("MARKET", "20201009", "ALLA_HIS")["stock"].to_list()
sample_df = pq.read_table(
        "/data/user/013150/marketdata_hist/mkt_test1/HTSCSecurityID=000001.SZ",
        filters=[('MDDate', '=', 20200302)],
        use_legacy_dataset = True).to_pandas()
df_columns = sample_df.columns.values.tolist()
sample_ds = pq.ParquetDataset("/data/user/013150/marketdata_hist/mkt_test1/HTSCSecurityID=000001.SZ")
sample_schema = sample_ds.schema
schema_list = []
schema_type_dict = {'INT32': pa.int32(), 'INT64': pa.int32(), 'BYTE_ARRAY': pa.string(), 'DOUBLE': pa.float64()}
for sc in sample_ds.schema:
    name = sc.name
    p_type = sc.physical_type
    schema_list.append((name, schema_type_dict[p_type]))


def read_table_hdfs(hdfs, stocks, start_date, end_date, columns):
    for stock in stocks:
        table = pq.read_table(
            "/analysis/xquant/013150/mkt_test1/HTSCSecurityID={}".format(stock),
            columns=columns, filters=[('MDDate', '>=', int(start_date)), ('MDDate', '<=', int(end_date))],
            filesystem=hdfs, use_legacy_dataset=True)
        df = table.to_pandas()


def read_table_nas(stocks, start_date, end_date, columns):
    for stock in stocks:
        table = pq.read_table(
            "/data/user/013150/marketdata_hist/mkt_test1/HTSCSecurityID={}".format(stock),
            columns=columns, filters=[('MDDate', '>=', int(start_date)), ('MDDate', '<=', int(end_date))],
            filesystem=hdfs, use_legacy_dataset=True)
        df = table.to_pandas()


def from_paths_hdfs(hdfs_fs, stocks, dates, schemas):
    for stock in stocks:
        file_paths = ["HTSCSecurityID={0}/MDDate={1}/{0}-{1}.parquet".format(stock, date) for date in dates]
        partitions = [ds.field("MDDate") == date for date in dates]
        dataset = ds.FileSystemDataset.from_paths(file_paths, schema=schemas,
            format=ds.ParquetFileFormat(), filesystem=fs.SubTreeFileSystem(
                "/analysis/xquant/013150/mkt_test1", hdfs_fs),
            partitions=partitions)
        df = dataset.to_table().to_pandas()


def from_paths_nas(stocks, dates, schemas):
    for stock in stocks:
        file_paths = ["HTSCSecurityID={0}/MDDate={1}/{0}-{1}.parquet".format(stock, date) for date in dates]
        partitions = [ds.field("MDDate") == date for date in dates]
        dataset = ds.FileSystemDataset.from_paths(file_paths, schema=schemas,
            format=ds.ParquetFileFormat(), filesystem=fs.SubTreeFileSystem(
                "/data/user/013150/marketdata_hist/mkt_test1",
                fs.LocalFileSystem()), partitions=partitions)
        df = dataset.to_table().to_pandas()


if __name__ == "__main__":
    hdfs = pa.hdfs.connect('168.9.65.62', 8020)
    hdfs_fs = fs.HadoopFileSystem('168.9.65.62')
    stocks = all_stocks[:20]
    start_date = '20200101'
    end_date = '20200131'
    columns = df_columns[0:47] + ['MDDate', 'HTSCSecurityID']
    dates = s.tradingday(start_date, end_date)
    schemas = pa.schema(schema_list[0:48] + [("MDDate", pa.string())])
    t1 = time.time()
    read_table_hdfs(hdfs, stocks, start_date, end_date, columns)
    t2 = time.time()
    print('hdfs read_table: ' + str(t2 - t1))
    read_table_nas(stocks, start_date, end_date, columns)
    t3 = time.time()
    print('nas read_table: ' + str(t3 - t2))
    from_paths_hdfs(hdfs_fs, stocks, dates, schemas)
    t4 = time.time()
    print('hdfs from_paths: ' + str(t4 - t3))
    from_paths_nas(stocks, dates, schemas)
    t5 = time.time()
    print('nas from_paths: ' + str(t5 - t4))