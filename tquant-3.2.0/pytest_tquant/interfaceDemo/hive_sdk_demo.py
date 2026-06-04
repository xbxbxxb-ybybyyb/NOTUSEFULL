#! /usr/bin/env python3
#-*- coding:utf-8 -*-

import pandas as pd
import numpy as np
import random
from htds.dataset.service.sdk import *

# 执行单句sql
def sdk_execute():
	ds_name = "dw-bigdata-hive"
	sql_string = "create table if not exists test.sdk1_helper  stored as parquet as SELECT * from test_yiwen.fmj_0115_6 limit 100"
	htdsc = HTDSContext()
	sql_execute = htdsc.get_public_datasource(ds_name)
	sql_execute.execute(sql_string,ret=False)
	### with ret
	#sql_string = "select * from test.sdk1_helper limit 100"
	#sql_execute = htdsc.get_public_datasource(ds_name)
	#print(sql_execute.execute(sql_string,ret=True).head())


# 同时执行多句sql
def sdk_execute_many():
    ds_name = "dw-bigdata-hive"
    sql_string_list = [ "create table if not exists test.sdk1_helper  stored as parquet as SELECT * from test_yiwen.fmj_0115_6 limit 100","INSERT into test.sdk1_helper select round(1*rand()), round(10*rand()), 10*rand(), 10*rand(), 10*rand(), 'Beijing is a big city', '中国银行', '610222', '2021-02-22'  from test_yiwen.fmj_01291 limit 10"]
    htdsc = HTDSContext()
    sql_execute = htdsc.get_public_datasource(ds_name)
    sql_execute.execute_many(sql_string_list)


# 仅支持impala 数据上传到hive后可执行该方法 即可使用impala查询
def sdk_impala_flush():
	ds_name = "dw-bigdata-impala"
	htdsc = HTDSContext()
	sql_execute_impala = htdsc.get_public_datasource(ds_name)
	sql_execute_impala.impala_flush("test", "sdk1_helper")

# 获取数据库连接
def sdk_get_conn():
	ds_name = "dw-bigdata-impala"
	htdsc = HTDSContext()
	sql_execute_impala = htdsc.get_public_datasource(ds_name)
	engine = sql_execute_impala.get_conn()


# 查询数据
def sdk_query():
	ds_name = "dw-bigdata-hive"
	sql_string = "select * from test.sdk1_helper limit 100"
	htdsc = HTDSContext()
	sql_execute = htdsc.get_public_datasource(ds_name)
	print(sql_execute.query(sql_string).head())


# 仅支持查询impala 用于查询大量数据
def sdk_query_table():
	ds_name = "dw-bigdata-impala"
	db_name = "test"
	tb_name = "sdk1_helper"
	htdsc = HTDSContext()
	ds_conn = htdsc.get_public_datasource(ds_name)
	print(ds_conn.query_table(db_name, tb_name))



# 上传文件到hdfs
def sdk_hdfs_upload():
	ds_name = "dw-bigdata-hdfs"
	df = pd.DataFrame(np.array(random.sample(range(1, 100), 16)).reshape(4, 4), columns=['a', 'b', 'c', 'd'])
	hdfs_path = "/tmp/"
	htdsc = HTDSContext()
	sql_execute = htdsc.get_public_datasource(ds_name)
	sql_execute.hdfs_upload(df, hdfs_path, file_name="sdk_helper")


# 从hdfs下载
def sdk_hdfs_download():
	ds_name = "dw-bigdata-hdfs"
	hdfs_path = "/tmp/sdk_helper.parquet"
	local_path = "."
	htdsc = HTDSContext()
	sql_execute = htdsc.get_public_datasource(ds_name)
	sql_execute.hdfs_download(hdfs_path, local_path)


# 上传普通表到hive
def sdk_hive_upload():
	df = pd.DataFrame(np.array(random.sample(range(1, 100), 16)).reshape(4, 4), columns=['a', 'b', 'c', 'd'])
	ds_name = "dw-bigdata-hive"
	db_name = "test"
	tb_name = "sdk_helper"
	htdsc = HTDSContext()
	sql_execute_upload = htdsc.get_public_datasource(ds_name)
	sql_execute_upload.hive_upload(df, db_name, tb_name, overwrite=True)


# 使用临时中间表 上传数据到hive
def sdk_hive_upload_with_temp():
	df = pd.DataFrame(np.array(random.sample(range(1, 100), 9)).reshape(3, 3), columns=['a', 'c', 'b'])
	ds_name = "dw-bigdata-hive"
	db_name = "test"
	tb_name = "sdk_helper"
	htdsc = HTDSContext()
	sql_execute_upload = htdsc.get_public_datasource(ds_name)
	sql_execute_upload.hive_upload_with_temp(df, db_name, tb_name, overwrite=False)
	df11 = sql_execute_upload.query('select * from {}.{} limit 100'.format(db_name, tb_name)).head(10)
	print(df11)


# 上传动态分区表到hive
def sdk_hive_upload_with_partition():
	df = pd.DataFrame(np.array(random.sample(range(1, 100), 16)).reshape(4, 4), columns=['a', 'b', 'c', 'd'])
	ds_name = "dw-bigdata-hive"
	db_name = "test"
	tb_name = "sdk_helper2"
	partitions = ['c', 'd']
	htdsc = HTDSContext()
	sql_execute_upload = htdsc.get_public_datasource(ds_name)
	sql_execute_upload.hive_upload_with_partition(df, db_name, tb_name, partitions)
	#sql_execute_upload.hive_upload_with_partition(df, db_name, tb_name, partitions, overwrite=True)



# 更快的上传分区表到hive
def sdk_df_upload_hive_partition():
	df = pd.DataFrame(np.array(np.random.randint(30,size=40)).reshape(10, 4), columns=['a', 'b', 'c', 'd'])
	# df = pd.DataFrame({'a':[11,11,11],'b':[22,22,22],'c':[29,18,18],'d':[15,19,19]})
	df['e']='20210113'
	print(df.head(20))
	ds_name = "dw-bigdata-hive"
	db_name = "test"
	tb_name = "sdk_helper3"
	partitions = ['e']
	htdsc = HTDSContext()
	sql_execute = htdsc.get_public_datasource(ds_name)
	#sql_execute.df_upload_hive_partition(df, db_name, tb_name, partitions)
	#动态分区表数据插入
	#动态分区表覆盖分区相同的数据（只覆盖分区字段相同的数据）
	#sql_execute.df_upload_hive_partition(df, db_name, tb_name, partitions, overwrite=False)
	#动态分区表先删除，后插入（全表覆盖）
	sql_execute.df_upload_hive_partition(df, db_name, tb_name, partitions, overwrite_all=True)
	df11 = sql_execute.query('select * from {}.{} limit 100'.format(db_name, tb_name)).head(100)
	print(df11)

if __name__=='__main__':
	sdk_execute()
	#sdk_execute_many()
	#sdk_impala_flush()
	#sdk_get_conn()
	#sdk_query()
	#sdk_query_table()
	#sdk_hdfs_upload()
	#sdk_hdfs_download()
	#sdk_hive_upload()
	#sdk_hive_upload_with_temp()
	#sdk_hive_upload_with_partition()
	#sdk_df_upload_hive_partition()