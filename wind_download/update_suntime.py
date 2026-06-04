# -*- coding: utf-8 -*-
"""
update_concensus_htsc

"""
from multifactor.data.utils import *
from xquant.factordata import FactorData
import utils
import settings
import shutil
import os
from loguru import logger
from multiprocessing import Pool

s = FactorData()


def ticker_match(ticker_num):
    ticker_num = int(ticker_num)
    suffix = '.SH' if ticker_num >= 600000 else '.SZ'
    pre_fill = (6 - len(str(ticker_num))) * '0'
    ticker = pre_fill + str(ticker_num) + suffix
    return ticker


def index_match(ticker_num):
    if not ticker_num.isnumeric():
        return str(ticker_num)
    if str(ticker_num)[:3] == '000':
        suffix = '.SH'
    elif str(ticker_num)[:3] == '399':
        suffix = '.SZ'
    else:
        return str(ticker_num)
    ticker_num = int(ticker_num)
    pre_fill = (6 - len(str(ticker_num))) * '0'
    ticker = pre_fill + str(ticker_num) + suffix
    return ticker


def data_reformat(dat, dat_fig):
    if dat.empty:
        return dat
    if 'drop' in dat_fig.keys():
        dat = dat.drop(dat_fig['drop'], axis=1)

    format_list = dat.dtypes
    num_list = [i != np.dtype('object') for i in format_list]
    str_list = [i == np.dtype('object') for i in format_list]
    col_list = dat.columns.values
    for i in range(len(str_list)):
        if str_list[i]:
            dat[col_list[i]] = dat[col_list[i]].astype('object')
    for i in range(len(num_list)):
        if num_list[i]:
            dat[col_list[i]] = dat[col_list[i]].astype('float64')

    if 'dt' in dat_fig.keys():
        dat[dat_fig['dt']] = dat[dat_fig['dt']].apply(
            lambda x: dt.datetime.strptime(str(int(x.replace('-', '')[:8])), '%Y%m%d')
            if type(x) == np.str_ or type(x) == str else dt.datetime.strptime(str(int(x)), '%Y%m%d'))

        if 'Ticker' in dat_fig.keys():
            if 'ticker_match' in dat_fig.keys():
                dat[dat_fig['Ticker']] = dat[dat_fig['Ticker']].apply(lambda x: 'drop' if not x.isnumeric() else x)
                dat = dat[dat[dat_fig['Ticker']] != 'drop']
                dat[dat_fig['Ticker']] = dat[dat_fig['Ticker']].apply(ticker_match)
            elif 'index_match' in dat_fig.keys():
                dat[dat_fig['Ticker']] = dat[dat_fig['Ticker']].apply(index_match)
            else:
                dat[dat_fig['Ticker']] = dat[dat_fig['Ticker']].astype('str')
            dat = dat.sort_values([dat_fig['dt'], dat_fig['Ticker']])
            dat = dat.set_index([dat_fig['dt'], dat_fig['Ticker']])
            dat.index.names = ['dt', 'Ticker']
        else:
            dat = dat.sort_values([dat_fig['dt'], 'ID'])
            dat = dat.set_index([dat_fig['dt'], 'ID'])
            dat.index.names = ['dt', 'ID']

    return dat


