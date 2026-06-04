# _*_ coding:utf-8 _*_
import re
import numpy as np
import pandas as pd
from tables import *
from Wind.utils import *

xml_path = "config-h5.xml"
sql_config = get_sql_config(xml_path)
print(sql_config)

#sql = "select * from WIND.ASHAREEODPRICES where trade_dt='19960102'"
sql = "select * from gogoal_new.stock_report_number where tdate = '20191125'"
# sql = "select owner from dba_tables where table_name= 'ASHAREEODPRICES'"
df = queryUserTableData(sql,sql_config)
print(df)






