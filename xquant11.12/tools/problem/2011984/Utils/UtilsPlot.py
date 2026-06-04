import matplotlib.pyplot as plt
from matplotlib import font_manager, gridspec
import pandas as pd
import numpy as np
import math


myfont = font_manager.FontProperties(fname='/data/user/011668/Utils/msyh.ttf')
myfont_legend = font_manager.FontProperties(fname='/data/user/011668/Utils/msyh.ttf', size=8)


def plot1(x, y, title=''):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(x, y, '-')
    if title != '':
        plt.title(title, fontproperties=myfont)
    plt.tight_layout()
    plt.show()


def plot2(x, y1, y2, y1_name, y2_name, title=''):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    lns = []
    lns1 = ax.plot(x, y1, '-', color='darkorange', label='{}(left)'.format(y1_name))
    lns += lns1
    ax2 = ax.twinx()
    lns2 = ax2.plot(x, y2, '-', color='#1f77b4', label='{}(right)'.format(y2_name))
    lns += lns2
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, ncol=4, prop=myfont)
    for tl in ax.get_yticklabels():
        tl.set_color('darkorange')
    for tl in ax2.get_yticklabels():
        tl.set_color("#1f77b4")
    if title != '':
        plt.title(title, fontproperties=myfont)
    plt.tight_layout()
    plt.show()


def plot_acc_earn(daily_earn_df, save_name=None, index_code=None):
    """略累计收益与相应的指数对比，index：沪深300对应000300.SH，中证500对应000905.SH"""
    from DataAPI.DataTools import get_index_data
    acc_earn_df = daily_earn_df.cumsum(axis=0)
    all_date = pd.to_datetime(acc_earn_df.index)
    all_tag = list(acc_earn_df.columns)

    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    lns = []
    for i in range(len(all_tag)):
        lns1 = ax.plot(all_date, acc_earn_df[all_tag[i]], '-', label=all_tag[i])
        lns += lns1
    if index_code is not None:
        st_date, ed_date = str(acc_earn_df.index[0]), str(acc_earn_df.index[-1])
        index_close = get_index_data(code=index_code, st_date=st_date, ed_date=ed_date)
        name_code_map = {"000300.SH": "沪深300", "000905.SH": "中证500", "000832.SH": "中证转债"}
        index_name = name_code_map[index_code]
        ax2 = ax.twinx()
        lns2 = ax2.plot(all_date, index_close, '-y', label='{}指数（右）'.format(index_name))
        lns += lns2
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, loc=0)
    plt.setp(ax.get_xticklabels(), rotation=45, horizontalalignment='right')
    plt.tight_layout()
    if save_name is not None:
        plt.savefig(save_name)
    plt.show()


def get_x_axis_pos(x):
    """坐标轴精简，输入的x为时序上的list，输出按半小时区分的位置信息"""
    x = np.array(x)
    x_pos = []
    x_label = ['09:30', '10:00', '10:30', '11:00', '13:00', '13:30', '14:00', '14:30', '15:00']
    if len(x[0]) == 8:
        for i in x_label:
            x_pos.append(len(x[x <= i + ':00']))
    elif len(x[0]) == 5:
        for i in x_label:
            x_pos.append(len(x[x <= i]))
    else:
        raise ValueError("x 内部格式为9:30或者9:30:00")
    if x_pos[-1] >= len(x):
        x_pos[-1] = len(x) - 1
    return x_pos, x_label


def multi_plot():
    fig = plt.figure(figsize=(16, 10))
    gs = gridspec.GridSpec(4, 2)
    ax1 = fig.add_subplot(gs[0:1, 0:1])


def plot_bar(ax, data_df, title_text='', decimal=0):
    # 画柱状图，index为柱状图的label，columns为柱状图的横坐标
    bar_width = 1 / (data_df.shape[1] + 2)
    x_list = list(data_df.index)
    label_list = list(data_df.columns)
    for j in range(data_df.shape[1]):
        y_select = data_df.iloc[:, j].values
        index = np.arange(len(y_select))
        ax.bar(index + bar_width * j, y_select, bar_width, label=label_list[j])

        for a, b in zip(range(data_df.shape[0]), y_select):
            text_b = int(b) if decimal == 0 else round(b, decimal)
            if b >= 0:
                plt.text(a + bar_width * j, b, text_b, ha='center', va='bottom', fontdict={'size': 6})
            else:
                plt.text(a + bar_width * j, b, text_b, ha='center', va='top', fontdict={'size': 6})
    plt.xticks(np.arange(len(x_list)) + bar_width * 0.5 * (len(label_list) - 1), x_list, fontproperties=myfont)
    ncols = data_df.shape[1] if data_df.shape[1] <= 4 else math.ceil(data_df.shape[1] / 2)
    plt.legend(ncol=ncols, loc='best', prop=myfont_legend)
    if title_text != '':
        plt.title(title_text, fontproperties=myfont)
    y_lim_min, y_lim_max = data_df.min().min(), data_df.max().max()
    if ncols == data_df.shape[1]:
        ax.set_ylim(-0.2 * y_lim_max + 1.2 * y_lim_min, 1.4 * y_lim_max - 0.4 * y_lim_min)
    else:
        ax.set_ylim(-0.2 * y_lim_max + 1.2 * y_lim_min, 1.6 * y_lim_max - 0.6 * y_lim_min)
    plt.tight_layout()
