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

logger = Log("update_wind_h5")



def hdf5_writer(xml_path,cdate_list,sql_config,supplement_h5_name,supplement_factors):
    """
    解析XML配置文件构建sql，生成DataFrame并写入h5文件
    :param xml_path: xml地址
    :param cdate_list: 日期列表 元素为int型
    :return:
    """
    logger.info("Start write to H5 ...")
    date = max(cdate_list)
    operation = 'append'
    op_type = None if operation == 'create' else True
    root_path = "/app/data/wdb_h5/WIND_TEST/"
    factor_dict = parse_xml(xml_path)
    for h5_name,source_data in factor_dict.items():
        #time1 = datetime.datetime.strptime(str(datetime.datetime.now().date()) + '16:00', '%Y-%m-%d%H:%M')
        #time2 = datetime.datetime.strptime(str(datetime.datetime.now().date()) + '17:00', '%Y-%m-%d%H:%M')
        #now1 = datetime.datetime.now()
        #if now1 > time1 and now1 <= time2:
        #    logger.info("time sleep 1 hours...")
        #    time.sleep(3600)
        #    logger.info("Continue...")
        #time3 = datetime.datetime.strptime(str(datetime.datetime.now().date()) + '1:00', '%Y-%m-%d%H:%M')
        #time4 = datetime.datetime.strptime(str(datetime.datetime.now().date()) + '2:00', '%Y-%m-%d%H:%M')
        #now2 = datetime.datetime.now()
        #if now2 > time3 and now2 <= time4:
        #    logger.info("time sleep 5 hours...")
        #    time.sleep(18000)
        #    logger.info("Continue...")
        # 如果传入了需要补的h5_name则只写指定的h5_name
        if supplement_h5_name and h5_name not in supplement_h5_name:
            continue
        store_h5_path = root_path + h5_name + "/"
        if not os.path.exists(store_h5_path):
            os.mkdir(store_h5_path)
        for type in source_data.keys():
            date_type = judge_Quarterly(date, sql_config)
            if date_type == "Quarterly" and source_data[type]['freq'] != "Quarterly" and source_data[type]['freq'] != "Monthly":
                continue
            elif date_type == "Daily" and (source_data[type]['freq'] == "Quarterly" or source_data[type]['freq'] == "Monthly"):
                continue
            elif date_type == "Monthly" and source_data[type]['freq'] != "Monthly":
                continue
            elif date_type == "No_tradingday":
                # 标记 补齐历史数据后continue应该为return
                logger.info("Today is No_tradingday!")
                continue
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
                        logger.info("%s have no data at date %s"%(table,str(date)))
                        continue
                    if isinstance(df["dt"].iloc[0],str) or isinstance(df["dt"].iloc[0],int):
                        df["dt"] = df["dt"].apply(pd.to_datetime)
                    factor_list.remove("Ticker")
                    factor_list.remove("dt")
                    if "statement_type" in factor_list:
                        factor_list.remove("statement_type")
                    if h5_name == "MD_CHINA_INDEX_DAILY_WIND":
                        index_list = ['000001.SH', '000002.SH', '000016.SH', '000300.SH', '000905.SH', '000906.SH',
                                      '399001.SZ', '399005.SZ', '399006.SZ', '000985.CSI']
                    else:
                        index_list = None
                    for factor_name in factor_list:
                        # supplement_factors非空则只写supplement_factors列表中的因子
                        if supplement_factors and factor_name not in supplement_factors:
                            continue
                        df_factor_1 = df[["Ticker", "dt", factor_name]]
                        df_factor = stock_select(df_factor_1, date, factor_name, sql_config,use_stock_list=index_list)
                        df_factor.set_index(['dt', 'Ticker'], inplace=True)
                        logger.info("Acquired the factor %s data ,then write to %s !" % (factor_name, h5_name))
                        pd_hdf5_writer(df_factor, store_h5_path + h5_name + ".h5", factor_name, append=op_type)
                        logger.info("The factor %s is writed" % factor_name)
                    logger.info("The h5 - %s write success!" % h5_name)
            elif type == 'type_1':
                factor_list = source_data[type]["factor_list"]
                Modular = source_data[type]["Modular"]
                func = source_data[type]["function"]
                # 反射机制导入模块
                md = __import__("Wind.%s" % Modular, fromlist=True)
                f = getattr(md,func)
                if source_data[type]["return_df"] == "all_factor":
                    #try:
                    df = f(sql_config,cdate_list,date,factor_name=None)
                    #except Exception as e:
                    #    logger.error("h5name is %s  Error occurred: %s" % (h5_name, e))
                    #    continue
                elif source_data[type]["return_df"] == "Internal_write":
                    try:
                        f(date, sql_config)
                        logger.info("The h5 - %s write success!" % h5_name)
                        continue
                    except Exception as e:
                        logger.error("h5name is %s  Error occurred: %s" % (h5_name, e))
                        continue
                for factor_name in factor_list:
                    # supplement_factors非空则只写supplement_factors列表中的因子
                    if supplement_factors and factor_name not in supplement_factors:
                        continue
                    if source_data[type]["return_df"] == "single_factor":
                        try:
                            df = f(sql_config, cdate_list, date, factor_name)
                        except Exception as e:
                            logger.error("h5name is %s factor_name is %s Error occurred: %s"%(h5_name,factor_name,e))
                            continue
                    if df is None or df.empty:
                        logger.info("%s have no data at date %s" % (h5_name, str(date)))
                        continue
                    if h5_name not in ["UNIV_CHINA_STOCK_DAILY_OPTM"]:
                        df_factor_1 = df.loc[:, ["Ticker", "dt", factor_name]]
                        df_factor = stock_select(df_factor_1, date, factor_name, sql_config)
                        df_factor.set_index(['dt', 'Ticker'], inplace=True)
                    else:
                        df_factor = df.loc[:, factor_name]
                    logger.info("Acquired the factor %s data ,then write to %s !" % (factor_name, h5_name))
                    pd_hdf5_writer(df_factor, store_h5_path + h5_name + ".h5", factor_name,append=op_type)#append=op_type
                    logger.info("The factor %s is writed" % factor_name)
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
                #if not "dt_field" in wind_table[table]:
                #    continue
                Indefinite_length = {}
                if "dt_field" in wind_table[table]:
                    if h5_name in ['i_organ_score', 'gg_org_list', 'i_report_type', 'author_core_type',
                                   't_great_author',
                                   'author_pjhb', 'author_core', 't_author_honor', 'researcher_info','AShareInsiderTrade']:
                        sql_use = "select *" + " from " + table
                    elif h5_name in ['cmb_report_subtable', 'der_report_subtable', 'cmb_report_adjust', 'report_author',
                                     'cmb_report_score_adjust', 'cmb_report_research', 'der_report_research']:
                        sql_use = "select *" + " from " + table + " where " + wind_table[table][
                            "dt_field"] + "=" + "to_date(" + str(date) + ",'YYYYMMDD')"
                    # elif h5_name in ['author_pj']:
                    #     sql_use = "select *" + " from " + table + " where " + 'Rpt_Date' + "=" + str(date)[:4]
                    else:
                        sql_use = "select *" + " from " + table + " where " + wind_table[table]["dt_field"] + "=" + str(date)
                else:
                    sql_use = "select *" + " from " + table
                logger.info(sql_use)
                df = sql_parser(queryUserTableData(sql_use, sql_config))
                if df.empty or df is None:
                    logger.info("The table %s at date %s have no data!" % (table, str(date)))
                    continue
                df[df.isnull()] = np.nan
                if delete_columns:
                    df.drop(delete_columns, axis=1, inplace=True)
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
                    column_attr, column_length = get_Oracle_column_attrs(table, sql_config, column)
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
                if 'dt' in df.columns and 'Ticker' in df.columns:
                    df.set_index(['dt', 'Ticker'], inplace=True)
                    Indefinite_length['Ticker'] = 20
                    logger.info("Acquired the table %s data ,then write to %s !" % (table, h5_name))
                    if "dt_field" in wind_table[table]:
                        if h5_name == "FCD_CHINA_STOCK_DAILY_SUNTIME":
                            pd_hdf5_writer(df, store_h5_path + h5_name + ".h5", h5_name, append=op_type,
                                           min_itemsize=Indefinite_length)
                        elif h5_name in ['i_organ_score', 'gg_org_list', 'i_report_type', 'author_core_type',
                                         't_great_author', 'author_pjhb', 'author_core', 't_author_honor',
                                         'researcher_info','AShareInsiderTrade']:
                            pd_hdf5_writer(df, store_h5_path + h5_name + ".h5", real_table, override=True)
                        else:
                            pd_hdf5_writer(df, store_h5_path + h5_name + ".h5", real_table, append=op_type,
                                           min_itemsize=Indefinite_length)
                    else:
                        pd_hdf5_writer(df, store_h5_path + h5_name + ".h5", real_table, override=True)
                    logger.info("The h5 - %s write success!" % h5_name)
                else:
                    if 'OBJECT_ID' in df.columns:
                        df.set_index(['dt', 'OBJECT_ID'], inplace=True)
                    elif 'ID' in df.columns:
                        df.set_index(['dt', 'ID'], inplace=True)
                    logger.info("Acquired the table %s data ,then write to %s !" % (table, h5_name))
                    if "dt_field" in wind_table[table]:
                        if h5_name in ['i_organ_score', 'gg_org_list', 'i_report_type', 'author_core_type',
                                       't_great_author', 'author_pjhb', 'author_core', 't_author_honor',
                                       'researcher_info','AShareInsiderTrade']:
                            pd_hdf5_writer(df, store_h5_path + h5_name + ".h5", real_table, override=True)
                        else:
                            pd_hdf5_writer(df, store_h5_path + h5_name + ".h5", real_table, append=op_type,
                                           min_itemsize=Indefinite_length)
                    else:
                        pd_hdf5_writer(df, store_h5_path + h5_name + ".h5", real_table, override=True)
                    logger.info("The h5 - %s write success!" % h5_name)



