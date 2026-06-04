from xquant.factordata import FactorData
import pandas as pd
from alpha_invest import alpha_logger
fa = FactorData()

def get_panel_daily_pv_df(stock_list, query_date_list, pv_type='close', adj_type='NONE') -> pd.DataFrame:
    """
    获取日级别的价量（pv - price & volume）行情，形式是panel data，即[股票list * 日期list]
    :param stock_list:  股票代码列表，e.g., ['000001.SZ', '600000.SH', '601688.SH']
    :param start_date_int: 查询起始日，e.g., 20180801，如当天是交易日，则将被包括进来
    :param end_date_int: 查询终止日， e.g., 20180808，如当天是交易日，则将被包括进来
    :param pv_type: 查询类型
    :param adj_type: 复权类型，'NONE'-不复权，'BACKWARD2'-（从上市日）向后复权， 'FORWARD' - 从end_date_int日向前复权；
                      仅对各种价格有效，对volume, amt, suspension和pct_chg无意义，对指数无意义，
    :return: 返回类型为DataFrame, 行为日期，列为股票代码
    """
    start_date_int = query_date_list[0]
    end_date_int = query_date_list[-1]

    pv_factors = ['close', 'open', 'high', 'low', 'pre_close', 'volume', 'amt', 'pct_chg', 'turn', 'vwap','twap',
                   'buy_twap', 'buy_twap_fill_rate', 'sell_twap', 'sell_twap_fill_rate', 'buyable_volume',
                   'sellable_volume', 'vwap', 'dealnum', 'buy_vwap', 'sell_vwap', 'suspension', 'UpPrice',
                   'DownPrice', 'UpPrice2', 'DownPrice2', "adjfactor"]
    if pv_type in pv_factors[:10]:
        pass
    else:
        raise TypeError
    available_index_list = ["000001.SH", "000016.SH", "000300.SH", "000905.SH", "000906.SH", "399001.SZ", "399006.SZ"]
    for available_index in available_index_list:  # 如要取指数的数据，但涉及到复权因子或复权价格
        if available_index in stock_list and adj_type is not 'NONE':
            raise Exception('Adjustment price is not applicable to index data')

    data_df = fa.get_factor_value("Basic_factor", stock_list, query_date_list, [pv_type], return_single_factor=True)
    data_df = data_df.loc[start_date_int: end_date_int]
    data_df = data_df.reindex(columns=stock_list)

    if adj_type == "FORWARD" and pv_type in ['open', 'high', 'low', 'close', 'pre_close', 'twap', 'vwap',
                                             'buy_twap','sell_twap', 'buy_vwap', 'sell_vwap', 'UpPrice', 'DownPrice']:
        raise Exception()
    elif adj_type == "BACKWARD2" and pv_type in ['open', 'high', 'low', 'close', 'pre_close', 'twap', 'vwap',
                                                 'buy_twap','sell_twap', 'buy_vwap', 'sell_vwap', 'UpPrice', 'DownPrice']:
        adj_df = fa.get_factor_value("Basic_factor", stock_list, query_date_list, ['adjfactor'], return_single_factor=True)
        data_df = data_df * adj_df
    # 因为Python原生的None在pandas/numpy中兼容性不好，影响读写以及在其他模块中的调用，这里转为np.nan
    if pv_type == 'dealnum':
        data_df = data_df.astype('float64')
    data_df = pd.DataFrame(data_df.values + 0.0, index=data_df.index, columns=data_df.columns)
    if pv_type == 'volume':  # 因得到的VOLUME单位是“手”，这里转为“股”
        data_df = pd.DataFrame(data_df.values * 100, index=data_df.index, columns=data_df.columns)
    elif pv_type == 'amt':  # 因得到的AMOUNT单位是“千元”，这里转为“元”
        data_df = pd.DataFrame(data_df.values * 1000, index=data_df.index, columns=data_df.columns)
    data_df = data_df.reindex(columns=stock_list)  # 使输出的列名顺序等于输入的顺序
    data_df.index = [int(day) for day in data_df.index]
    alpha_logger.debug("{} factor shape: {}".format(pv_type, data_df.shape))
    return data_df


def get_factor_values(stock_list, query_date_list, factor_list):
    #query_date_list = sorted(query_date_list)
    file_seg = [('20140602', '20150601'), ('20150602', '20160601'),
                ('20160602', '20170601'), ('20170602', '20180601'),
                ('20180602', '20190601'), ('20190602', '20200601'),
                ('20200602', '20210601')]
    date_dict = {}
    for date in query_date_list:
        for i in range(len(file_seg)):
            if file_seg[i][0] < date < file_seg[i][1]:
                if file_seg[i][0]+'_'+file_seg[i][1] not in date_dict:
                    date_dict[file_seg[i][0]+'_'+file_seg[i][1]] = [date]
                else:
                    date_dict[file_seg[i][0] + '_' + file_seg[i][1]].append(date)
                break

    res_df_list = []
    for key, item in date_dict.items():
        df_tmp = pd.read_pickle("processed_data_{}.pkl".format(key))
        df_tmp = df_tmp[['mddate', 'stock']+factor_list]
        df_tmp = df_tmp[(df_tmp['mddate'].isin(item)) & (df_tmp['stock'].isin(stock_list))]
        res_df_list.append(df_tmp)
    res_df = pd.concat(res_df_list, axis=0)
    res_df = res_df.set_index('mddate')
    return res_df













if __name__=="__main__":
    fa = FactorData()
    days = fa.tradingday("20190701", "20191231")
    stocks = fa.hset("MARKET", "20190701", "ALLA")["stock"].tolist()
    df = get_panel_daily_pv_df(stocks, days, "close", "FORWARD")
    print(df)