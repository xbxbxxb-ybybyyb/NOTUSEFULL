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
                df_new.reset_index(inplace=True)
                df_his.reset_index(inplace=True)
                df_new.set_index(['dt','Ticker','STATEMENT_TYPE'],inplace=True)
                df_his.set_index(['dt','Ticker','STATEMENT_TYPE'],inplace=True)
                data_targe = ["new_num", "his_num", "new_lack", "new_extra_num", "different_num", "same_num","deviation_rate"]
                factors = list(df_his.columns)
                df_p = pd.DataFrame(np.zeros((len(factors),len(data_targe))),columns=data_targe,index=factors)
                df_p.index.name = 'factor'
                for factor in factors:
                    start_time = time.time()
                    try:
                        df_new_factor = pd.DataFrame(df_new.loc[:, factor])
                        df_his_factor = pd.DataFrame(df_his.loc[:, factor])
                    except Exception as e:
                        logger.info("h5_name：%s Error occurred:%s"%(his_h5,e))
                        continue
                    df_new_factor.fillna(999999999,inplace=True)
                    df_his_factor.fillna(999999999,inplace=True)
                    df1 = pd.merge(df_new_factor, df_his_factor, how='right', left_index=True, right_index=True,suffixes=('_new', '_his'))
                    df2 = pd.merge(df_new_factor, df_his_factor, how='left', left_index=True, right_index=True,suffixes=('_new', '_his'))
                    column_new = factor + '_new'
                    column_his = factor + '_his'
                    df01 = df1.round(4)
                    df02 = df2.round(4)
                    df01['result'] = df01.apply(lambda x: fun(x[column_new], x[column_his]), axis=1)
                    df_lack = df01[pd.isnull(df01[column_new])]
                    if not df_lack.empty:
                        df_lack.to_csv(csv_root + '%s_%s_lack.csv'%(new_h5[:-3],factor))
                    df_diff = df01[df01['result'] == False & ~pd.isnull(df01[column_new])]
                    if not df_diff.empty:
                        df_diff.to_csv(csv_root + '%s_%s_different.csv'%(new_h5[:-3],factor))
                    df_extra = df02[pd.isnull(df02[column_his])]
                    if not df_extra.empty:
                        df_extra.to_csv(csv_root + '%s_%s_extra.csv'%(new_h5[:-3],factor))
                    logger.info("h5_name:%s,factor:%s,new_h5 has %d pieces of data" % (new_h5, factor, len(df_new_factor)))
                    logger.info("h5_name:%s,factor:%s,his_h5 has %d pieces of data"%(his_h5, factor,len(df_his_factor)))
                    logger.info("h5_name:%s,factor:%s,missing data %d !"%(his_h5, factor,len(df_lack)))
                    logger.info("h5_name:%s,factor:%s,calc different data %d ！"%(his_h5, factor,len(df_diff)))
                    logger.info("h5_name:%s,factor:%s,extra data %d ！"%(his_h5, factor,len(df_extra)))
                    logger.info("h5_name:%s,factor:%s,same data %d ！" % (his_h5, factor, df01['result'].sum()))
                    accuracy_rate = df01['result'].sum() / len(df01)
                    deviation_rate = 1 - accuracy_rate
                    dataset = [len(df_new_factor), len(df_his_factor), len(df_lack), len(df_extra), len(df_diff),
                               df01['result'].sum(), deviation_rate]
                    df_p.loc[factor, :] = dataset
                    logger.info("h5_name:%s,factor:%s,Deviation_rate:%.4f" % (his_h5, factor, deviation_rate))
                    end_time = time.time()
                    logger.info("h5_name:%s,factor:%s,spend time %d seconds"%(his_h5, factor,(end_time-start_time)))
                df_p.to_csv(csv_root + "%s.csv" % his_h5[:-3])

def fun(x,y):
    if x == y:
        return True
    else:
        return False


if __name__ == "__main__":
    csv_root = "/app/tools/update_h5_framework_1/check_data/"
    his_h5_path = "/app/data/wdb_h5/WIND/AShareBalanceSheet/"
    new_h5_path = "/app/data/wdb_h5/WIND_TEST/AShareBalanceSheet/"
    #校对每日更新数据

    date_range = [20190930, 20190930]
    check_data(his_h5_path, new_h5_path, csv_root, date_range)
    # 校对财务数据
    # start_date = 20190331
    # date_list = [start_date]
    # while start_date <= 20190930:
    #     if start_date % 10000 == 1231:
    #         start_date = int(start_date / 10000) * 10000 + 10000 + 630
    #     elif start_date % 10000 == 630:
    #         start_date = int(start_date / 10000) * 10000 + 1231
    #     else:
    #         start_date = int(start_date / 10000) * 10000 + 630
    #     date_list.append(start_date)
    # for i in range(len(date_list) - 1):
    #     sdate = date_list[i]
    #     edate = date_list[i + 1]
    #     date_range = [sdate,edate]
    #     check_data(his_h5_path,new_h5_path,csv_root,date_range)

