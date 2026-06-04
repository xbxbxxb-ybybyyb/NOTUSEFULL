
from tquant.basic_data import BasicData
from tquant.stock_data import StockData
import pandas as pd
import numpy as np
from normalziaton import Normalization2
from tquant.strategy.factor_tester.normalization import Normalization2
from sklearn.linear_model import LinearRegression
import mkl
mkl.set_num_threads(5)

def update_neu_factor(factor, norm_size, industry_mark_df, dates_need_update):
    black_date = ['20160104', '20160105', '20160106', '20160107']
    if factor.index[-1] != norm_size.index[-1]:
        assert False
    if factor.index[0] != norm_size.index[0]:
        assert False

    norm_factor = Normalization2(factor)
    norm_factor = norm_factor.norm_dataframe()

    factor_neu_df = []
    for cur_date in dates_need_update:
        if cur_date in black_date:
            factor_neu_df.append(norm_factor.loc[cur_date])
        else:
            factor_cur_day = norm_factor.loc[cur_date]
            factor_cur_day.name = 'factor'

            norm_size_cur_day = norm_size.loc[cur_date]
            industry_mark_df_cur_day = industry_mark_df.xs(cur_date, level=1).transpose()

            prepared_neu = pd.concat([factor_cur_day, norm_size_cur_day, industry_mark_df_cur_day], axis=1,
                                     sort=True).dropna()
            reg = LinearRegression(fit_intercept=False, n_jobs=1)
            x = prepared_neu.drop(['factor'], axis=1).values
            y = prepared_neu.transpose().loc[['factor']].values.T
            reg.fit(x, y)
            residual = y - reg.predict(x)
            factor_series = pd.Series(np.nan, index=factor_cur_day.index, name=cur_date)
            factor_series.loc[prepared_neu.index] = residual.T[0]
            factor_neu_df.append(factor_series)

    factor_neu_df = pd.concat(factor_neu_df, axis=1).transpose()
    return factor_neu_df

def get_neu_factor(factor_df, industry_code_all, size):

    # industry_code_all = get_industry_code_all(factor_start_date, factor_end_date)
    industry_list = industry_code_all.stack().unique()
    industry_list = industry_list[industry_list != 0]

    industry_mark = {}
    for industry in industry_list:
        tmp = pd.DataFrame(0., index=industry_code_all.index, columns=industry_code_all.columns)
        tmp[industry_code_all == industry] = 1
        industry_mark[industry] = tmp
    industry_mark_df = pd.concat(industry_mark)

    # size = get_mkt_cap_ard(factor_start_date, factor_end_date)
    # size = np.log(size)

    norm_size = Normalization2(size, axis=0)
    norm_size = norm_size.norm_dataframe()

    if industry_code_all.index[-1] != norm_size.index[-1]:
        assert False
    if industry_code_all.index[0] != norm_size.index[0]:
        assert False
    try:
        dates_need_update = factor_df.index.tolist()
        factor_neu_update = update_neu_factor(factor_df, norm_size, industry_mark_df, dates_need_update)
        factor_neu_all = factor_neu_update
        factor_neu_all = factor_neu_all.sort_index()
        return factor_neu_all
    except:
        raise AssertionError("factor data has some problem in neutralization, please check your data")