def csv2h5(csv_list, h5_path, table_name, operation, min_size=0):
    fail_list = []
    if operation == 'create':
        if os.path.exists(h5_path):
            os.remove(h5_path)
    with pd.HDFStore(h5_path) as h5_store:
        if table_name in list(h5_store.root._v_groups.keys()):
            dt_lst = list(set(h5_store.select_column(table_name, 'dt')))
        else:
            dt_lst = []
        for fname in csv_list:
            dat = pd.read_csv(fname, encoding='utf_8_sig')
            columns = dat.columns.values

            if 'dt' in columns:
                dat['dt'] = dat['dt'].apply(lambda x: dt.datetime.strptime(x.replace('-', ''), '%Y%m%d'))
            if 'dt' in columns and 'Ticker' in columns:
                dat.set_index(['dt', 'Ticker'], inplace=True)
            elif 'dt' in columns and 'ID' in columns:
                dat.set_index(['dt', 'ID'], inplace=True)

            if 'CON_HISDATE' in columns:
                dat['CON_HISDATE'] = dat['CON_HISDATE'].astype('str')

            if len(dat) < min_size or dat.empty:
                fail_list.append(fname + '@amount_fail')
            else:
                if operation == 'append':
                    curr_date = list(set(dat.index.get_level_values('dt')))[0]
                    if curr_date in dt_lst:
                        h5_store.remove(table_name, 'dt=curr_date')

                if table_name in ['CON_FORECAST_IDX', 'CON_FORECAST_C2_IDX', 'CON_FORECAST_C3_IDX']:
                    h5_store.append(table_name, dat, data_columns=True, min_itemsize={'STOCK_NAME': 50})
                else:
                    h5_store.append(table_name, dat, data_columns=True)
    return fail_list


