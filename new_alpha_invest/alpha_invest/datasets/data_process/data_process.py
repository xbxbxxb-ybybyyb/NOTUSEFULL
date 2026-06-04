# 數據預處理
from tquant.stock_data import StockData
from tquant.basic_data import BasicData
import pandas as pd
import os
from get_neu_factor import get_neu_factor
from .normalziaton import median_filter
from select_factor import select_factor
import numpy as np


#1 去除nan值
#2 去極值
#3 因子中性化
#4 過濾漲停股 st股 新上市的股票
#5 過濾因子： 根據超額收益的變化

# 思考： 先過濾漲停股和因子 再做預處理
#         原始的因子数据的格式
# 正投原始的数据文件是每个因子一个pkl文件的形式 每个文件是pickle的形式
# 最终的输出的形式是

#  按天过滤 股票 自定义过滤规则
# def data_process_filter_stock(factor_df):
#     """
#     :param factor_df:  no index dataframe  columns： mdddate securityid fac1 fac2 fac3
#     :param alpha_universe:
#     :return:
#     """
#     factor_df_is_universe = filter_universe(factor_df)
#     return factor_df_is_universe
#
#
# def filter_universe(df, start_date, end_date):
#     """
#
#     :param df:  multiindex dataframe
#     :param alpha_universe: 漲停股st股票新上市股票信息
#     :return: 按行過濾之後的df
#     """
#     # 获取每一天需要被过滤调的标的列表
#     date_list = bd.get_trading_day(start_date, end_date)
#     stocks_all = sd.get_plate_info('MARKET', end_date, 'ALLA_HIS').loc[:, 'stock'].tolist()
#
#     listing_df = sd.get_factor_newsmsg(stocks_all, ['listing_date', 'delisting_date']).fillna(0, inplace=True)
#     listing_df= listing_df[(listing_df['listing_date']<= int(end_date))&(listing_df['listing_date']>= int(start_date))]
#
#     mkt_cap_df = sd.get_factor_valuation_metrics(stocks_all, (start_date, end_date),['mkt_cap_ard']).unstack(level=1)
#
#     pct_chg_df = sd.get_factor_price_daily(stocks_all, (start_date, end_date),['pct_chg'])['pct_chg'].unstack(level=1)
#     for date in date_list:
#         filter_stock_list = filter_universe_per_day(date, stocks_all, listing_df, mkt_cap_df,pct_chg_df)
#         df = df[(df.MDDate.isin([date]))&(df.SecurityID.isin(filter_stock_list))]
#     return df
#
#
#
#
# def filter_universe_per_day(date, stocks_all, listing_df, mkt_cap_df, pct_chg_df):
#     """
#
#     :param date:
#     :return:
#     """
#     # 过滤条件1 上市不满俩月
#     filter_stock_list1 = list(listing_df[listing_df['listing_date'] <= (int(date) - 2000)].index)
#
#     # 条件2 市值在后5%
#     mkt_cap_df_rank= mkt_cap_df.dropna().rank().reset_index(level=0, drop=True, inplace=True)
#     filter_stock_list2 = list(mkt_cap_df_rank.index)[int(len(mkt_cap_df_rank.index)*0.95):]
#
#     # 条件3 STPT和停牌和涨停的股票
#     filter_stock_list3 = sd.stock_filter(stocks_all, filter_date=str(date), filter_type='SSO')['stock'].values.tolist()
#
#     # 条件4 过滤涨幅超过9.8的
#     pct_chg_ser = pct_chg_df.loc[date,:]
#     filter_stock_list4 = list(pct_chg_ser[(pct_chg_ser.values<9.8) | (pct_chg_ser.values>-9.8)].index)
#
#     # 求交集
#     filter_stock_list = set(filter_stock_list1).intersection(set(filter_stock_list2)).intersection(
#         set(filter_stock_list3)).intersection(set(filter_stock_list4))
#     return filter_stock_list


def read_pickle_file(base_path, factor_name):
    file_name = factor_name+'.pkl'
    full_path = os.path.join(base_path, file_name)
    df = pd.read_pickle(full_path)
    return df


def save_pickle_file(df, file_name, target_path):
    return pd.to_pickle(df, os.path.join(target_path, file_name))


def data_process(base_path, factor_list, start_date, end_date):
    """

    :param base_path:
    :param factor_list:
    :return:
    """
    bd = BasicData()
    sd = StockData()
    trade_edate = bd.get_trading_day(end_date, -5)[-1]
    date_list = bd.get_trading_day(start_date, end_date)
    stock_list = sd.get_plate_info('MARKET', trade_edate, 'ALLA_HIS')['stock'].tolist()

    print("preparing alpha universe data")
    df1 = sd.get_factor_evaluation(stock_list, (start_date, end_date), ['alpha_universe'])
    data = df1['alpha_universe'].unstack()
    alpha_filter = data.astype(float)
    is_alpha_universe = (alpha_filter == 1).loc[start_date:end_date]

    print("preparing industry data")
    df2 = sd.get_stock_industry(stock_list, date_list, 'SW', industry_level=1)
    df2.set_index(['tradingday', 'trading_code'], inplace=True)
    df_ind = df2['industry_code']
    df_ind.index.names = [None, None]
    industry_code_all = df_ind.unstack(level=1)[start_date:end_date]

    print("preparing size data")
    df3 = sd.get_factor_valuation_metrics(stock_list, date_list, ['mkt_cap_ard'])
    df3.reset_index(inplace=True)
    df3.set_index(['mddate', 'stock'], inplace=True)
    df_mkt_cap_ard = df3['mkt_cap_ard']
    df_mkt_cap_ard.index.names = [None, None]
    size = np.log(df_mkt_cap_ard.unstack(level=1)[start_date:end_date])


    neu_factor_df_res = []
    for factor_name in factor_list:
        try:
            print("loading factor data")
            factor_df = read_pickle_file(base_path=base_path, factor_name=factor_name).loc[start_date:end_date]
            print("filter alpha universe")
            alpha_universe_factor_df = factor_df[is_alpha_universe].loc[start_date:end_date]
            print("get neu factor data")
            neu_factor_df = get_neu_factor(alpha_universe_factor_df, industry_code_all, size).stack().to_frame()
            neu_factor_df.columns = [factor_name]
            neu_factor_df_res.append(neu_factor_df)
            print("factor_name: {} is finished".format(factor_name))
        except:
            continue
    print("start concat res")
    neu_factors_df = pd.concat(neu_factor_df_res,axis=1)
    neu_factor_df.index.names = ['mddate', 'stock']
    neu_factors_df = neu_factors_df.reset_index().dropna(how='all', axis=0)
    print("save res pickle")
    save_pickle_file(neu_factors_df, 'processed_data_{}_{}.pkl'.format(start_date, end_date), '.')

    factor_union_dict = {}
    for factor in datax.columns:#datax, multiindex dataframe
        factor_df = median_filter(datax[factor].unstack(), 5)
        mean = factor_df.apply(lambda x: np.nanmean(x), axis=1)
        std = factor_df.apply(lambda x: np.nanstd(x), axis=1)
        factor_df1 = factor_df.subtract(mean, axis=0).divide(std, axis=0)
        factor_union_dict[factor] = factor_df1.stack()

    return True


if __name__ == "__main__":
    #factor_list = select_factor()
    #print(factor_list)
    factor_list = []
    data_process("/data/group/800002/alpha_factor/lib/x_factor_lib/", factor_list=factor_list,start_date='20140601', end_date='20150601')

