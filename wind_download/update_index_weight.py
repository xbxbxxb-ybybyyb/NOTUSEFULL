'''
if reload history data, you should remove csv in SH50 by hand first.
weiych
'''
import time
import os
from loguru import logger
import settings
import utils
from multifactor.data.utils import *
from xquant.factordata import FactorData

s = FactorData()


def retriver(date_list, factors):
    namedict = {'HS300': 'index_weight_hs300', 'SH50': 'index_weight_sh50', 'ZZ500': 'index_weight_zz500'}
    for date in date_list:
        date = str(date)
        for factor in factors:
            df = s.get_factor_value('Basic_factor', stock=[], mddate=[date], factor_names=[namedict[factor]])
            if len(df) == 0:
                continue
            df = df.reset_index()[['stock', namedict[factor]]]
            df = df.rename(columns={'stock': 'Ticker', namedict[factor]: factor})
            df = df.set_index('Ticker')
            df.to_csv(os.path.join(settings.BASE_DIR, "LOCAL_DATA/CSV/stock_universe/", factor, date + '.csv'))
            logger.info("下载完成: factor_name={}".format(factor))


def update_universe_raw(date_list, csv_path, h5_path, factor_list, operation='append'):
    logger.info("开始更新h5: h5={}".format(h5_path))
    weight_list = ['index_weight_sh50', 'index_weight_hs300', 'index_weight_zz500']
    df_list = []
    for date in date_list:
        tmp_list = []
        df = get_stock_list(date)
        df.reset_index(inplace=True)
        df['dt'] = dt.datetime.strptime(str(date), '%Y%m%d')
        df.set_index(['dt', 'Ticker'], inplace=True)
        tmp_list.append(df)
        for factor_name in factor_list:
            if factor_name == 'SH50':
                weight_name = 'index_weight_sh50'
            elif factor_name == 'ZZ500':
                weight_name = 'index_weight_zz500'
            elif factor_name == 'HS300':
                weight_name = 'index_weight_hs300'
            if factor_name == 'SH50' and date < 20100101:
                continue
            fname = os.path.join(csv_path, factor_name, str(date) + '.csv')
            dat = pd.read_csv(fname)
            dat['dt'] = dt.datetime.strptime(str(date), '%Y%m%d')
            dat.set_index(['dt', 'Ticker'], inplace=True)
            dat.columns = [weight_name]
            dat = pd.concat([df, dat], axis=1)
            dat.fillna(0, inplace=True)
            dat[weight_name] = dat[weight_name] / 100.0

            if len(dat) > 0:
                tmp_list.append(dat[[weight_name]])

        df = pd.concat(tmp_list, axis=1)

        for col in weight_list:
            if col not in df.columns:
                continue
            df[col].fillna(0, inplace=True)
        df_list.append(df)
    df = pd.concat(df_list)
    for colume in df.columns:
        if colume == 'alla':
            continue
        if operation == 'append':
            IO.pd_hdf5_writer(df[[colume]], h5_path, dataset=colume, append=True)
        else:
            IO.pd_hdf5_writer(df[[colume]], h5_path, dataset=colume)
    logger.info("完成更新h5: h5={}".format(h5_path))


def get_stock_list(date):
    table_name = 'AShareDescription'
    h5_path = os.path.join(settings.BASE_DIR, 'DATABASE/WIND/')
    table_path = os.path.join(h5_path, table_name, table_name + '.h5')
    df = IO.read_data([20090101, 21000101], columns=['S_INFO_LISTDATE', 'S_INFO_DELISTDATE'], alt=table_path)
    df.reset_index('dt', inplace=True)
    df.drop('dt', axis=1, inplace=True)
    df.fillna(20990101, inplace=True)

    tmp_df = df[df['S_INFO_DELISTDATE'] > date]
    tmp_df = tmp_df[tmp_df['S_INFO_LISTDATE'] <= date]
    tmp_df['alla'] = True
    tmp_df = tmp_df[['alla']]
    return tmp_df


sdate, edate, cdate_list = check_update_date()

csv_path = os.path.join(settings.BASE_DIR, 'LOCAL_DATA/CSV/stock_universe/')
h5_path_source = os.path.join(settings.BASE_DIR,
                              'INDEXWEIGHT/CHINA_STOCK/DAILY/CSI/INDEXWEIGHT_CHINA_STOCK_DAILY_CSI.h5')
factor_list = ['HS300', 'ZZ500', 'SH50']

utils.create_flag(str(edate) + '_' + 'INDEX_WEIGHT.start', edate)

fileflag = True
while fileflag:
    retriver(cdate_list, factor_list)
    if os.path.exists("/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/stock_universe/" + 'SH50' + '/' + str(
            cdate_list[-1]) + '.csv'):
        logger.info("权重CSV文件已下载")
        fileflag = False
    else:
        logger.info("权重CSV文件未下载，300s后重试下载")
        time.sleep(300)

update_universe_raw(cdate_list, csv_path, h5_path_source, factor_list)

utils.create_flag(str(edate) + '_' + 'INDEX_WEIGHT.success', edate)