def retrieve(table_name, pdate_list, root_folder):
    logger.info('开始下载：table={} '.format(table_name))

    table_name_sql = 'GOGOAL_' + table_name
    table_folder = root_folder + '/' + table_name + '/'
    if not os.path.exists(table_folder):
        os.makedirs(table_folder)

    for date in pdate_list:
        if table_name in ['cmb_report_research', 'der_report_research', 'cmb_report_subtable', 'der_report_subtable',
                          'cmb_report_adjust', 'report_author', 'cmb_report_score_adjust', 'change_event']:
            df = s.get_factor_value(table_name_sql, EntryDate=[str(date)])
        elif table_name in ['author_pj']:
            df = s.get_factor_value(table_name_sql, Rpt_Date=[str(date)[:4]])
        elif table_name in ['researcher_info', 'author_core', 'author_core_type', 'i_report_type', 'i_organ_score',
                            'gg_org_list', 't_great_author', 'author_pjhb', 'change_type']:
            # t_author_honor
            df = s.get_factor_value(table_name_sql)
        elif table_name == 't_author_honor':
            df = s.get_factor_value(table_name_sql, EntryDate=['>=20150101']).append(
                s.get_factor_value(table_name_sql, EntryDate=['<20150101']))
        else:
            # logger.info()
            df = s.get_factor_value(table_name_sql, tdate=[str(date)])

        if table_name in ['con_forecast_schedule', 'con_forecast_stk', 'stock_diversity', 'con_stock_deviation',
                          'stock_diversity', 'stock_emotion', 'stock_report_extremum', 'stock_report_number',
                          'con_forecast_c2_stk',
                          'con_forecast_c3_cgb_stk', 'con_forecast_c3_stk', 'con_forecast_cb_stk', 'con_stock_income']:
            dat_fig = {'dt': 'TDATE', 'Ticker': 'STOCK_CODE', 'ticker_match': 'STOCK_CODE'}

        elif table_name in ['CON_FORECAST_IDX', 'CON_FORECAST_C2_IDX', 'CON_FORECAST_C3_IDX']:
            dat_fig = {'dt': 'TDATE', 'Ticker': 'STOCK_CODE', 'index_match': 'STOCK_CODE'}

        elif table_name in ['cmb_report_subtable', 'der_report_subtable',
                            'i_organ_score', 'report_author', 'gg_org_list', 'i_report_type',
                            'author_core_type', 't_great_author', 'cmb_report_research', 'der_report_research']:
            dat_fig = {'dt': 'ENTRYDATE'}
        elif table_name in ['cmb_report_adjust', 'cmb_report_score_adjust', 'author_pj', 'author_pjhb', 'author_core']:
            dat_fig = {'dt': 'ENTRYDATE', 'Ticker': 'STOCK_CODE', 'ticker_match': 'STOCK_CODE'}

        elif table_name in ['t_author_honor']:
            dat_fig = {'dt': 'ENTRYDATE', 'Ticker': 'CODE', 'ticker_match': 'CODE'}

        elif table_name in ['researcher_info']:
            dat_fig = {}
        else:
            dat_fig = {'dt': 'TDATE', 'Ticker': 'STOCK_CODE', 'ticker_match': 'STOCK_CODE', 'drop': ['CONKEYTMS']}

        if table_name not in ['cmb_report_research', 'der_report_research', 'change_type', 'change_event']:
            df = data_reformat(df, dat_fig)

        if table_name in 'researcher_info':
            df.set_index('ID', inplace=True)
            df.to_csv(table_folder + 'researcher_info.csv', sep=',', encoding='utf_8_sig')
        elif table_name in ['author_core', 'author_core_type', 'i_report_type', 'i_organ_score',
                            'gg_org_list', 't_great_author', 'author_pjhb', 't_author_honor', 'change_type']:
            df.to_csv(table_folder + table_name + '.csv', sep=',', encoding='utf_8_sig')
        elif table_name in ['cmb_report_research', 'der_report_research']:
            tmp_csv_root = os.path.join(settings.BASE_DIR, 'LOCAL_DATA/CSV/gogoal_htsc/', table_name)
            if not os.path.exists(tmp_csv_root):
                os.makedirs(tmp_csv_root)
            csv_path = os.path.join(tmp_csv_root, str(date) + '.csv')

            df['CONTENT'] = df['CONTENT'].astype(str)
            df['CONTENT'] = df['CONTENT'].apply(lambda x: x.replace('\n', ''))
            df['CONTENT'] = df['CONTENT'].apply(lambda x: x.replace('\r', ''))
            df['CONTENT'] = df['CONTENT'].apply(lambda x: x.replace(',', '，'))

            df['AUTHOR'] = df['AUTHOR'].astype(str)
            df['AUTHOR'] = df['AUTHOR'].apply(lambda x: x.replace('\n', ''))
            df['AUTHOR'] = df['AUTHOR'].apply(lambda x: x.replace('\r', ''))
            df['AUTHOR'] = df['AUTHOR'].apply(lambda x: x.replace(',', '，'))

            df['TITLE'] = df['TITLE'].astype(str)
            df['TITLE'] = df['TITLE'].apply(lambda x: x.replace('\n', ''))
            df['TITLE'] = df['TITLE'].apply(lambda x: x.replace('\r', ''))
            df['TITLE'] = df['TITLE'].apply(lambda x: x.replace(',', '，'))

            df.to_csv(csv_path, sep=',', encoding='utf_8_sig')

        elif table_name == 'der_report_subtable':
            tmp_csv_root = os.path.join(settings.BASE_DIR, 'LOCAL_DATA/CSV/gogoal_htsc/', table_name)
            if not os.path.exists(tmp_csv_root):
                os.makedirs(tmp_csv_root)
            csv_path = tmp_csv_root + str(date) + '.csv'
            df.to_csv(csv_path, sep=',', encoding='utf_8_sig')
            df = pd.read_csv(csv_path)
            df['ID'] = df['ID'].astype('int')
            df['REPORT_SEARCH_ID'] = df['REPORT_SEARCH_ID'].astype('int')
            df['TIME_YEAR'] = df['TIME_YEAR'].astype('int')
            df.to_csv(csv_path, sep=',', encoding='utf_8_sig')
        elif table_name == 'author_pj':
            df.to_csv(table_folder + str(date)[:4] + '.csv', sep=',', encoding='utf_8_sig')
        else:
            df.to_csv(table_folder + str(date) + '.csv', sep=',', encoding='utf_8_sig')
    logger.info('完成下载：table={} '.format(table_name))


