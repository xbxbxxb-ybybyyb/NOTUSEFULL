import os
import pandas as pd

os.system("export NLS_LANG='SIMPLIFIED CHINESE_CHINA.ZHS16GBK'")
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK'
#print(cx_Oracle.clientversion())
#conn = cx_Oracle.connect("center_admin/CE_ad_1120@168.61.2.4:1521/gbk")


#aws connection
#jdbc:oracle:thin:@qdb04-000285.cbegq5uaeort.rds.cn-north-1.amazonaws.com.cn:1521:QDB04
#connstr = 'center_read/Htsc_Htzx@qdb04-000285.cbegq5uaeort.rds.cn-north-1.amazonaws.com.cn:1521/QDB04'


#connstr = 'QUANTPF/QUANTPF@168.9.2.43:1521/QDB05'

#创建sql会话
#cursor = conn.cursor()

#执行sql语句
#sql = "select * from wind.aindexeodprices where trade_dt = '20200107' and s_info_windcode='000001.SH'"
#sql = "select S_INFO_WINDCODE, REPORT_PERIOD, S_FA_EXINTERESTDEBT_CURRENT, S_FA_EXINTERESTDEBT_NONCURRENT, S_STM_IS from wind.AShareFinancialIndicator where report_period>'20150101' and report_period<='20201231'"
#sql = "select S_INFO_WINDCODE, REPORT_PERIOD, FREE_CASH_FLOW, STATEMENT_TYPE,NET_PROFIT,NET_CASH_FLOWS_OPER_ACT,NET_CASH_FLOWS_INV_ACT, NET_INCR_CASH_CASH_EQU,ANN_DT from wind.AShareCashFlow where report_period>'20150101' and report_period<='20201231'"
#sql = "select S_INFO_WINDCODE,REPORTING_PERIOD,RESEARCH_INST_NAME,EST_DT,S_EST_PE from wind.AShareEarningEst where REPORTING_PERIOD>'20090101' and REPORTING_PERIOD<='20201231'"

#sql = "select S_INFO_WINDCODE, REPORT_PERIOD, STATEMENT_TYPE, NET_PROFIT_INCL_MIN_INT_INC, NET_PROFIT_EXCL_MIN_INT_INC from wind.AShareIncome where report_period>'20140101' and report_period<='20201231'"

#sql = "select S_INFO_WINDCODE, REPORT_PERIOD, STATEMENT_TYPE, ACCT_PAYABLE, TAXES_SURCHARGES_PAYABLE, OTH_CUR_LIAB, OTH_CUR_ASSETS, INVENTORIES, ACCOUNTS_RECEIVABLE,ACCOUNTS_RECEIVABLE_BILL,OTH_RCV_TOT,LONG_TERM_REC,NOTES_RCV,ACCT_RCV,OTH_RCV,INT_RCV from wind.AShareBalanceSheet where report_period>'20140101' and report_period<='20201231'"
#sql = "select S_INFO_WINDCODE, TRADE_DT,  NET_PROFIT_PARENT_COMP_LYR from wind.AShareEODDerivativeIndicator where TRADE_DT>'20140101' and TRADE_DT<='20201231'"


#sql = "select id,mediacode,medianame,textcategory,pubdate,writingdate,texttitle,subtitle,keywords,comcode,comname,authors,reportlevel,infolevel,entrytime,updatetime,groundtime,resourceid,recordid,workno,status,reportid,updateid,rank,expirationdate from center_admin.text_basicinfo a where a.updatetime>to_date('20220608000000', 'YYYYmmddHH24MISS') and  a.updatetime<=to_date('20220608235959', 'YYYYmmddHH24MISS')"# or a.updatetime>to_date('20211027', 'YYYYmmdd') and  a.updatetime<=to_date('20211109235959', 'YYYYmmddHH24MISS')"



#sql = "select * from center_admin.pub_tradingday where tradingday > to_date('20211231', 'YYYYmmdd')"

