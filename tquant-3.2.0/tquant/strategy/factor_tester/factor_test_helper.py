import os
import numpy as np
import pandas as pd
from tquant.strategy.factor_tester.normalization import Normalization2
from sklearn.linear_model import LinearRegression
import mkl

mkl.set_num_threads(5)
os.environ["OPENBLAS_NUM_THREADS"] = "1"
black_date = ['20160104', '20160105', '20160106', '20160107']


def update_neu_factor(factor, norm_size, industry_mark_df, dates_need_update):
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
