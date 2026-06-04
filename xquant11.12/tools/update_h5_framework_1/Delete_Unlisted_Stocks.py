# _*_ coding:utf-8 _*_

import pandas as pd
from Wind.utils import *
from log import Log
import datetime as dt

logger = Log("re_write_h5")

def re_write_h5(h5_name,sql_config):
    logger.info("Start...")
    source_path = "/app/data/wdb_h5/WIND_TEST/"
    hdf5 = source_path + h5_name + "/" + h5_name + ".h5"
    df = read_data([sdate, edate], alt=hdf5)
    logger.info("get the history H5 data...")
    factor_list = list(df.columns)
    df.reset_index(inplace=True)
    for date in cdate_list:
        time1 = dt.datetime.strptime(str(dt.datetime.now().date()) + '1:00', '%Y-%m-%d%H:%M')
        time2 = dt.datetime.strptime(str(dt.datetime.now().date()) + '2:00', '%Y-%m-%d%H:%M')
        now = dt.datetime.now()
        if now > time1 and now <= time2:
            logger.info("time sleep 5 hours...")
            time.sleep(18000)
            logger.info("Continue...")
        df_day = df[df['dt'] == pd.Timestamp(str(date))]
        logger.info("get one day data and write...")
        for factor_name in factor_list:
            df_factor_1 = df_day.loc[:, ["Ticker", "dt", factor_name]]
            logger.info("stock filter ...")
            df_factor = stock_select(df_factor_1, date, factor_name, sql_config)
            df_factor.set_index(['dt', 'Ticker'], inplace=True)
            df_factor = df_factor.loc[:, factor_name]
            logger.info("Acquired the factor %s data ,then write to %s !" % (factor_name, h5_name))
            pd_hdf5_writer(pd_factor=df_factor, hdf5=hdf5, dataset=factor_name, append=True)


if __name__ == "__main__":
    start_date = 20140605
    end_date = 20140608
    sdate, edate, cdate_list = check_update_date(start_date, end_date)
    xml_path = "config-h5.xml"
    sql_config = get_sql_config(xml_path)
    h5_name = "INDUSTRY_CHINA_STOCK_DAILY_WIND"
    re_write_h5(h5_name,sql_config)