def execute(start_date,end_date,xml_path,sql_config,supplement_h5_name,supplement_factors):
    sdate, edate, cdate_list = check_update_date(start_date, end_date)
    for his_enddate in cdate_list:
        start = time.time()
        his_sdate, his_edate, his_datelst = check_update_date(start_date, his_enddate)
        logger.info("Start run task date %s ..." % his_edate)
        wind_stock_path = "/app/data/wdb_h5/WIND_TEST/universe_complete/stocklst/"
        csv_name = wind_stock_path + str(his_edate) + '.csv'
        csv_exist = os.path.exists(csv_name)
        i = 0
        while not csv_exist:
            get_stock_list(his_edate,sql_config)
            if os.path.exists(csv_name):
                break
            i += 1
            if not os.path.exists(csv_name):
                logger.info("Write the csv %s %s times,it has not written,the progrem sleep 10s" % (str(his_edate) + '.csv', str(i)))
                time.sleep(10)
        # 开始解析配置项并写入h5文件
        hdf5_writer(xml_path,his_datelst,sql_config,supplement_h5_name,supplement_factors)
        for csv in os.listdir(wind_stock_path):
            if csv[:-4] == str(his_edate):
                os.remove(os.path.join(wind_stock_path,csv))
        end = time.time()
        logger.info('Task %s runs %0.2f seconds.' % (his_edate, (end - start)))
    # print(parse_xml(xml_path))