#df.to_pickle("AShareCashFlow.pkl")
#df.to_pickle("AShareEODDerivativeIndicator.pkl")
#df.to_pickle("AShareBalanceSheet.pkl")
#df.to_pickle("text_basicinfo09.pkl")
#df = pd.read_pickle("text_basicinfo09.pkl")
#print(df)

#engine = sqlalchemy.create_engine("mysql+pymysql://xquant_wind:qEK%wH2f7KE#fX^o@168.9.65.8:3326/xquant_wind?charset=utf8")
#engine = sqlalchemy.create_engine("mysql+pymysql://htsc_dwa_quant:X7_mJw12m8UW@168.15.241.39:3306/htsc_dwa_quant?charset=utf8")

#conn = pymysql.connect(host  = server, user  = user, passwd = password, port = 3306, db = 'htsc_dwa_quant', charset = 'utf8')  #»ñÈ¡Á¬½Ó

server = "168.9.65.8"    # Á¬½Ó·þÎñÆ÷µØÖ·
user = "xquant_wind"
password = "qEK%wH2f7KE#fX^o"
user = 'xquant_data'
password = 'jy0C1K*#x^VOmMaB'
import pymysql
conn = pymysql.connect(host  = server, user  = user, passwd = password, port = 3326, db = user, charset = 'utf8')  #»ñÈ¡Á¬½Ó
cursor = conn.cursor() # »ñÈ¡¹â±ê

import numpy as np
#df = df.fillna(99999)
#df = df.replace(99999, None)
import time
#time.sleep(500)
if True:#for table in [ 'tasset', 'tcombi', 'tfundinfo']:#['exchangeorder', 'execution', 'position', 'fund', 'positionext', 'tstockinfo', 'tasset', 'tcombi', 'tfundinfo']:
    sql = 'select * from factor_d_marketindex where tdate between 20230605 and 20230609 and mdc_adjfactor is not null'
    df = pd.read_sql(sql, conn)
    df.to_parquet('/data/user/013150/tmp/{}.pqt'.format("mdc"))


raise Exception()

df['EXPIRATIONDATE'] = None
df['WRITINGDATE'] = None
df['mediacode'.upper()]=None
df['reportlevel'.upper()]=None
df['status'.upper()]=None
df['reportid'.upper()]=None

#df = df.replace(None, 'NULL')

for row_id, row in df.iterrows():
    values = list(row.values)
    values.extend(values)
    values1 = []
    for v in values:
        if v is None or pd.isnull(v):
            values1.append('NULL')
        else:
            if str(v).startswith('2022-') or str(v).startswith('2021-') or str(v).startswith('2020-') or str(v).startswith('2019-') or str(v).startswith('2018-') or str(v).startswith('2017-') or str(v).startswith('2016') or str(v).startswith('2015-') or str(v).startswith('2014-'):
                v = str(v)[:10]
            if type(v)==str:
                v = '\''+v+'\''
            values1.append(v)
    try:
        cursor.execute(sql.format(*values1))
    except Exception as e:
        print(sql.format(*values1))

        print(e)
        print(row_id)
    
conn.commit()        
raise Exception()
def func(x):
    if pd.isnull(x):
        return None
    else:
        return x.strftime("%Y%m%d")

#df["TRADINGDAY"] = df["TRADINGDAY"].apply(lambda x: x.strftime("%Y%m%d"))
#df["NEXTTRADINGDAY"] = df["NEXTTRADINGDAY"].apply(lambda x: func(x))
#df["LASTTRADINGDAY"] = df["LASTTRADINGDAY"].apply(lambda x: x.strftime("%Y%m%d"))
#df["NORMALDAY"] = df["NORMALDAY"].apply(lambda x: x.strftime("%Y%m%d"))

print(df)
df = df.iloc[:,:17]
df = df.drop(columns = ['ENTRYTIME','UPDATETIME','GROUNDTIME', 'UPDATEID'])
df.to_sql('pub_tradingday', con = engine, if_exists = 'append', index = False)
cursor.close()
conn.close()
raise Exception()




