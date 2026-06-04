from xquant.factordata import FactorData
import pandas as pd
from alpha_invest.datasets.data_utils import get_n_days_off, convert_df_index_type
from alpha_invest.datasets.factor import get_panel_daily_pv_df
import numpy as np
from alpha_invest import alpha_logger
from sklearn.preprocessing import LabelEncoder


fa = FactorData()


def load_label(stock_list,  date_list, label_type='twap', holding_period=1, time_interval=None):
    start_date, end_date = date_list[0], date_list[1]
    if label_type == 'coda':
        valid_end_date = get_n_days_off(end_date, holding_period + 2)[-1]
        data_df_coda = get_panel_daily_pv_df(stock_list, date_list,
                                                 pv_type='twp_coda', adj_type='FORWARD')
        return_rate_df = data_df_coda.shift(-holding_period) / data_df_coda - 1  # 计算收益率
        # factor的index是timestamp, 而非8位数的日期，这里做转化，以便后续可比
        return_rate_df = convert_df_index_type(return_rate_df, 'date_int', 'timestamp')
        return return_rate_df
    elif label_type == 'vwap':
        valid_end_date = get_n_days_off(end_date, holding_period + 2)[-1]
        data_df_amt = get_panel_daily_pv_df(stock_list, date_list,
                                                pv_type='amt', adj_type='NONE')
        data_df_volume = get_panel_daily_pv_df(stock_list, date_list,
                                                   pv_type='volume', adj_type='NONE')
        data_vwap = data_df_amt / data_df_volume  # 计算vwap
        adj_df = get_panel_daily_pv_df(stock_list, start_date, end_date, 'adjfactor')
        data_vwap = data_vwap * adj_df  # 计算后复权的vwap
        return_rate_df = data_vwap.shift(-holding_period) / data_vwap - 1  # 计算收益率
        # factor的index是timestamp, 而非8位数的日期，这里做转化，以便后续可比
        return_rate_df = convert_df_index_type(return_rate_df, 'date_int', 'timestamp')
        alpha_logger.debug("{} factor shape: {}".format(label_type, return_rate_df.shape))
        return return_rate_df
    elif label_type == 'twap':
        valid_end_date = get_n_days_off(end_date, holding_period + 2)[-1]
        data_df_coda = get_panel_daily_pv_df(stock_list, date_list,
                                                 pv_type='twap', adj_type='FORWARD')
        return_rate_df = data_df_coda.shift(-holding_period) / data_df_coda - 1  # 计算收益率
        # factor的index是timestamp, 而非8位数的日期，这里做转化，以便后续可比
        return_rate_df = convert_df_index_type(return_rate_df, 'date_int', 'timestamp')
        alpha_logger.debug("{} factor shape: {}".format(label_type, return_rate_df.shape))
        return return_rate_df
    elif label_type == 'twap_excess_300':
        benchmark = "000300.SH"
        valid_end_date = get_n_days_off(end_date, holding_period + 2)[-1]
        price_df = get_panel_daily_pv_df(stock_list, date_list, pv_type='twap', adj_type='FORWARD')
        benchmark_price_df = get_panel_daily_pv_df([benchmark], date_list, pv_type='twap')
        return_rate_df = price_df.shift(-holding_period) / price_df - 1
        return_rate_benchmark_df = benchmark_price_df.shift(-holding_period) / benchmark_price_df - 1
        return_rate_benchmark_df = pd.DataFrame(np.tile(return_rate_benchmark_df.values, [1, return_rate_df.shape[1]]),
                                                index=return_rate_df.index, columns=return_rate_df.columns)
        excess_return_df = return_rate_df - return_rate_benchmark_df
        excess_return_df = convert_df_index_type(excess_return_df, 'date_int', 'timestamp')
        alpha_logger.debug("{} factor shape: {}".format(label_type, excess_return_df.shape))
        return excess_return_df
    elif label_type == 'vwap_excess_300':
        benchmark = "000300.SH"

        valid_end_date = get_n_days_off(end_date, holding_period + 2)[-1]
        price_df = get_panel_daily_pv_df(stock_list, date_list, pv_type='vwap', adj_type='BACKWARD2')
        benchmark_price_df = get_panel_daily_pv_df([benchmark], date_list, pv_type='close')
        return_rate_df = price_df.shift(-holding_period) / price_df - 1
        return_rate_benchmark_df = benchmark_price_df.shift(-holding_period) / benchmark_price_df - 1
        return_rate_benchmark_df = pd.DataFrame(np.tile(return_rate_benchmark_df.values, [1, return_rate_df.shape[1]]),
                                                index=return_rate_df.index, columns=return_rate_df.columns)
        excess_return_df = return_rate_df - return_rate_benchmark_df
        excess_return_df = convert_df_index_type(excess_return_df, 'date_int', 'timestamp')
        alpha_logger.debug("{} factor shape: {}".format(label_type, excess_return_df.shape))
        return excess_return_df


def transform_label_2binray(df_label):
    """
    df_label的为截面因子形式，行为日期，列为标的
    :param df_label:
    :return:
    """
    def float2binray(x):
        if x<=0:
            x = 0
        else:
            x = 1
        return x
    df_label = df_label.applymap(lambda x: float2binray(x))
    return df_label


if __name__=="__main__":
    fa = FactorData()
    days = fa.tradingday("20190701", "20191231")
    stocks = fa.hset("MARKET", "20190701", "ALLA")["stock"].tolist()
    df = load_label(stocks,  days, label_type='vwap_excess_300')
    print(df.head())
    df_binray = transform_label_2binray(df)
    print(df_binray.head())