def update_suntime_data(start_date=None, end_date=None):
    logger.info("开始更新 朝阳永续 数据")
    table_list = ['con_forecast_stk', 'con_forecast_schedule', 'stock_order3', 'stock_report_adjustment',
                  'stock_report_number', 'stock_order2', 'stock_report_adjustment2', 'stock_concern_level',
                  'con_stock_deviation3', 'con_stock_deviation2', 'con_stock_deviation',
                  'stock_diversity', 'stock_emotion', 'stock_report_extremum',
                  'der_report_subtable', 'cmb_report_score_adjust', 'i_organ_score', 'report_author',
                  'cmb_report_adjust', 'gg_org_list', 'i_report_type', 'author_core_type', 'author_core',
                  'cmb_report_subtable', 'author_pj', 'author_pjhb', 't_great_author',
                  'con_forecast_c2_stk', 'con_forecast_c3_cgb_stk', 'con_forecast_c3_stk', 'con_forecast_cb_stk',
                  'researcher_info', 't_author_honor', 'der_report_research', 'cmb_report_research',
                  'CON_FORECAST_IDX', 'CON_FORECAST_C2_IDX', 'CON_FORECAST_C3_IDX', 'change_type', 'change_event']

    # table_list = ['con_forecast_stk']

    sdate, edate, cdate_list = check_update_date(start_date, end_date)

    root_folder = os.path.join(settings.BASE_DIR, 'LOCAL_DATA/CSV/gogoal_htsc')

    # pool = Pool(1)
    #
    # for table_name in table_list:
    #     pool.apply_async(__download_table, args=(table_name, sdate, edate, cdate_list, root_folder))
    # pool.close()
    # pool.join()
    for table_name in table_list:
        __download_table(table_name, sdate, edate, cdate_list, root_folder)

def copy_file_from002_to80(start):

    suntime_h5_list = [


        "DATABASE/SUNTIME/stock_concern_level/stock_concern_level.h5",
        "DATABASE/SUNTIME/author_pj/author_pj.h5",
        "DATABASE/SUNTIME/CON_FORECAST_C3_IDX/CON_FORECAST_C3_IDX.h5",
        "DATABASE/SUNTIME/con_forecast_schedule/con_forecast_schedule.h5",
        "DATABASE/SUNTIME/gg_org_list/gg_org_list.h5",
        "DATABASE/SUNTIME/cmb_report_subtable/cmb_report_subtable.h5",
        "DATABASE/SUNTIME/con_stock_deviation2/con_stock_deviation2.h5",
        "DATABASE/SUNTIME/CON_FORECAST_C2_IDX/CON_FORECAST_C2_IDX.h5",
        "DATABASE/SUNTIME/author_core/author_core.h5",
        "DATABASE/SUNTIME/con_forecast_cb_stk/con_forecast_cb_stk.h5",
        "DATABASE/SUNTIME/der_report_subtable/der_report_subtable.h5",
        "DATABASE/SUNTIME/cmb_report_adjust/cmb_report_adjust.h5",
        "DATABASE/SUNTIME/cmb_report_score_adjust/cmb_report_score_adjust.h5",
        "DATABASE/SUNTIME/CON_FORECAST_IDX/CON_FORECAST_IDX.h5",
        "DATABASE/SUNTIME/i_report_type/i_report_type.h5",
        "DATABASE/SUNTIME/stock_report_extremum/stock_report_extremum.h5",
        "DATABASE/SUNTIME/author_pjhb/author_pjhb.h5",
        "DATABASE/SUNTIME/t_great_author/t_great_author.h5",
        "DATABASE/SUNTIME/con_forecast_c3_cgb_stk/con_forecast_c3_cgb_stk.h5",
        "DATABASE/SUNTIME/t_author_honor/t_author_honor.h5",
        "DATABASE/SUNTIME/report_author/report_author.h5",
        "DATABASE/SUNTIME/con_forecast_c3_stk/con_forecast_c3_stk.h5",
        "DATABASE/SUNTIME/author_core_type/author_core_type.h5",
        "DATABASE/SUNTIME/stock_report_adjustment/stock_report_adjustment.h5",
        "DATABASE/SUNTIME/con_stock_deviation3/con_stock_deviation3.h5",
        "DATABASE/SUNTIME/researcher_info/researcher_info.h5",
        "DATABASE/SUNTIME/stock_order3/stock_order3.h5",
        "DATABASE/SUNTIME/stock_report_adjustment2/stock_report_adjustment2.h5",
        "DATABASE/SUNTIME/i_organ_score/i_organ_score.h5",
        "DATABASE/SUNTIME/stock_order2/stock_order2.h5",
        "DATABASE/SUNTIME/stock_emotion/stock_emotion.h5",
        "DATABASE/SUNTIME/con_forecast_c2_stk/con_forecast_c2_stk.h5",
        "DATABASE/SUNTIME/stock_report_number/stock_report_number.h5",
        "DATABASE/SUNTIME/stock_diversity/stock_diversity.h5",
        "DATABASE/SUNTIME/con_stock_deviation/con_stock_deviation.h5",
        "FCD/CHINA_STOCK/DAILY/SUNTIME/FCD_CHINA_STOCK_DAILY_SUNTIME.h5",
        "LOCAL_DATA/CSV/gogoal_htsc/con_forecast_stk/{}.csv".format(str(start))
    ]

    destination_folder = "/data/group/800080/warehouse/prod/"
    source_folder = "/data/group/800002/basic_data/full/financial_data"

    total_size = 0
    for file in suntime_h5_list:
        source_file = os.path.join(source_folder, file)
        tmp_folder = destination_folder
        for i in file.split("/")[:-1]:
            tmp_folder = os.path.join(tmp_folder, i)
            if not os.path.exists(tmp_folder):
                os.mkdir(tmp_folder)
        destination_file = os.path.join(destination_folder, file)
        size = os.path.getsize(source_file) / 1000 / 1000
        total_size += size
        logger.info("file={}, size={}".format(source_file, int(size)))
        shutil.copyfile(source_file, destination_file)

    logger.info("total_size={}".format(total_size))


