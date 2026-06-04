# _*_ coding:utf-8 _*_

import pandas as pd
from Wind.utils import *
from log import Log
import datetime as dt
import os
import time
logger = Log("check_data")

def check_data(his_h5_path,new_h5_path,csv_root,date_range):
    """
    对新生成的h5文件与原文件中的数据比对校验
    :param his_h5_path: 历史数据路径
    :param new_h5_path: 最新生成数据的路径
    :param csv_root: 异常数据写入csv的路径
    :param date_range: 列表，日期范围，如：[20180101,20190101]
    :return:
    """
    his_list = os.listdir(his_h5_path)
    new_list = os.listdir(new_h5_path)
    if not os.path.exists(csv_root):
        os.mkdir(csv_root)
    for his_h5 in his_list:
        for new_h5 in new_list:
            if his_h5 == new_h5:
                his_h5_name = os.path.join(his_h5_path, his_h5)
                new_h5_name = os.path.join(new_h5_path, new_h5)
                df_new = read_data(date_range, alt=new_h5_name)
                df_his = read_data(date_range, alt=his_h5_name)
                for factor in df_his.columns:
                    start_time = time.time()
                    try:
                        df_new_factor = pd.DataFrame(df_new.loc[:, factor])
                        df_his_factor = pd.DataFrame(df_his.loc[:, factor])
                    except Exception as e:
                        logger.info("h5_name：%s Error occurred:%s"%(his_h5,e))
                        continue
                    df_new_factor.fillna('nan',inplace=True)
                    df_his_factor.fillna('nan',inplace=True)
                    df1 = pd.merge(df_new_factor, df_his_factor, how='right', left_index=True, right_index=True,suffixes=('_new', '_his'))
                    df2 = pd.merge(df_new_factor, df_his_factor, how='left', left_index=True, right_index=True,suffixes=('_new', '_his'))
                    column_new = factor + '_new'
                    column_his = factor + '_his'
                    df1['result'] = df1.apply(lambda x: fun(x[column_new], x[column_his]), axis=1)
                    df_lack = df1[pd.isnull(df1[column_new])]
                    df_lack.to_csv(csv_root + '%s_%s_lack.csv'%(new_h5[:-3],factor))
                    df_diff = df1[df1['result'] == False & ~pd.isnull(df1[column_new])]
                    df_diff.to_csv(csv_root + '%s_%s_different.csv'%(new_h5[:-3],factor))
                    df_extra = df2[pd.isnull(df2[column_his])]
                    df_extra.to_csv(csv_root + '%s_%s_extra.csv'%(new_h5[:-3],factor))
                    logger.info("h5_name:%s,factor:%s,new_h5 has %d pieces of data" % (new_h5, factor, len(df_new_factor)))
                    logger.info("h5_name:%s,factor:%s,his_h5 has %d pieces of data"%(his_h5, factor,len(df_his_factor)))
                    logger.info("h5_name:%s,factor:%s,missing data %d !"%(his_h5, factor,len(df_lack)))
                    logger.info("h5_name:%s,factor:%s,calc different data %d ！"%(his_h5, factor,len(df_diff)))
                    logger.info("h5_name:%s,factor:%s,extra data %d ！"%(his_h5, factor,len(df_extra)))
                    accuracy_rate = df1['result'].sum() / len(df1)
                    logger.info("h5_name:%s,factor:%s,Accuracy_rate:%.4f" % (his_h5, factor, accuracy_rate))
                    end_time = time.time()
                    logger.info("h5_name:%s,factor:%s,spend time %d seconds"%(his_h5, factor,(end_time-start_time)))

def fun(x,y):
    if x == y:
        return True
    else:
        return False


if __name__ == "__main__":
    # /app/data/010739/20190122
    csv_root = "/app/data/wdb_h5/WIND_TEST/check_data_csv/"
    his_h5_path = "/app/data/wdb_h5/WIND_TEST/Wind_api"
    new_h5_path = "/app/data/wdb_h5/WIND/MD_CHINA_INDEX_DAILY_WIND"
    date_range = [20100101,20110101]
    check_data(his_h5_path,new_h5_path,csv_root,date_range)