def parse_argv():
    if len(sys.argv) > 1:
        assert sys.argv[1].isdigit() and len(sys.argv[1]) == 8, "Date is 8 digit number,aborting..."
        start_date = int(sys.argv[1])
        current_time = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        current_date = int(current_time[:8])
        if start_date >= current_date:
            raise Exception("The date greater than or equal to today, aborting...")
    if len(sys.argv) == 5:
        start_date = int(sys.argv[1])
        end_date = int(sys.argv[2])
        supplement_h5_name = []
        supplement_factors = []
        for i in sys.argv[3].split(','):
            supplement_h5_name.append(i)
        for j in sys.argv[4].split(','):
            supplement_factors.append(j)
        logger.info("Will supplement data: the date is %s to %s ,h5_name is %s,factor is %s"
              % (str(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3]), str(sys.argv[4])))
    elif len(sys.argv) == 4:
        if sys.argv[2].isdigit():
            assert len(sys.argv[2]) == 8, "Date is 8 digit number,aborting..."
            end_date = int(sys.argv[2])
            if start_date > end_date:
                raise Exception("End_date greater than start_date,aborting...")
            supplement_h5_name = []
            supplement_factors = []
            for i in sys.argv[3].split(','):
                supplement_h5_name.append(i)
            logger.info("Will supplement data: the date is %s to %s ,h5_name is %s,factor is all"
                        % (str(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3])))
        else:
            end_date = start_date
            supplement_h5_name = []
            supplement_factors = []
            for i in sys.argv[2].split(','):
                supplement_h5_name.append(i)
            for j in sys.argv[3].split(','):
                supplement_factors.append(j)
            logger.info("Will supplement data: the date is %s ,h5_name is %s,factor is %s"
                  % (str(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3])))
    elif len(sys.argv) == 3:
        if sys.argv[2].isdigit():
            assert len(sys.argv[2]) == 8, "Date is 8 digit number,aborting..."
            end_date = int(sys.argv[2])
            if start_date > end_date:
                raise Exception("End_date greater than start_date,aborting...")
            supplement_h5_name = []
            supplement_factors = []
            logger.info("Will supplement data: the date is %s to %s ,all h5_name and all factors."
                        % (str(sys.argv[1]), str(sys.argv[2])))
        else:
            end_date = start_date
            supplement_h5_name = []
            supplement_factors = []
            for i in sys.argv[2].split(','):
                supplement_h5_name.append(i)
            logger.info("Will supplement data: the date is %s ,h5_name is %s,factor is all."
                        % (str(sys.argv[1]), str(sys.argv[2])))
    elif len(sys.argv) == 2:
        end_date = start_date
        supplement_h5_name = []
        supplement_factors = []
        logger.info("Will supplement data: the date is %s ,all h5_name and all factors."
                    % (str(sys.argv[1])))
    elif len(sys.argv) == 1:
        start_date = 20200331 #20100107
        end_date = 20200331 # 20190705
        # 补某h5的历史数据，supplement_factors为空则补该h5的所有因子
        supplement_h5_name = ['AShareCashFlow']
        supplement_factors = []
    else:
        raise Exception("The passed parameter's number is inconformity , aborting...")

    return start_date,end_date,supplement_h5_name,supplement_factors



if __name__ == "__main__":
    xml_path = "config-h5.xml"
    sql_config = get_sql_config(xml_path)
    start_date,end_date,supplement_h5_name,supplement_factors = parse_argv()
    if supplement_factors and not supplement_h5_name:
        raise Exception("supplement data must appoint the h5 name,aborting...")
    execute(start_date, end_date, xml_path, sql_config, supplement_h5_name, supplement_factors)
    logger.info("=================update finish======================")