def __download_table(table_name, sdate, edate, cdate_list, root_folder):
    try:
        table_list3 = ['researcher_info', 'author_core', 'author_core_type', 'i_report_type', 't_author_honor',
                       'i_organ_score', 'gg_org_list', 't_great_author', 'author_pjhb']
        if table_name in table_list3:
            retrieve(table_name, cdate_list[-1:], root_folder)
        else:
            retrieve(table_name, cdate_list, root_folder)
        if table_name not in ['cmb_report_research', 'der_report_research', 'author_pj', 'change_type', 'change_event']:
            if table_name == 'con_forecast_stk':
                h5_root = os.path.join(settings.BASE_DIR, 'FCD/CHINA_STOCK/DAILY/SUNTIME/')
                if not os.path.exists(h5_root):
                    os.makedirs(h5_root)
                h5_path = os.path.join(h5_root, 'FCD_CHINA_STOCK_DAILY_SUNTIME.h5')
            else:
                h5_root = os.path.join(settings.BASE_DIR, 'DATABASE/SUNTIME/', table_name)
                if not os.path.exists(h5_root):
                    os.makedirs(h5_root)
                h5_path = os.path.join(h5_root, table_name + '.h5')

            logger.info("开始更新h5：table_name={}, h5={}".format(table_name, h5_path))
            source_path = os.path.join(root_folder, table_name)
            csv_list = [os.path.join(source_path, i) for i in os.listdir(source_path)]

            if table_name in table_list3:
                csv2h5(csv_list, h5_path, table_name, 'create', min_size=0)
            else:
                csv_list.sort()
                csv_date_list = [int(i[-12:-4]) for i in csv_list]
                csv_date_list_take = [i for i in csv_date_list if sdate <= i <= edate]
                csv_list_take = [source_path + '/' + str(i) + '.csv' for i in csv_date_list_take]
                csv_list_take.sort()
                csv2h5(csv_list_take, h5_path, table_name, 'append', min_size=0)
            logger.info("完成更新h5：table_name={}, h5={}".format(table_name, h5_path))
    except Exception as e:
        logger.error("更新失败, table_name={}, msg={}".format(table_name, e))


if __name__ == '__main__':
    start, end, _ = check_update_date()
    utils.create_flag(str(end) + '_' + 'SUNTIME.start', end)
    update_suntime_data(start, end)

    utils.create_flag(str(end) + '_' + 'SUNTIME.success', end)
    copy_file_from002_to80(start)