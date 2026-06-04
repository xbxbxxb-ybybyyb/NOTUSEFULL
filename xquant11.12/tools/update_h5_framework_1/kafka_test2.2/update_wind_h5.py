# _*_ coding:utf-8 _*_
import xml.dom.minidom as xmldom
from xml.dom.minidom import parse
import xml.etree.ElementTree as ET
import numpy as np
from Wind.utils import *
import os
from log import Log
import time
import sys
import datetime as dt
import sched
from Wind.push_kafka import push_data

logger = Log("update_wind_h5")



def hdf5_writer(xml_path,cdate_list,sql_config,fail_h5_list=None,supplement_h5_name=None):
    """
    解析XML配置文件构建sql，生成DataFrame并写入h5文件
    :param xml_path: xml地址
    :param cdate_list: 日期列表 元素为int型
    :return:
    """
    logger.info("Start write to H5 ...")
    cdate = max(cdate_list)
    operation = 'append'
    op_type = None if operation == 'create' else True
    root_path = "/app/data/wdb_h5/WIND_TEST/"
    factor_dict = parse_xml(xml_path)
    fail_list = []
    key = 'start'
    for h5_name,source_data in factor_dict.items():
        if supplement_h5_name and h5_name not in supplement_h5_name:
            continue
        if fail_h5_list and h5_name not in fail_h5_list:
            continue
        store_h5_path = root_path + h5_name + "/"
        if not os.path.exists(store_h5_path):
            os.mkdir(store_h5_path)
        date_type = Judge_Tradingday(cdate, sql_config)
        if date_type == "No_tradingday":
            return
        execDate = str(cdate)
        produceTime1 = dt.datetime.strftime(dt.datetime.now(),'%Y-%m-%d %H:%M:%S')
        params = {'method':key,'taskNames':h5_name,'execDate':execDate}
        push_data(params)
        qtrdate_list = get_qtr_list(sql_config,cdate)
        for type in source_data.keys():
            if source_data[type]['freq'] == "Quarterly":
                update_list = qtrdate_list
            else:
                update_list = [cdate]
            for date in update_list:
                if type == 'type_0':
                    wind_table = source_data[type]['wind_table']
                    for table in wind_table.keys():
                        wind_fields = wind_table[table]["wind_fields"]
                        factor_list = wind_table[table]["factor_list"]
                        ofield_factor, fields = factor_transform(wind_fields, factor_list)
                        sql_use = "select " + fields + " from " + table + \
                                  " where " + wind_table[table]["dt_field"] + "=" + str(date)
                        logger.info(sql_use)
                        df = sql_parser(queryUserTableData(sql_use,sql_config))
                        if "STATEMENT_TYPE" in fields:
                            if df['STATEMENT_TYPE'].dtype == 'object':
                                df["STATEMENT_TYPE"] = df["STATEMENT_TYPE"].apply(pd.to_numeric)
                            df = df[df['STATEMENT_TYPE'] == 408001000.0]
                        df.rename(columns=ofield_factor,inplace=True)
                        if df.empty:
                            produceTime2 = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d %H:%M:%S')
                            params = {'method':'stop','taskNames':h5_name,'execDate':execDate,'taskStatus':4}
                            push_data(params)
                            logger.info("%s have no data at date %s"%(table,str(date)))
                            continue
                        if isinstance(df["dt"].iloc[0],str) or isinstance(df["dt"].iloc[0],int):
                            df["dt"] = df["dt"].apply(pd.to_datetime)
                        factor_list_1 = []
                        for factor in factor_list:
                            if factor != "Ticker" and factor != "dt" and factor != "statement_type":
                                factor_list_1.append(factor)
                        if h5_name == "MD_CHINA_INDEX_DAILY_WIND":
                            index_list = ['000001.SH', '000002.SH', '000016.SH', '000300.SH', '000905.SH', '000906.SH',
                                          '399001.SZ', '399005.SZ', '399006.SZ', '000985.CSI']
                        else:
                            index_list = None
                        for factor_name in factor_list_1:
                            produceTime3 = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d %H:%M:%S')
                            params = {'method':key,'taskNames':factor_name,'execDate':execDate}
                            push_data(params)
                            df_factor_1 = df[["Ticker", "dt", factor_name]]
                            df_factor = stock_select(df_factor_1, date, factor_name, sql_config,use_stock_list=index_list)
                            df_factor.set_index(['dt', 'Ticker'], inplace=True)
                            logger.info("Acquired the factor %s data ,then write to %s !" % (factor_name, h5_name))
                            pd_hdf5_writer(df_factor, store_h5_path + h5_name + ".h5", factor_name, append=op_type)
                            logger.info("The factor %s is writed" % factor_name)
                        produceTime4 = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d %H:%M:%S')
                        params = {'method': 'stop', 'taskNames': h5_name, 'execDate': execDate, 'taskStatus': 2}
                        push_data(params)
                        logger.info("The h5 - %s write success!" % h5_name)
                elif type == 'type_1':
                    factor_list = source_data[type]["factor_list"]
                    Modular = source_data[type]["Modular"]
                    func = source_data[type]["function"]
                    # 反射机制导入模块
                    md = __import__("Wind.%s" % Modular, fromlist=True)
                    f = getattr(md,func)
                    if source_data[type]["return_df"] == "all_factor":
                        try:
                            df = f(sql_config,cdate_list,date,factor_name=None)
                        except Exception as e:
                            logger.error("h5name is %s  Error occurred: %s" % (h5_name, e))
                            continue
                    for factor_name in factor_list:
                        produceTime5 = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d %H:%M:%S')
                        params = {'method':key,'taskNames':factor_name,'execDate':execDate}
                        push_data(params)
                        if source_data[type]["return_df"] == "single_factor":
                            try:
                                df = f(sql_config, cdate_list, date, factor_name)
                            except Exception as e:
                                logger.error("h5name is %s factor_name is %s Error occurred: %s"%(h5_name,factor_name,e))
                                continue
                        if df.empty:
                            produceTime6 = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d %H:%M:%S')
                            params1 = {'method':'stop','taskNames':factor_name,'execDate':execDate,'taskStatus':4}
                            push_data(params1)
                            logger.info("%s have no data at date %s" % (h5_name, str(date)))
                            continue
                        if h5_name not in ["UNIV_CHINA_STOCK_DAILY_OPTM"]:
                            df_factor_1 = df.loc[:, ["Ticker", "dt", factor_name]]
                            df_factor = stock_select(df_factor_1, date, factor_name, sql_config)
                            df_factor.set_index(['dt', 'Ticker'], inplace=True)
                        else:
                            df_factor = df.loc[:, factor_name]
                        logger.info("Acquired the factor %s data ,then write to %s !" % (factor_name, h5_name))
                        pd_hdf5_writer(df_factor, store_h5_path + h5_name + ".h5", factor_name, append=op_type)
                        logger.info("The factor %s is writed" % factor_name)
                    produceTime7 = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d %H:%M:%S')
                    params = {'method': 'stop', 'taskNames': h5_name, 'execDate': execDate, 'taskStatus': 2}
                    push_data(params)
                    logger.info("The h5 - %s write success!" % h5_name)
                elif type == 'type_2':
                    wind_table = source_data[type]['wind_table']
                    table = list(wind_table.keys())[0]
                    real_table = table.split('.')[-1]
                    wind_fields = wind_table[table]["wind_fields"]
                    factor_list = wind_table[table]["factor_list"]
                    delete_columns = wind_table[table]["delete_columns"]
                    # Indefinite_length = wind_table[table].get("Indefinite_character",None)
                    ofield_factor, fields = factor_transform(wind_fields, factor_list)
                    # if not "dt_field" in wind_table[table]:
                    #     continue
                    date_10 = dt.datetime.strptime(str(date), '%Y%m%d') - dt.timedelta(days=9)
                    previous_date_10 = dt.datetime.strftime(date_10, "%Y%m%d")
                    Indefinite_length = {}
                    if "dt_field" in wind_table[table]:
                        if h5_name in ['i_organ_score','gg_org_list','i_report_type','author_core_type','t_great_author',
                                       'author_pjhb','author_core','t_author_honor','researcher_info','AShareInsiderTrade']:
                            sql_use = "select *" + " from " + table
                        elif h5_name in ['cmb_report_subtable', 'der_report_subtable', 'cmb_report_adjust',  'report_author',
                                         'cmb_report_score_adjust','cmb_report_research', 'der_report_research']:
                            sql_use = "select *" + " from " + table + " where " + wind_table[table]["dt_field"] + "=" + "to_date(" + str(date) +  ",'YYYYMMDD')"
                        # elif h5_name in ['author_pj']:
                        #     sql_use = "select *" + " from " + table + " where " + 'Rpt_Date' + "=" + str(date)[:4]
                        elif h5_name in ['AShareMarginTradeSum']:
                            sql_use = "select *" + " from " + table + " where " + \
                                      wind_table[table]["dt_field"] + ">=" + previous_date_10 + " and " + \
                                      wind_table[table]["dt_field"] + "<="+ str(date)
                        else:
                            sql_use = "select *" + " from " + table + " where " + wind_table[table]["dt_field"] + "=" + str(date)
                    else:
                        sql_use = "select *" + " from " + table
                    logger.info(sql_use)
                    df = sql_parser(queryUserTableData(sql_use, sql_config))
                    if df is None or df.empty :
                        produceTime8 = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d %H:%M:%S')
                        params = {'method':'stop','taskNames':h5_name,'execDate':execDate,'taskStatus':4}
                        push_data(params)
                        logger.info("The table %s at date %s have no data!"%(table,str(date)))
                        # 每日更新的数据因万德表更新时间在定时任务后，会导致读取时没有数据
                        if "dt_field" in wind_table[table] and wind_table[table]["dt_field"] == 'TRADE_DT':
                            fail_list.append(h5_name)
                        continue
                    df[df.isnull()] = np.nan
                    if delete_columns:
                        df.drop(delete_columns,axis=1,inplace=True)
                    if "ticker_match" in wind_table[table]:
                        code_label = wind_table[table]['ticker_match']
                        df[code_label] = df[code_label].apply(lambda x: np.nan if not x.isnumeric() else x)
                        df = df[~df[code_label].isna()]
                        df[code_label] = df[code_label].apply(ticker_match)
                    # if h5_name in ['cmb_report_research','der_report_research']:
                    #     print(df.head())
                    #     df['CONTENT'] = df['CONTENT'].astype(str)
                    #     df['CONTENT'] = df['CONTENT'].apply(lambda x: x.replace('\n', ''))
                    #     df['CONTENT'] = df['CONTENT'].apply(lambda x: x.replace('\r', ''))
                    #     df['CONTENT'] = df['CONTENT'].apply(lambda x: x.replace(',', '，'))
                    for column in df.columns:
                        column_attr,column_length = get_Oracle_column_attrs(table,sql_config,column)
                        if column_attr == "NUMBER" or column_attr == "FLOAT":
                            if "dt_field" in wind_table[table] and column == wind_table[table]["dt_field"]:
                                df[column] = df[column].astype(str)
                            else:
                                df[column] = df[column].astype(float)
                                # df[column] = df[column].apply(pd.to_numeric)
                        elif ('Ticker' not in factor_list and column == 'OBJECT_ID') or column in wind_fields:
                            continue
                        elif column_attr == 'VARCHAR2' or column_attr == 'VARCHAR':
                            Indefinite_length[column] = column_length * 2 + 2
                    if h5_name == 'der_report_subtable':
                        df['ID'] = df['ID'].astype(int)
                        df['REPORT_SEARCH_ID'] = df['REPORT_SEARCH_ID'].astype(int)
                        df['TIME_YEAR'] = df['TIME_YEAR'].astype(int)
                    if ofield_factor:
                        df.rename(columns=ofield_factor, inplace=True)
                    if "category" in wind_table[table] and wind_table[table]['category'] == "Unanimous_expectation":
                        if 'CON_HISDATE' in df.columns:
                            df['CON_HISDATE'] = df['CON_HISDATE'].astype('str')
                    if "dt_field" in wind_table[table]:
                        if isinstance(df["dt"].iloc[0], str) or isinstance(df["dt"].iloc[0], int):
                            df["dt"] = df["dt"].apply(pd.to_datetime)
                    else:
                        df["dt"] = pd.Timestamp(str(date))
                    # dt对应date的h5需用override=True，每天更新覆盖前一天的数据。
                    produceTime9 = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d %H:%M:%S')
                    params = {'method':key,'taskNames':h5_name,'execDate':execDate}
                    push_data(params)
                    if 'dt' in df.columns and 'Ticker' in df.columns:
                        df.set_index(['dt', 'Ticker'], inplace=True)
                        Indefinite_length['Ticker'] = 20
                        logger.info("Acquired the table %s data ,then write to %s !" % (table, h5_name))
                        if "dt_field" in wind_table[table]:
                            if h5_name == "FCD_CHINA_STOCK_DAILY_SUNTIME":
                                pd_hdf5_writer(df, store_h5_path + h5_name + ".h5", h5_name, append=op_type,min_itemsize=Indefinite_length)
                            elif h5_name in ['i_organ_score','gg_org_list','i_report_type','author_core_type',
                                           't_great_author','author_pjhb','author_core','t_author_honor','researcher_info','AShareInsiderTrade']:
                                pd_hdf5_writer(df, store_h5_path + h5_name + ".h5", real_table, override=True)
                            else:
                                pd_hdf5_writer(df, store_h5_path + h5_name + ".h5", real_table, append=op_type,min_itemsize=Indefinite_length)
                        else:
                            pd_hdf5_writer(df, store_h5_path + h5_name + ".h5", real_table, override=True)
                        logger.info("The h5 - %s write success!" % h5_name)
                    else:
                        if 'OBJECT_ID' in df.columns:
                            df.set_index(['dt','OBJECT_ID'], inplace=True)
                        elif 'ID' in df.columns:
                            df.set_index(['dt', 'ID'], inplace=True)
                        logger.info("Acquired the table %s data ,then write to %s !" % (table, h5_name))
                        if "dt_field" in wind_table[table]:
                            if h5_name in ['i_organ_score','gg_org_list','i_report_type','author_core_type',
                                           't_great_author','author_pjhb','author_core','t_author_honor','researcher_info','AShareInsiderTrade']:
                                pd_hdf5_writer(df, store_h5_path + h5_name + ".h5", real_table, override=True)
                            else:
                                pd_hdf5_writer(df, store_h5_path + h5_name + ".h5", real_table, append=op_type,min_itemsize=Indefinite_length)
                        else:
                            pd_hdf5_writer(df, store_h5_path + h5_name + ".h5", real_table, override=True)
                        logger.info("The h5 - %s write success!" % h5_name)
    return fail_list


