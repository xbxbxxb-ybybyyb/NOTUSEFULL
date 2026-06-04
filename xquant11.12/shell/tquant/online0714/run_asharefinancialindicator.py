# -*- coding: utf-8 -*-

from data_clean import base_data_clean, Kafka_producer
import pandas as pd
import time
import sys
sys.path.append("/app/tools")
from gaya_factor.utils import get_sql_script

pd.set_option('display.max_columns', None)


class data_clean(base_data_clean):
    def __init__(self, date, library_name, library_id, field, env_id, cloud_env):
        super().__init__(env_id, cloud_env)
        self.date = date
        self.library_name = library_name
        self.library_id = library_id
        self.field = field

    def calculation(self, df, td):
        pass


def main(need_merge=True):
    from setEnv import env_id, cloud_env
    # 日期有页面传入-----
    try:
        date = sys.argv[1]
    except:
        date = '20181231'
    # 表名要修改----
    library_name = "factor_d_financialanalysisindex"
    library_id = 1
    # 因子要修改-----
    field = ['eps_basic', 'eps_diluted', 'eps_diluted2', 'bps', 'ocfps', 'grps', 'orps', 'surpluscapitalps',
             'surplusreserveps', 'undistributedps', 'retainedps', 'cfps', 'ebitps', 'fcffps', 'fcfeps', 'roa2', 'roa',
             'roic', 'roe_yearly', 'roa2_yearly', 'roa_yearly', 'netprofitmargin', 'grossprofitmargin', 'cogstosales',
             'expensetosales', 'profittogr', 'optogr', 'ebittogr', 'gctogr', 'operateexpensetogr', 'adminexpensetogr',
             'finaexpensetogr', 'impairtogr', 'impairtogr_ttm', 'grossmargin', 's_qfa_yoyop', 's_qfa_yoyprofit',
             's_qfa_cgrsales', 'waa_roe', 'operateincometoebt', 'investincometoebt', 'nonoperateprofittoebt',
             'taxtoebt', 'deductedprofittoprofit', 'extraordinary', 'deductedprofit', 'salescashintoor', 'ocftoor',
             'ocftooperateincome', 'capitalizedtoda', 'debttoassets', 'assetstoequity', 'catoassets', 'ncatoassets',
             'tangibleassetstoassets', 'equitytototalcapital', 'intdebttototalcap', 'currentdebttodebt',
             'longdebtodebt', 'current', 'quick', 'cashratio', 'debttoequity', 'equitytodebt', 'equitytointerestdebt',
             'tangassettointdebt', 'tangibleassettodebt', 'tangibleassettonetdebt', 'ebitdatodebt', 'ocftodebt',
             'ocftointerestdebt', 'ocftoshortdebt', 'ocftonetdebt', 'ebittointerest', 'longdebttoworkingcapital',
             'turndays', 'invturndays', 'arturndays', 'invturn', 'arturn',
             'caturn', 'faturn', 'assetsturn', 'yoyeps_basic', 'yoyeps_diluted', 'yoyocfps', 'yoy_tr', 'yoy_or',
             'yoyop', 'yoyebt', 'yoynetprofit', 'yoynetprofit_deducted', 'yoyocf', 'yoyroe', 'yoy_equity', 'yoybps',
             'yoyassets', 'yoyequity','roe','operateincome','stmnote_finexp_fa','stm_is','exinterestdebt_current',
             'exinterestdebt_noncurrent','investcapital','ocftoprofit','cashtoliqdebtwithinterest','fcff', 'ebit_fa',
             'ebitda_fa']
    env_id = env_id
    cloud_env = cloud_env
    # 解析任务
    dc = data_clean(date, library_name, library_id, field, env_id, cloud_env)
    # 日行情需要改成每日
    # date_list = dc.get_date()
    # 数据清洗
    # 获取df
    # 获取sql语句的DataFrame
    df_sql = get_sql_script(field[0])
    # sql需要修改----
    sql_script = df_sql.loc['A股', 'factor_sql']
    sql = sql_script.format(date)
    df = dc.read_from_cloud(sql)

    if need_merge:
        chiname = ["chiname", "exchangecode", "exchangename"]
        dc.field = chiname + field
        df = dc.merge_chiname(['TDATE', 'TRADINGCODE'], df)

    dc.run_task(df)
    dc.mysql_close()

if __name__ == '__main__':
    main()
