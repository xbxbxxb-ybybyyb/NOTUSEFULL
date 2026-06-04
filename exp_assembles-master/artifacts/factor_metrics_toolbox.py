import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, spearmanr


def plt_distribution(df, factor, ax=None):
    if type(factor) == list:
        factor = factor[0]
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


def get_ic(df, factor, ret='ret', ic_type='normal'):
    assert (ic_type == 'normal') ^ (ic_type == 'rank'), 'IC type should be either "normal" or "rank"!'
    try:
        if ic_type == 'normal':
            factor_ic = pearsonr(df[factor], df[ret])[0]
        else:
            factor_ic = spearmanr(df[factor], df[ret])[0]
        return factor_ic
    except Exception as e:
        print(df[factor])
        print(df[ret])
        print(f'Error occured when calculating IC: {e}')
        return np.nan

def merge_position_for_plot(long_idxs, short_idxs):
    x = []
    y = []
    long_idx_list, short_idx_list = long_idxs[:], short_idxs[:]
    while long_idx_list or short_idx_list:
        if long_idx_list and short_idx_list:
            if long_idx_list[0][0] <= short_idx_list[0][0]:
                cor = long_idx_list.pop(0)
                x.append(cor[0])
                y.append(0)
                x.append(cor[0])
                y.append(1)
                x.append(cor[-1])
                y.append(1)
                x.append(cor[-1])
                y.append(0)
            else:
                cor = short_idx_list.pop(0)
                x.append(cor[0])
                y.append(0)
                x.append(cor[0])
                y.append(-1)
                x.append(cor[-1])
                y.append(-1)
                x.append(cor[-1])
                y.append(0)
        elif long_idx_list:
            cor = long_idx_list.pop(0)
            x.append(cor[0])
            y.append(0)
            x.append(cor[0])
            y.append(1)
            x.append(cor[-1])
            y.append(1)
            x.append(cor[-1])
            y.append(0)
        elif short_idx_list:
            cor = short_idx_list.pop(0)
            x.append(cor[0])
            y.append(0)
            x.append(cor[0])
            y.append(-1)
            x.append(cor[-1])
            y.append(-1)
            x.append(cor[-1])
            y.append(0)
    return x, y 

def plot_market_factor1(factor_label_market, factor_name, x_list=[], y_list=[]):
    if type(factor_name) == str:
        factor_name = [factor_name]
    factor_df = factor_label_market[factor_name]
    market_df = factor_label_market[["BasePx"]]

    def x_fmt_func(x, pos=None):
        idx = np.clip(int(x+0.5), 0, factor_df.shape[0]-1)
        return factor_df.index[idx]

    # 验证 factor_df 和 market_df 长度是否对齐
    idx_proxy = np.arange(factor_df.shape[0])
    factor_name = factor_df.columns[0]
    market_name = market_df.columns[0]

    fig=plt.figure(4,figsize=(100, 30))##增添画布，必须要有这一步
    ax1=fig.add_subplot(411)  ##切割画布，并且定位画布到1行4列的第一个

    # f, axs = plt.subplots(2, 1, figsize=(200, 10))
    # ax2=fig.add_subplot(421, sharex=ax1)
    ax2 = ax1.twinx()

    # 绘制原始行情
    y1min, y1max = (None, None)
    ax1.plot(idx_proxy, market_df.values, alpha=1.0, lw=1.5, color='blue')
    # ax1.xaxis.set_major_formatter(MTK.FuncFormatter(x_fmt_func))

    ax1.set(ylabel=market_name, xlabel="Time")
    ax1.set_title("Factor Value & Market Value")
    ax1.axhline(0.0, linestyle='-', color='black', lw=1, alpha=0.8)
    ax1.legend([market_name], loc='upper left')
    y1min, y1max = ax1.get_ylim()
    ax1.set_ylim([y1min, y1max])


    # 绘制因子值
    ax2.plot(idx_proxy, factor_df.values, alpha=0.7, lw=2.5, color='red')
    ax2.set(ylabel=factor_name, xlabel="Time")
    ax2.legend([factor_name], loc='upper right')
    y2min, y2max = ax2.get_ylim()
    ax2.set_ylim([y2min, y2max])

    # 绘制持仓
    ax3=fig.add_subplot(412, sharex=ax2)
    ax3.plot(x_list, y_list, color="blue", lw=2.5)
    # y3min, y3max = ax3.get_ylim()
    # ax3.set_ylim([-1.1, 1.1])

    return ax1