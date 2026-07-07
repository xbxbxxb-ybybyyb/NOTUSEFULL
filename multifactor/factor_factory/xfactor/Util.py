import pandas as pd
import numpy as np


def array_coef(x, y):
    x_values = x.values
    y_values = y.values
    x_values[np.isinf(x_values)] = np.nan
    y_values[np.isinf(y_values)] = np.nan

    delta_x = x_values - np.nanmean(x_values, axis=0)
    delta_y = y_values - np.nanmean(y_values, axis=0)
    multi = np.nanmean(delta_x * delta_y, axis=0) / (np.nanstd(delta_x, axis=0) * np.nanstd(delta_y, axis=0))
    multi[np.isinf(multi)] = np.nan
    return pd.Series(multi, index=x.columns)

def rolling_corr(df_x, df_y, window=None):
    """"""
    assert df_x.shape[0] == df_y.shape[0], 'dims must be same'

    corr = pd.DataFrame(np.nan, index=df_x.index, columns=df_x.columns)

    if window == None or window <= 0:
        window = df_x.shape[0]
    if window <= df_x.shape[0] and window > 1:
        for idx, index in enumerate(df_x.index):
            if idx >= window - 1:
                corr.loc[index] = array_coef(df_x.iloc[idx - window + 1:idx + 1],df_y.iloc[idx - window + 1:idx + 1]).values
    return corr

def array_column_wise_regress(df_x, df_y):
    x_values = df_x.values
    y_values = df_y.values
    x_values[np.isinf(x_values)] = np.nan
    y_values[np.isinf(y_values)] = np.nan

    mean_x = np.nanmean(x_values, axis=0)
    mean_y = np.nanmean(y_values, axis=0)
    delta_x = x_values - mean_x
    delta_y = y_values - mean_y
    beta = np.nanmean(delta_x * delta_y, axis=0) / np.nanstd(delta_x, axis=0) ** 2
    beta[np.isinf(beta)] = np.nan
    const = mean_y - beta * mean_x
    resid = np.subtract(y_values - np.multiply(x_values, beta), const)

    beta = pd.Series(beta, index=df_x.columns)
    resid = pd.DataFrame(resid, index=df_x.index, columns=df_x.columns)
    return beta, resid


