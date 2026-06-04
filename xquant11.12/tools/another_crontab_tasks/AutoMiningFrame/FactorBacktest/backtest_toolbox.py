import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, spearmanr


def plt_distribution(df, factor, ax=None):
    if ax is None:
        plt.figure(figsize=(16, 9))
        ax = plt.gca()
    fac = df[factor].dropna()
    des = fac.describe()
    sns.distplot(fac, color="b", norm_hist=True, kde=True, ax=ax, kde_kws={'bw': des['mean']})
    ax.set_ylim(0, ax.dataLim.ymax * 1.1)
    ax.axvline(des['mean'], color='w', linestyle='dashed', linewidth=3)
    ax.axvline(des['mean'] + des['std'], color='w', linestyle=':', linewidth=2)
    ax.axvline(des['mean'] - des['std'], color='w', linestyle=':', linewidth=2)
    ax.set_ylabel('Density', fontsize=16)
    ax.set_xlabel(factor, fontsize=16)


def plt_scatter(df, x, y, ax=None):
    if ax is None:
        plt.figure(figsize=(16, 9))
        ax = plt.gca()
    ax.scatter(df[x], df[y])
    mean = df[x].mean()
    std = df[x].std()
    ax.axvline(mean, color='r', linestyle='dashed', linewidth=3)
    ax.axvline(mean + std, color='r', linestyle=':', linewidth=2)
    ax.axvline(mean - std, color='r', linestyle=':', linewidth=2)
    ax.axhline(0, color='y', linestyle=':', linewidth=2)
    ax.set_xlabel(x, fontsize=16)
    ax.set_ylabel(y, fontsize=16)


def get_ic(df, factor, ret='ret', ic_type='normal', need_factor_name=False):
    assert (ic_type == 'normal') ^ (ic_type == 'rank'), 'IC type should be either "normal" or "rank"!'
    try:
        if ic_type == 'normal':
            factor_ic = pearsonr(df[factor], df[ret])[0]
        else:
            factor_ic = spearmanr(df[factor], df[ret])[0]
        if need_factor_name:
            return [factor,ret,factor_ic]
        else:
            return factor_ic
    except Exception as e:
        print(f'Error occured when calculating IC: {e}')
        if need_factor_name:
            return [factor,ret,np.nan]
        else:
            return np.nan