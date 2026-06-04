import cx_Oracle
import os
import pandas as pd



server = "168.9.65.8"    # Á¬½Ó·þÎñÆ÷µØÖ·
user = "xquant_wind"
password = "qEK%wH2f7KE#fX^o"
user = 'xquant_data'
password = 'jy0C1K*#x^VOmMaB'
user = 'xquant'
password='b%GW0Z8mt#7uY8@w'

import pymysql
conn = pymysql.connect(host  = server, user  = user, passwd = password, port = 3326, db = user, charset = 'utf8')  #»ñÈ¡Á¬½Ó

import numpy as np
import time
for table in [ 'tasset']:#['exchangeorder', 'execution', 'position', 'fund', 'positionext', 'tstockinfo', 'tasset', 'tcombi', 'tfundinfo']:
    sql = '''select a.* from gem_job a join xq_oa_user b on a.user_account=b.user_account 
where job_status=1 and job_type=4 and team in ("证券投资部", "股票策略交易团队","因子管理系统", "金融工程团队", "智能算法团队", "系统研发团队", "宏观对冲团队2","量化投资团队")
and a.resource_config like "%dol_gene%"
order by user_account'''
    df = pd.read_sql(sql, conn)
    print(table, df)
    df.to_parquet('/data/user/013150/tmp/gem_job.pqt')


raise Exception()