def execute(start_date,end_date,xml_path,sql_config):
    sdate, edate, cdate_list = check_update_date(start_date, end_date)
    start = time.time()
    logger.info("Start run task date %s ..." % edate)
    wind_stock_path = "/app/data/wdb_h5/WIND_TEST/universe_complete/stocklst/"
    if not os.path.exists(wind_stock_path):
        os.makedirs(wind_stock_path)
    csv_name = wind_stock_path + str(edate) + '.csv'
    csv_exist = os.path.exists(csv_name)
    i = 0
    while not csv_exist:
        get_stock_list(edate,sql_config)
        if os.path.exists(csv_name):
            break
        i += 1
        if not os.path.exists(csv_name):
            logger.info("Write the csv %s %s times,it has not written,the progrem sleep 10s" % (str(edate) + '.csv', str(i)))
            time.sleep(10)

    # 开始解析配置项并写入h5文件
    fail_list = hdf5_writer(xml_path,cdate_list,sql_config)
    # 对不是每天都有数据的H5从fail_list中剔除
    if 'ASharePlacementInfo' in fail_list:
        fail_list.remove('ASharePlacementInfo')
    logger.info("The fail H5 table is %s" % str(fail_list))
    j = 0
    while fail_list and j<=10:
        logger.info("sleep 30min update the failed table!")
        time.sleep(1800)
        fail_list = hdf5_writer(xml_path, cdate_list, sql_config,fail_h5_list=fail_list)
        j += 1
        if not fail_list:
            break
    #logger.info("Daily tasks have been completed, waiting for the implementation of 5 p.m tasks...")
    #Special_list_5 = ['stock_report_adjustment', 'MD_CHINA_INDEX_DAILY_WIND', 'con_stock_deviation2']
    #def crontab_job():
    #    hdf5_writer(xml_path, cdate_list, sql_config, supplement_h5_name=Special_list_5)
    # def crontab_job2():
    #     hdf5_writer(xml_path, cdate_list, sql_config, supplement_h5_name=Special_list_6)
    #now_time = dt.datetime.now()
    #logger.info("Now the time is %s ..."%str(now_time))
    #schedule = sched.scheduler(time.time, time.sleep)
    #crontab_time = dt.datetime(now_time.year, now_time.month, now_time.day, 10, 32, 0)
    #delay_time = (crontab_time - now_time).seconds
    #logger.info("The job sleep %s s"%str(delay_time))
    #schedule.enter(delay_time, 0, crontab_job, ())
    #logger.info("Start execute the 17:00 task ... ")
    #schedule.run()
    # for csv in os.listdir(wind_stock_path):
    #     if csv[:-4] == str(edate):
    #         os.remove(os.path.join(wind_stock_path,csv))
    end = time.time()
    logger.info('Task %s runs %0.2f seconds.' % (edate, (end - start)))



if __name__ == "__main__":
    xml_path = "config-h5.xml"
    sql_config = get_sql_config(xml_path)
    # print(sql_config)
    # print(parse_xml(xml_path))
    start_date = 20131118    #20131118
    end_date = 20131118     #20151026
    execute(start_date, end_date, xml_path, sql_config)
    logger.info("=================update finish======================")




