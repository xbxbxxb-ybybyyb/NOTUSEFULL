# -*- coding: utf-8 -*-
import os
import datetime
import pandas as pd
import numpy as np
import warnings
from tquant.strategy.day_factor_backtest.backtest.utility import pprint, max_drawdown_ts, calc_cum_return_ts, \
    calc_year_date_num, calc_annualized_return, calc_percentile, \
    calc_hhi, calc_filter_correlation, find_er_ls_col
from tquant.strategy.day_factor_backtest.backtest.segment_test import segment_performance_measure

from tquant.strategy.day_factor_backtest.backtest.pdf_config import *
from tquant.strategy.day_factor_backtest.backtest.naming_config import *

version_number = '1.00'


def dataframe2str(df, col_type, axis, reformat_type):
    """get dataframe column, return string with format"""
    df = df if axis == 1 else df.T
    df_col = df.columns.tolist()
    df_row = df.index.tolist()
    df_str = [''] + df_row
    for col, ct in zip(df_col, col_type):
        data = [col] + num2str(df[col].values.tolist(), ct) if reformat_type == True else [col] + df[
            col].values.tolist()
        df_str = np.vstack([df_str, data])
    df_str = df_str.T.tolist() if axis == 1 else df_str.tolist()
    return df_str


def num2str(data, data_type):
    # take number and change format, return list of string
    round_num = int(data_type[-1])
    number_type = data_type[:-1]
    if isinstance(data, np.float):
        if number_type == 'pct':
            data = ('{:' + ('.%d' % round_num) + '%' + '}').format(data) if not pd.isnull(data) else 'NaN'
        elif number_type == 'dcm':
            data = ('{:' + ('.%d' % round_num) + 'f' + '}').format(data) if not pd.isnull(data) else 'NaN'
    else:
        if number_type == 'pct':
            data = [('{:' + ('.%d' % round_num) + '%' + '}').format(i) if not pd.isnull(i) else 'NaN' for i in data]
        elif number_type == 'dcm':
            data = [('{:' + ('.%d' % round_num) + 'f' + '}').format(i) if not pd.isnull(i) else 'NaN' for i in data]
    return data


def legend_helper():
    handles, labels = [], []
    for ax in plt.gcf().axes:
        for h, l in zip(*ax.get_legend_handles_labels()):
            handles.append(h)
            labels.append(l)
    return handles, labels


def generate_table(df, col_type, axis, reformat_type):
    df_str = dataframe2str(df, col_type, axis, reformat_type)
    df_str[0] = [i.encode('utf-8') for i in df_str[0]]
    t = Table(df_str)
    mytable = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                          ('BACKGROUND', (0, 0), (0, -1), colors.gray),
                          ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                          ('BOX', (0, 0), (-1, -1), 1, colors.black),
                          ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                          ('FONTNAME', (0, 0), (-1, -1), font_name),
                          ('FONTSIZE', (0, 0), (-1, -1), CANVAS_FONT_SIZE)])
    t.setStyle(mytable)
    return t


def generate_basicinfo_table(df, col_type, axis, reformat_type):
    df_str = dataframe2str(df, col_type, axis, reformat_type)
    df_str[0] = [i.encode('utf-8') for i in df_str[0]]
    t = Table(df_str)
    mytable = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                          ('BACKGROUND', (0, 1), (0, -1), colors.gray),
                          ('BACKGROUND', (2, 1), (2, -1), colors.gray),
                          ('BACKGROUND', (4, 1), (4, -1), colors.gray),
                          ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                          ('BOX', (0, 0), (-1, -1), 1, colors.black),
                          ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                          ('FONTNAME', (0, 0), (-1, -1), font_name),
                          ('FONTSIZE', (0, 0), (-1, -1), CANVAS_FONT_SIZE)])
    t.setStyle(mytable)
    return t


def generate_plot(df, plot_name, x_label, y_label,
                  plot_type='line', rot=None,
                  legend_outside=False, bottom=None,
                  show_stats=False, show_format='pct2',
                  width=img_width * inch, height=img_height * inch, fig_height = fig_height,
                  **kwargs):
    legend_on = True if min(df.shape) > 1 else False
    fig, ax = plt.subplots()
    df_plot = df.plot(kind=plot_type, figsize=(fig_width, fig_height),
                      legend=legend_on, fontsize=font_size_axis, rot=rot, colormap='RdYlGn', **kwargs)
    if legend_on:
        if legend_outside:
            plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=font_size_legend)
        else:
            plt.legend(loc=legend_loc, fontsize=font_size_legend)
    if bottom is not None:
        plt.subplots_adjust(bottom=bottom)
    if plot_type == 'line' and show_stats:
        if isinstance(df, pd.DataFrame):
            # if df.shape[1]>1:
            df_list = df.columns.tolist()
            add_str = ''
            for d in df_list:
                mean = df[d].mean()
                current_percentile = calc_percentile(df[d].dropna()).iloc[-1] * 100
                add_str = add_str + '\n%s - Avg:%s  Current Percentile:%.2f' % (
                    d, num2str(mean, show_format), current_percentile) + '%'
            plot_name = plot_name + add_str
        else:
            mean = df.mean()
            current_percentile = calc_percentile(df.dropna()).iloc[-1] * 100
            plot_name = plot_name + '\nAvg:%s  Current Percentile:%.2f' % (
                num2str(mean, show_format), current_percentile) + '%'
    df_plot.set_title(plot_name, fontsize=font_size_title, fontweight=font_title_weight)
    df_plot.set_xlabel(x_label, fontsize=font_size_axis)
    df_plot.set_ylabel(y_label, fontsize=font_size_axis)
    imgdata = BytesIO()
    df_plot.figure.savefig(imgdata, format=img_format, dpi=img_dpi)
    imgdata.seek(0)
    plt.close()
    return Image(imgdata, width=width, height=height)


def generate_plot_with_secondary(df1, plot_name, x_label, y_label1, y_label2, plot_type='line'):
    df1.index.name = ''
    # df2.index.name = ''
    fig, ax = plt.subplots()
    df1_plot = df1.plot(ax=ax, kind=plot_type, figsize=(fig_width, fig_height),
                        fontsize=font_size_axis, legend=False, color='orangered')
    df1_plot.set_title(plot_name, fontsize=font_size_title, fontweight=font_title_weight)

    df1_plot.set_ylabel(y_label1, fontsize=font_size_axis)
    ax.set_xlabel(x_label, fontsize=font_size_axis)
    # df2_plot = df2.plot(ax=ax, kind=plot_type, figsize=(fig_width, fig_height),
    # df2_plot = df2.plot(ax=ax, kind=plot_type, figsize=(fig_width, fig_height),
    #                     fontsize=font_size_axis, secondary_y=True, style='--', legend=False)
    # df2_plot.set_ylabel(y_label2, fontsize=font_size_axis)
    plt.legend(*legend_helper(), loc=legend_loc, fontsize=font_size_legend)
    imgdata = BytesIO()
    plt.savefig(imgdata, format=img_format, dpi=img_dpi)
    imgdata.seek(0)
    plt.close()
    return Image(imgdata, width=img_width * inch, height=img_height * inch)


def generate_ts_heatmap_by_month_plot(ps_raw, title_text, vmin, vmax, fmt='.2f', agg_method='mean',
                                      width=img_width * inch, height=img_height * inch, fig_height = fig_height):
    year_list = list(set(ps_raw.index.year))
    year_list.sort(reverse=False)
    month_ps = pd.DataFrame(index=[i for i in range(1, 13)])
    for year in year_list:
        sliced = ps_raw.loc[str(year)]
        if agg_method == 'mean':
            month_ps[year] = sliced.groupby(sliced.index.month).mean()
        elif agg_method == 'sum':
            month_ps[year] = sliced.groupby(sliced.index.month).sum()
        else:
            raise NotImplementedError
    sns.set_style('white')
    sns.set(font_scale=1.6)
    cmap = sns.diverging_palette(220, 10, as_cmap=True)
    month_ps = month_ps.rename(index=month_mapper)
    month_ps.index.name = title_text
    month_ps.columns.name = ''
    plt.figure(figsize=(fig_width, fig_height))
    sns.heatmap(month_ps.T, vmin=vmin, vmax=vmax, linewidths=.5, cmap='RdYlGn', annot=True, fmt=fmt)
    imgdata = BytesIO()
    plt.subplots_adjust(right=1, top=1)
    plt.savefig(imgdata, format=img_format, dpi=img_dpi)
    imgdata.seek(0)
    plt.close()
    plt.style.use('ggplot')
    return Image(imgdata, width=width, height=height)


def generate_ts_by_type_plot(ts, by='Month', x_label=None, ann_scale=False, vmin=-0.2, vmax=0.2, fmt='.2f'):
    if by == 'Month':
        grp_index = ts.index.month
        scale_num = 21
    elif by == 'Year':
        grp_index = ts.index.year
        scale_num = 252
    else:
        raise AssertionError
    grp_obj = ts.groupby(grp_index)
    grp_num = grp_obj.mean()
    if ann_scale:
        grp_num = grp_num * scale_num
    grp_num = grp_num.rename(index=month_mapper) if by == 'Month' else grp_num
    grp_num.index.name = x_label + ' by ' + by
    grp_num.columns.name = ''
    grp_num = grp_num.fillna(0)
    sns.set_style('white')
    sns.set(font_scale=1.6)
    cmap = sns.diverging_palette(220, 10, as_cmap=True)
    plt.figure(figsize=(fig_width, fig_height * 1.8))
    sns.heatmap(grp_num.T, vmin=vmin, vmax=vmax, linewidths=.5, cmap='RdYlGn', annot=True, fmt=fmt)
    plt.yticks(rotation=0)
    plt.tight_layout()
    imgdata = BytesIO()
    plt.savefig(imgdata, format=img_format, dpi=img_dpi)
    imgdata.seek(0)
    plt.close()
    plt.style.use('ggplot')
    return Image(imgdata, width=img_width * inch, height=img_height * inch * 1.8)


def generate_bar_line_plot(df, title, bar_column, line_column, show_stats=False, show_format='pct2'):
    plt.figure(figsize=(fig_width, fig_height))
    plt.subplot(211, axisbg='#FFDAB9')
    plt.bar(np.arange(len(df)), df[bar_column], color='orangered')
    if show_stats:
        #计算均值及当前值在近20日的排名
        df_avg, df_pct = df[bar_column].mean(), calc_percentile(df[bar_column].dropna()).iloc[-1]
        title = title + ' - Avg: %s - Current Percentile(Rolling 20 Days): %s' % (num2str(df_avg, show_format), num2str(df_pct, 'pct2'))
    plt.title(title, fontsize=font_size_title, fontweight=font_title_weight)
    plt.xticks([])
    plt.xticks(fontsize=font_size_axis)
    plt.yticks(fontsize=font_size_axis)
    plt.subplot(212,axisbg='#FFDAB9')
    plt.plot(df[line_column], color='orangered')
    plt.title(line_column, fontsize=font_size_title, fontweight=font_title_weight)
    plt.xlabel('')
    plt.xticks(fontsize=font_size_axis)
    plt.yticks(fontsize=font_size_axis)
    imgdata = BytesIO()
    plt.savefig(imgdata, format=img_format, dpi=img_dpi)
    imgdata.seek(0)
    plt.close()
    return Image(imgdata, width=img_width * inch, height=img_height * inch)


def generate_line_subplot(df):
    df.index.name = ''
    height_scaler = min(max_fig_height, fig_height * len(df.columns) * 0.75) / fig_height
    df.plot(subplots=True, figsize=(fig_width, fig_height * height_scaler), fontsize=font_size_axis)
    [ax.legend(loc=legend_loc, fontsize=font_size_legend) for ax in plt.gcf().axes]
    plt.subplots_adjust(bottom=0.05, top=0.99, wspace=0, hspace=0.1)
    imgdata = BytesIO()
    plt.savefig(imgdata, format=img_format, dpi=img_dpi)
    imgdata.seek(0)
    plt.close()
    return Image(imgdata, width=img_width * inch, height=img_height * inch * height_scaler)


def generate_whisker_plot(df, title='Style Correlation Distribution', rot=0, bottom=None, ylim=None, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        df.index.name = ''
        df.plot(kind='box', figsize=(fig_width, fig_height), rot=rot, fontsize=font_size_axis, **kwargs)
        if ylim is not None:
            plt.ylim(ylim)
        plt.title(title, fontsize=font_size_title, fontweight=font_title_weight)
        if bottom is not None:
            plt.subplots_adjust(bottom=bottom)
        imgdata = BytesIO()
        plt.savefig(imgdata, format=img_format, dpi=img_dpi)
        imgdata.seek(0)
        plt.close()
    return Image(imgdata, width=img_width * inch, height=img_height * inch)


def generate_performance_report(df):
    col_name = df.columns
    idx_name = df.index.tolist()

    df.index = idx_name
    plt.figure(figsize=(fig_width, fig_height * 2))
    for i in range(len(col_name)):
        plt.subplot(2, 3, i + 1,axisbg='#FFDAB9')
        df.iloc[:, i].plot(kind='bar', fontsize=font_size_axis)
        plt.title(col_name[i], fontsize=font_size_title, fontweight=font_title_weight)
    plt.subplots_adjust(hspace=0.25)
    imgdata = BytesIO()
    plt.savefig(imgdata, format=img_format, dpi=img_dpi)
    imgdata.seek(0)
    plt.close()
    return Image(imgdata, width=img_width * inch, height=img_height * inch * 2)


def generate_segment_ret_year_plot(df, col_name='Return(Ann.)'):
    df_ret = df[col_name]
    year_list = list(set(df_ret.index.get_level_values(0)))
    year_list.sort(reverse=True)
    year_num = len(year_list)
    plt_rows = int(np.ceil(year_num / 2))
    height_scaler = min(max_fig_height, fig_height * plt_rows * 0.75) / fig_height
    er_col = [i for i in df_ret.loc[year_list[-1]].index.tolist() if i.find('-Index') > 0][0]
    plt.figure(figsize=(fig_width, fig_height * height_scaler))
    for i in range(year_num):
        plt.subplot(plt_rows, 2, i + 1,axisbg='#FFDAB9')
        sliced = df.loc[year_list[i]]
        sliced[col_name].plot(kind='bar', fontsize=font_size_axis)
        title_name = (str(year_list[i]) + ' - ' + 'RET: %.2f%%' % (sliced.loc[er_col]['Return(Ann.)'] * 100) + ', ' +
                      'Sharpe: %.2f' % (sliced.loc[er_col]['Sharpe']) + ', '
                                                                        'MDD: %.2f%%' % (
                              sliced.loc[er_col]['MDD'] * 100))
        plt.title(title_name, fontsize=font_size_title, fontweight=font_title_weight)
    plt.tight_layout()
    imgdata = BytesIO()
    plt.savefig(imgdata, format=img_format, dpi=img_dpi)
    imgdata.seek(0)
    plt.close()
    return Image(imgdata, width=img_width * inch, height=img_height * inch * height_scaler)


def generate_segment_ret_plot(seg_dict, interest_type):
    fig, ax = plt.subplots()
    seg_dict = {k: v for k, v in seg_dict.items() if v is not None}
    if np.any(['With Ind After Cost' in seg_dict]):
        title_key = 'With Ind After Cost'
    elif np.any(['With Ind Before Cost' in seg_dict]):
        title_key = 'With Ind Before Cost'
    elif np.any(['No Ind After Cost' in seg_dict]):
        title_key = 'No Ind After Cost'
    else:
        title_key = 'No Ind Before Cost'
    for k, v in seg_dict.items():
        v.index.name = ''
        if k == title_key:
            segment_helper(ax, v, title=True, title_text=k, interest_type=interest_type)
        else:
            segment_helper(ax, v, title=False, title_text=k, interest_type=interest_type)
    imgdata = BytesIO()
    plt.savefig(imgdata, format=img_format, dpi=img_dpi)
    imgdata.seek(0)
    plt.close()
    return Image(imgdata, width=img_width * inch, height=img_height * inch * 1.4)

def segment_helper(ax, easy_seg_return, title=False, title_text='', interest_type='SIMPLE'):
    easy_seg_return.dropna(inplace=True)
    # easy_seg_return = easy_seg_return.dropna()
    # easy_seg_return.is_copy = False  # False不提示正在修改复制的数据
    max_q = easy_seg_return.iloc[:, :10].mean().idxmax()
    easy_seg_return.loc[:, max_q + '-index'] = easy_seg_return[max_q] - easy_seg_return['Index']
    easy_seg_return_cum = calc_cum_return_ts(easy_seg_return, interest_type)  # 累计收益率，累乘
    easy_seg_return_cum.loc[:, 'MDD_L-index'] = max_drawdown_ts(easy_seg_return_cum[max_q + '-index'],
                                                                interest_type=interest_type)
    mdd_l_index = easy_seg_return_cum['MDD_L-index'].min()
    _ = easy_seg_return_cum[max_q + '-index']
    _.name = 'Excess Return - ' + title_text
    plt1 = _.plot(ax=ax, figsize=(fig_width, fig_height*1.3), fontsize=font_size_axis, legend=False)
    _ = easy_seg_return_cum['MDD_L-index']
    _.name = 'MDD - ' + title_text
    plt2 = _.plot(ax=ax, figsize=(fig_width, fig_height*1.3), secondary_y=True,
                  fontsize=font_size_axis, style='--', legend=False)
    plt.legend(*legend_helper(), loc=legend_loc, fontsize=font_size_legend)
    plt.ylim([0.05, mdd_l_index-0.1])

    if title:
        ann_ret = calc_annualized_return(easy_seg_return.loc[:, max_q + '-index'], interest_type)
        plt1.set_title(title_text + '\n' +
                       'Excess CumRet: %0.2f' % (ann_ret * 100) + '% (LHS), ' +
                       'Max Drawdown: ' + str(np.round(mdd_l_index * 100, 2)) + '% (RHS)',
                       fontsize=font_size_title, fontweight=font_title_weight)
        plt1.set_ylabel('Excess CumRet', fontsize=font_size_axis)
        plt1.set_xlabel('')
        plt2.set_ylabel('Max Drawdown', fontsize=font_size_axis)
        plt2.set_xlabel('')
    plt2.invert_yaxis()


def generate_stacked_bar_plot(df, x_label, y_label, freq='m', title=None, rot=None,
                              legend_outside=False, bottom=None):
    date_num = len(df)
    legend_on = True if min(df.shape) > 1 else False
    fig, ax = plt.subplots()
    if freq is None:
        if date_num >= 1000:
            freq = 'q'
        if date_num >= 50:
            freq = 'm'
        else:
            freq = 'd'
    title = 'By ' + freq if title is None else title + ' by ' + freq
    df_mean = df.resample(freq).mean()
    df_mean.plot(kind='bar', stacked=True, figsize=(fig_width, fig_height),
                 legend=legend_on, fontsize=font_size_axis, rot=rot, title=title, color='orangered')
    if legend_on:
        if legend_outside:
            plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=font_size_legend)
        else:
            plt.legend(loc=legend_loc, fontsize=font_size_legend)
    imgdata = BytesIO()
    plt.savefig(imgdata, format=img_format, dpi=img_dpi)
    imgdata.seek(0)
    plt.close()
    return Image(imgdata, width=img_width * inch, height=img_height * inch)


def generate_pdf(pickle_name, corr_information=None, rolling_window=20,factor_data_num=0):
    pprint('Retrieving basic numbers from pickle')
    output_dict = pd.read_pickle(pickle_name)
    sum_df = output_dict['summary_info']
    factor_stat = output_dict['distribution']
    seg_ret = output_dict['seg_return']
    seg_ret_stat = output_dict['seg_return_stat']
    seg_return_stat_year = output_dict['seg_return_stat_year']
    factor_auto_correlation = output_dict['factor_auto_correlation']
    ic_ts_combined = output_dict['ic_ts_combined']
    ic_stats = output_dict['ic_stats']
    factor_ts = output_dict['stock_count']
    ic_decay = output_dict['ic_decay']
    ic_duration = output_dict['ic_duration']
    market_rank = output_dict['market_rank']

    pprint('Calculate immediate data')
    factor_name = sum_df.loc['Factor Name'].values[0]
    easy_test = sum_df['Settings2'].values[0]
    ic_type = sum_df['Settings2'].values[1]
    compare_style = sum_df['Settings2'].values[2]
    interest_type = sum_df['Settings2'].values[3]
    if ic_type == 'score_weighted':
        ic_type = 'IC Score Weighted'
    elif ic_type == 'original':
        if easy_test:
            ic_type = 'IC Original'
        else:
            ic_type = 'IC Neutralized'

    try:
        seg_return_after_cost_stat = output_dict['seg_return_after_cost_stat']
        seg_return_after_cost = output_dict['seg_return_after_cost']
        t_cost_flag = True
    except:
        t_cost_flag = False
    try:
        seg_return_each_industry = output_dict['seg_return_each_industry']
        seg_return_each_industry_stat = output_dict['seg_return_each_industry_stat']
        industry_concentration = output_dict['industry_concentration']
        seg_return_ew = output_dict['seg_return_ew']

        seg_by_industry_flag = True
        if t_cost_flag:
            segret_by_ind_after_cost = output_dict['segret_by_ind_after_cost']
            segret_by_ind_stat_after_cost = output_dict['segret_by_ind_stat_after_cost']
            seg_return_ew_after_cost = output_dict['seg_return_ew_after_cost']
    except:
        seg_by_industry_flag = False
    if not easy_test:
        pass
        # bie ȥ�� regression_analysis
        # factor_TIC = output_dict['regression_output']
        # factor_TIC_test = output_dict['regression_stats']
        # bie barra factor delay online
        # style_corr_pd = output_dict['style_corr']
        # ic_style_corr = output_dict['ic_style_corr']
        # bie barra factor delay online
        # ic_contextual_stats = output_dict['ic_contextual_stats']

    try:
        seg_return_fac = output_dict['seg_return_fac']
        compare_style_flag = True
        if t_cost_flag:
            seg_return_after_cost_fac = output_dict['seg_return_after_cost_fac']
    except:
        compare_style_flag = False

    sample_bin_ret_mean = output_dict['sample_bin_ret_mean']
    sample_bins_ret_stat = output_dict['sample_bins_ret_stat']
    sample_bins_ret_diff2ret = output_dict['sample_bins_ret_diff2ret']
    sample_std2ret = output_dict['sample_std2ret']
    Calmar_half_year = output_dict['Calmar_half_year']

    ###############################################################################

    if not easy_test:
        pass
        # bie ȥ�� regression_analysis
        # IC_ts = pd.DataFrame(factor_TIC['IC'])  # neutralized IC series
        # IC_ts['Avg %d Period' % rolling_window] = factor_TIC['IC'].rolling(rolling_window).mean()
        # Tstat_ts = pd.DataFrame(factor_TIC['T-stat'])
        # Tstat_ts['Avg %d Period' % rolling_window] = factor_TIC['T-stat'].rolling(rolling_window).mean()
        # bie barra factor delay online
        # style_corr_roll = style_corr_pd.rolling(rolling_window).mean()

    factor_stat.columns = ['Basic Statistics']
    factor_auto_correlation_roll = factor_auto_correlation.rolling(rolling_window).mean()

    seg_num = int(max([float(item.replace('Q', '')) for item in seg_ret.columns if '-' not in item and 'Q' in item]))
    seg_return_stat_year.index.names = ['dt', '']
    seg_cumret = calc_cum_return_ts(seg_ret, interest_type=interest_type)
    seg_ret_year = seg_return_stat_year['Return(Ann.)'].unstack()
    seg_er_col = [col for col in seg_ret_year.columns.tolist() if col.find('-') > 0]
    assert len(seg_er_col) == 1

    seg_col_name_order = ['Q' + str(i + 1) for i in range(seg_num)] + seg_er_col + ['Index']
    seg_ret_year = seg_ret_year[seg_col_name_order]
    seg_sharpe_year = (seg_return_stat_year['Sharpe'].unstack())[seg_col_name_order]
    seg_return_by_year_list = []

    for year in seg_ret.index.year.unique():
        _ = calc_cum_return_ts(seg_ret[seg_er_col[0]].loc[str(year)], interest_type=interest_type)
        _.name = year
        _.index = range(1, len(_) + 1)
        seg_return_by_year_list.append(_)
    seg_return_by_year = pd.concat(seg_return_by_year_list, axis=1)

    if seg_by_industry_flag:
        ind_seg_er_col = [col for col in seg_return_each_industry.columns.tolist() if col.find('-') > 0]
        assert len(ind_seg_er_col) == 1
        if t_cost_flag:
            excess_return_industry_sliced = segret_by_ind_stat_after_cost.xs(ind_seg_er_col[0], level=1)
        else:
            excess_return_industry_sliced = seg_return_each_industry_stat.xs(ind_seg_er_col[0], level=1)#每个行业的超额收益Q-Index这一层

    pprint('Generating tables')
    tr_list = ['Return(Ann.)', 'Vol(Ann.)', 'Sharpe', 'MDD', 'HitRate']
    er_list = ['Excess Return', 'Tracking Error', 'IR', 'MDD_ER', 'HitRate_ER']
    col_type_tr_list = ['pct2', 'pct2', 'dcm2', 'pct2', 'pct2']
    col_type = ['str1'] * len(sum_df)
    t_sum = generate_table(sum_df, col_type, axis=0, reformat_type=False)
    col_type = ['dcm2', 'dcm2', 'pct2', 'dcm3', 'dcm3', 'dcm2', 'dcm2', 'dcm2']
    t_factor_stat = generate_table(factor_stat.T, col_type, axis=1, reformat_type=True)
    col_type = col_type_tr_list * 2
    t_seg_ret = generate_table(seg_ret_stat, col_type, axis=1, reformat_type=True)
    if t_cost_flag:
        col_type = col_type_tr_list * 2
        t_seg_return_after_cost = generate_table(seg_return_after_cost_stat, col_type, axis=1, reformat_type=True)

    col_type = ['dcm3'] * ic_stats.shape[1]
    t_ic_stats = generate_table(ic_stats, col_type, axis=0, reformat_type=True)

    if easy_test == False:
        col_type = ['dcm3', 'pct2', 'dcm3', 'dcm3', 'dcm3', 'dcm3', 'dcm3', 'dcm3', 'pct2', 'pct2', 'dcm3', 'pct2']
    # bie ȥ�� regression_analysis
    # t_factor_TIC_Test = generate_table(factor_TIC_test, col_type, axis=0, reformat_type=True)

    if seg_by_industry_flag:
        t_excess_return_industry_sliced = generate_table(excess_return_industry_sliced[tr_list], col_type_tr_list,
                                                         axis=1, reformat_type=True)

    ###################### added by Jiaping You, 20191129  ########################
    col_type = ['dcm2', 'dcm2']
    t_sample_bins_ret_stat = generate_table(sample_bins_ret_stat, col_type, axis=0, reformat_type=True)
    ###############################################################################

    plt.ioff()
    pprint('Generating graphs')
    from pandas.plotting import register_matplotlib_converters
    register_matplotlib_converters()
    show_percentile = 'IC Original'
    ic_ts_combined_show = ic_ts_combined[[i for i in ic_ts_combined.columns if i[0] != 'Q']]
    # if not easy_test:
    #    ic_ts_combined_show = pd.concat([ic_ts_combined_show,ic_combined_ts[['IC Score Weighted']]],axis=1)
    ic_ts_combined_roll = ic_ts_combined_show.rolling(rolling_window,min_periods=0).apply(np.nanmean)
    # ic_ts_combined_cumsum = ic_ts_combined_show.cumsum()
    ic_percentile = calc_percentile(ic_ts_combined_roll).dropna().iloc[-1]
    ic_orig_percentile = ic_percentile.loc[show_percentile]

    col_name_roll = '%d 日平均' % (rolling_window)
    market_rank_df = pd.concat([market_rank, market_rank.rolling(rolling_window).mean()], axis=1)
    market_rank_df.columns = ['market_rank', col_name_roll]
    g_market_rank = generate_bar_line_plot(df=market_rank_df, title='Top Segment Total Return Market Rank',
                                           bar_column='market_rank',
                                           line_column=col_name_roll, show_stats=True, show_format='pct2')
    h_ic_ts_combined_roll = Paragraph("因子与收益IC({}日平均)".format(rolling_window), pdf_styles['STSONG'])
    g_ic_ts_combined_roll = generate_plot_with_secondary(ic_ts_combined_roll,
                                                         'IC (Rolling %d day Average) \nCurrent %s Percentile %.2f' % (
                                                             rolling_window, show_percentile, ic_orig_percentile),
                                                         '', 'IC', 'Bucket IC', plot_type='line')
    g_seg_cumret = generate_plot(seg_cumret, plot_name='Segment Return', x_label='', y_label='Cummulative Return')
    g_ic_decay = generate_plot(ic_decay, plot_name='IC Decay', x_label='Days after factor', y_label='IC')
    g_ic_duration = generate_plot(ic_duration, plot_name='IC Duration', x_label='Days after factor',
                                  y_label='IC', plot_type='bar', rot=0)

    auto_corr_mean = factor_auto_correlation.mean().values[0] * 100
    g_factor_auto_correlation_rolling = generate_plot(factor_auto_correlation_roll,
                                                      plot_name='Factor Auto Correlation \n' + \
                                                                '(avg correlation: %0.2f' % auto_corr_mean + '%)',
                                                      x_label='', y_label='Correlation')
    # 年化收益
    g_return_by_year = generate_plot(seg_return_by_year, plot_name=seg_er_col[0] + ' Return by Year',
                                     x_label='Day in Year',
                                     y_label='Cummulative Return')
    # g_seg_ret_year = generate_plot(seg_ret_year, plot_name='Total Return', x_label='', y_label='Return (Ann.)',
    #                               plot_type='bar', legend_outside=True, rot=45)
    h_seg_sharpe_year = Paragraph("分层测试年化Sharpe统计图", pdf_styles['STSONG'] )
    g_seg_sharpe_year = generate_plot(seg_sharpe_year, plot_name='Sharpe', x_label='', y_label='Sharpe',
                                      plot_type='bar', legend_outside=True, rot=45)
    # g_ic_ts_combined_cumsum = generate_plot(ic_ts_combined_cumsum, plot_name='Cumulative IC Comparison', x_label='', y_label='Cum IC')
    g_factor_ts = generate_plot(factor_ts, plot_name='Stock Count with Factor \n' + \
                                                     '(avg stock count: %d)' % (factor_ts.mean().values[0]),
                                x_label='', y_label='Number of Stocks')

    import collections
    show_dict = collections.OrderedDict()
    if seg_by_industry_flag:  # industry segment activated
        if t_cost_flag:
            show_dict['With Ind After Cost'] = seg_return_after_cost
            show_dict['With Ind Before Cost'] = seg_ret
            show_dict['No Ind After Cost'] = seg_return_ew_after_cost
            show_dict['No Ind Before Cost'] = seg_return_ew

            # show_dict = {'With Ind After Cost': seg_return_after_cost,
            #              'With Ind Before Cost': seg_ret,
            #              'No Ind After Cost': seg_return_ew_after_cost,
            #              'No Ind Before Cost': seg_return_ew}
        else:
            show_dict['With Ind Before Cost'] = seg_ret
            show_dict['No Ind Before Cost'] = seg_return_ew
            # show_dict = {'With Ind Before Cost': seg_ret,
            #              'No Ind Before Cost': seg_return_ew}

        # 行业细分的IC值，从easy_test中抽出
        h_ic_by_industry = Paragraph('行业与收益的IC', pdf_styles['STSONG'])
        ic_by_industry = output_dict['ic_by_industry']
        g_ic_ind_by_month = generate_ts_by_type_plot(ic_by_industry, by='Month', x_label=ic_type, fmt='.3f')
        g_ic_ind_by_year = generate_ts_by_type_plot(ic_by_industry, by='Year', x_label=ic_type, fmt='.3f')
    else:
        if t_cost_flag:
            show_dict['No Ind After Cost'] = seg_return_after_cost
            show_dict['No Ind Before Cost'] = seg_ret
            # show_dict = {'No Ind After Cost': seg_return_after_cost,
            #              'No Ind Before Cost': seg_ret}
        else:
            show_dict['No Ind Before Cost'] = seg_ret
            # show_dict = {'No Ind Before Cost': seg_ret}

    g_seg_return_new = generate_segment_ret_plot(show_dict, interest_type)
    # bie ȥ�� regression_analysis
    g_ic_by_month = generate_ts_heatmap_by_month_plot(ic_ts_combined[ic_type], title_text=ic_type + '  by Month',
                                                      vmax=0.2, vmin=-0.2, fmt='.2f')
    """seg_use"""
    # check which seg_return to use
    show_dict_stat = {i: segment_performance_measure(show_dict[i], interest_type) for i in show_dict}
    seg_ret_sum_stats = pd.concat([show_dict_stat[i].iloc[-1] for i in show_dict_stat], axis=1).T
    seg_ret_sum_stats.index = list(show_dict.keys())
    seg_ret_sum_stats = seg_ret_sum_stats[tr_list]

    seg_ret_use = seg_return_after_cost if t_cost_flag else seg_ret
    # seg_ret_stat_use = seg_return_after_cost_stat if t_cost_flag else seg_ret_stat
    # excess_ret_stat_use = pd.DataFrame(seg_ret_stat_use.iloc[-1])
    t_excess_ret_stat_use = generate_table(seg_ret_sum_stats, col_type_tr_list, axis=1, reformat_type=True)
    er_col_use, l_col_use, s_col_use = find_er_ls_col(seg_ret_use)
    er_use = seg_ret_use[er_col_use]  # 超额收益
    g_er_by_month = generate_ts_heatmap_by_month_plot(er_use * 100,
                                                      title_text='{} Excess Return(%) by Month'.format(er_col_use),
                                                      vmin=-10, vmax=10, fmt='.2f', agg_method='sum', fig_height = fig_height*1.5
                                                      )  #
    seg_ret_use['Avg %d Period' % rolling_window] = seg_ret_use[er_col_use].rolling(
        rolling_window).mean()  # 滚动平均，seg_er_col最大收益层的超额收益
    h_seg_ret_bar = Paragraph("分层测试最佳组合超额收益({}日平均)".format(rolling_window), pdf_styles['STSONG'])
    g_seg_ret_bar = generate_bar_line_plot(df=seg_ret_use, title='{} Excess Return'.format(er_col_use),
                                           bar_column=er_col_use,
                                           line_column='Avg %d Period' % (rolling_window), show_stats=True,
                                           show_format='pct2')

    # generate_stacked_bar_plot(df,x_label, y_label,freq='m',title=None,rot=None)

    if compare_style_flag:
        if factor_data_num > 250:
            # 比较因子分层结果和风格因子分层结果（默认的风格因子为Size）
            seg_ret_use_fac = seg_return_after_cost_fac if t_cost_flag else seg_return_fac  # seg_return_fac,每日分层收益，seg_return_after_cost_fac，每日去除成本后的分层收益
            er_col_use_fac, l_col_use_fac, s_col_use_fac = find_er_ls_col(seg_ret_use_fac)  # Q10-Index， Q1，Q10

            # ls_ret_use = seg_ret_use[l_col_use] - seg_ret_use[s_col_use]
            ls_ret_use_fac = seg_ret_use_fac[l_col_use_fac] - seg_ret_use_fac[s_col_use_fac]  # ls，多空组合，第一层减去最后一层
            # er_corr = seg_ret_use[er_col_use].rolling(rolling_window).corr(seg_ret_use_fac[er_col_use_fac])
            # ls_corr = ls_ret_use.rolling(rolling_window).corr(ls_ret_use_fac)
            date_year = 240
            corr_remove_mid_pct = 0.4
            corr_win = rolling_window if len(ls_ret_use_fac) < date_year else date_year
            er_ls_corr = seg_ret_use[er_col_use].rolling(corr_win).corr(
                ls_ret_use_fac)  # er_col_use和er_col_use_fac相同，每240天的序列，计算一个pearson相关系数，比如0:240计算第一个相关性，1:241计算第二个相关性
            all_history_corr = seg_ret_use[er_col_use].corr(ls_ret_use_fac)  # 最大层超额与多空的相关关系
            ret_remove_mid = ls_ret_use_fac[(ls_ret_use_fac < ls_ret_use_fac.quantile(corr_remove_mid_pct / 2))
                                            | (ls_ret_use_fac > ls_ret_use_fac.quantile(1 - corr_remove_mid_pct / 2))]
            all_history_remove_mid_corr = seg_ret_use[er_col_use].corr(ret_remove_mid)
            corr_use = pd.concat([ls_ret_use_fac, seg_ret_use[er_col_use]], axis=1).dropna()
            er_ls_corr_remove_middle = calc_filter_correlation(corr_use, corr_win, filter_x_middle=corr_remove_mid_pct,
                                                               min_pct=0.8)  # 去除两端极值后，计算相关性
            corr_df = pd.concat([er_ls_corr, er_ls_corr_remove_middle], axis=1)
            corr_df.columns = ['all_sample', 'remove_middle %s' % (num2str(corr_remove_mid_pct, 'pct0'))]
            ls_corr_name = '相关性 %s ( %d 天窗口)' % (compare_style, corr_win)
            add_avg_str = '\n 历史相关性: %s: %s   %s: %s' % (
                corr_df.columns[0], num2str(all_history_corr, 'pct2'),
                corr_df.columns[1], num2str(all_history_remove_mid_corr, 'pct2'))
            plt_name = 'Correlation with %s (Rolling %d Days) \n (Factor Excess Return vs Style Long Short Return)%s' % (
                compare_style, corr_win, add_avg_str)
            g_ls_corr_show = generate_plot(corr_df, plot_name=plt_name, x_label='', y_label='Correlation',
                                           show_stats=True, show_format='pct2', fig_height = fig_height*1.1)
        else:
            pass

    """
        ls_corr_name = 'Correlation with %s (Long Short Return: Rolling %d Days)'%(compare_style,rolling_window)
        er_corr_avg,ls_corr_avg = seg_ret_use[er_col_use].corr(seg_ret_use_fac[er_col_use_fac]),ls_ret_use.corr(ls_ret_use_fac)
        g_ls_corr_show = generate_plot_with_secondary(ls_corr_show[col_name[:2]]*100, ls_corr_show[col_name[2]], 
                                                      plot_name=ls_corr_name + '\nAvg Corr:%.2f'%(ls_corr_avg*100)+'%',
                                                      x_label='', y_label1='LS Ret (Daily%)', y_label2='Correlation', plot_type='line')

        er_corr_name = 'Correlation with %s (Excess Return: Rolling %d Days)'%(compare_style,rolling_window)
        g_er_corr_show = generate_plot_with_secondary(er_corr_show[col_name[:2]]*100, er_corr_show[col_name[2]], 
                                                      plot_name=er_corr_name + '\nAvg Corr:%.2f'%(er_corr_avg*100)+'%', 
                                                      x_label='', y_label1='Excess Ret(Daily%)', y_label2='Correlation', plot_type='line')
        """
    """ic_use"""
    # bie ȥ�� regression_analysis
    # ic_use = ic_ts_combined[[ic_type]]
    # ic_use['Avg %d Period' % rolling_window] = ic_use[ic_type].rolling(rolling_window).mean()
    # g_ic_bar = generate_bar_line_plot(df=ic_use, title=ic_type, bar_column=ic_type,
    #                                   line_column='Avg %d Period' % rolling_window, show_stats=True, show_format='dcm3')



    if not easy_test:
        pass
        # bie ȥ�� regression_analysis
        # g_Tstat = generate_bar_line_plot(df=Tstat_ts, title='T-Statistics', bar_column='T-stat',
        #                                  line_column='Avg %d Period' % rolling_window, show_stats=True,
        #                                  show_format='dcm2')
        # bie ȥ�� regression_analysis
        # ic_neu = ic_ts_combined[['IC Neutralized']]
        # ic_neu['Avg %d Period' % rolling_window] = ic_ts_combined['IC Neutralized'].rolling(rolling_window).mean()
        # g_ic = generate_bar_line_plot(df=ic_neu, title='IC', bar_column='IC Neutralized',
        #                               line_column='Avg %d Period' % rolling_window,
        #                               show_stats=True, show_format='dcm3')
        # bie barra factor delay online
        # g_style_corr = generate_line_subplot(style_corr_roll)
        # g_style_distribution = generate_whisker_plot(style_corr_pd)
        # g_ic_style_corr = generate_line_subplot(ic_style_corr)

        # new
        # bie barra factor delay online
        # ic_context_mean = ic_contextual_stats.loc['IC Mean'].T
        # bie barra factor delay online
        # g_ic_context_mean = generate_plot(ic_context_mean, plot_name='IC_Original Contextual Mean',
        #                                   x_label='Context,Level', y_label='IC Avg', plot_type='bar', bottom=0.5)

    if seg_by_industry_flag:
        seg_ret_industry_use = segret_by_ind_after_cost if t_cost_flag else seg_return_each_industry
        seg_by_industry = seg_ret_industry_use[ind_seg_er_col[0]].unstack() * 100
        g_seg_ind_by_month = generate_ts_by_type_plot(seg_by_industry, by='Month', x_label='Excess Return(%)',
                                                      ann_scale=True, vmin=-10, vmax=10)
        g_seg_ind_by_year = generate_ts_by_type_plot(seg_by_industry, by='Year', x_label='Excess Return(%)',
                                                     ann_scale=True, vmin=-50, vmax=50)
        if industry_concentration.dropna().empty:
            g_industry_concentration = None
            pass
        else:
            g_industry_concentration = generate_plot(industry_concentration,
                                                     plot_name='Excess Return - Industry Concentration',
                                                     x_label='', y_label='Concentration', plot_type='line',
                                                     show_stats=True)  # , rot=45)

    ##############################################

    g_sample_bin_ret_mean = generate_plot(sample_bin_ret_mean, plot_name='Sampled mean excess return', x_label='Sample',
                                          y_label='Mean Return ', plot_type='bar', rot=45)
    # bie
    if factor_data_num > 250:
        g_sample_bins_ret_diff2ret = generate_plot(sample_bins_ret_diff2ret,
                                                       plot_name='Rolling (Max ret - Min ret) / Mean ret', x_label='',
                                                       y_label='', rot=45)
        g_sample_std2ret = generate_plot(sample_std2ret, plot_name='Rolling Variance ratio of sampled ret (STD/Mean)',
                                         x_label='', y_label='', rot=45)
    h_Calmar_half_year = Paragraph("Calmar比率图(半年)", pdf_styles['STSONG'])
    g_Calmar_half_year = generate_plot(Calmar_half_year, plot_name='Calmar ratio in half year', x_label='',
                                       y_label='Calmar Ratio', plot_type='bar', rot=30, bottom=0.2)

    ###############################################################################

    plt.ioff()

    pprint('Generating headers')
    add_t_cost = '(费前)' if t_cost_flag else '(费后)'
    add_seg_by_ind = ' -行业中性化' if seg_by_industry_flag else ''

    h_seg_by_industry = Paragraph('行业超额收益率统计图' + add_t_cost, pdf_styles['STSONG'])
    # h_corr_info = Paragraph(corr_information, heading_size)
    h_sum = Paragraph('回测报告信息', pdf_styles['STSONG'])
    h_factor_stat = Paragraph('因子分布指标与IC统计表', pdf_styles['STSONG'])
    h_seg_ret = Paragraph('分层收益率统计表', pdf_styles['STSONG'])
    h_seg_ret_table = Paragraph('分层测试指标统计表(费前)%s' % (add_seg_by_ind), pdf_styles['STSONG'])
    h_excess_ret_stat_use = Paragraph('分层测试最佳组合收益统计', pdf_styles['STSONG'])
    h_seg_ret_table_after_cost = Paragraph('分层测试指标统计表(费后)%s' % (add_seg_by_ind), pdf_styles['STSONG'])

    h_return_by_year = Paragraph('年度超额收益图', pdf_styles['STSONG'])
    h_seg_year = Paragraph('年化收益图', pdf_styles['STSONG'])
    h_seg_cumret = Paragraph('分层测试累计收益（费前）', pdf_styles['STSONG'])
    h_ic_decay = Paragraph('因子IC随时间的衰减图', pdf_styles['STSONG'])
    h_factor_auto_correlation_rolling = Paragraph('因子自相关', pdf_styles['STSONG'])
    h_ic_stats = Paragraph('因子IC指标统计图', pdf_styles['STSONG'])
    h_market_rank = Paragraph('最佳组合收益在全市场的排序图', pdf_styles['STSONG'])
    # bie ȥ�� regression_analysis
    h_ic_by_month = Paragraph(ic_type + '（每月）', pdf_styles['STSONG'])
    h_er_by_month = Paragraph('月度超额收益热力图', pdf_styles['STSONG'])

    h_factor_ts = Paragraph('因子覆盖率统计图', pdf_styles['STSONG'])
    h_seg_return_new = Paragraph('分层测试最佳组合超额收益图(%d 层)' % seg_num, pdf_styles['STSONG'])
    current_time = datetime.datetime.today()
    pdf_report_date = '回测日期 :  ' + current_time.strftime('%Y-%m-%d %H:%M:%S')
    # h_version = Paragraph('Version: %s' % (version_number), pdf_styles['Normal'])
    h_date = Paragraph(pdf_report_date, pdf_styles['STSONG'])
    h_ic_style_corr = Paragraph('Style Correlation - IC Time Series', pdf_styles['STSONG'])
    if compare_style_flag:
        if factor_data_num > 250:
            h_ls_corr_show = Paragraph(ls_corr_name, pdf_styles['STSONG'])
        else:
            pass

    if easy_test == False:
        pass
        # bie ȥ�� regression_analysis
        # h_factor_TIC_Test = Paragraph('Neutralized T-Stats & IC Test', heading_size)
        # h_style_distribution = Paragraph('Style Correlation Distribution', heading_size)
        # bie ȥ�� regression_analysis
        # h_Tstat = Paragraph('Neutralized T-Statistics by Time', heading_size)
        # h_ic = Paragraph('Neutralized IC by Time', heading_size)
        # h_style_corr = Paragraph('Style Correlation Time Series - Rolling %d Days' % rolling_window, heading_size)

    h_excess_return_industry_sliced = Paragraph('按行业分层超额收益统计表' + add_t_cost, pdf_styles['STSONG'])

    h_sample_ret_stat = Paragraph('分层测试最佳组合采样收益分析表', pdf_styles['STSONG'])

    pprint('Generating pdf')
    # set path
    output_folder = os.path.dirname(pickle_name)
    report_name = 'FactorBacktest_%s_%s' % (str(factor_name), current_time.strftime('%Y%m%d_%H%M%S'))
    pdf_name = os.path.join(output_folder, report_name + '.pdf')

    doc = SimpleDocTemplate(pdf_name,
                            pagesize=letter,
                            topMargin=0.8 * inch,
                            bottomMargin=0.8 * inch)
    elements = []
    # elements.append(h_version)

    elements.append(h_date)
    # elements.append(h_corr_info)
    elements.append(Spacer(0, 1 * cm))

    elements.append(h_sum)
    elements.append(t_sum)
    elements.append(Spacer(0, 1 * cm))

    elements.append(h_factor_stat)
    elements.append(t_factor_stat)
    elements.append(Spacer(0, 1 * cm))
    # elements.append(h_ic_stats)
    elements.append(t_ic_stats)
    if os.environ.get('backtest_desc'):
        import urllib.parse
        comments = urllib.parse.unquote(os.environ.get('backtest_desc'))
        try:
            elements.append(Paragraph("回测记录备注: {}".format(comments),pdf_styles['STSONG']))
        except:
            elements.append(Paragraph("Test Comment: {}".format(comments),heading_size))
    elements.append(PageBreak())

    elements.append(h_factor_ts)
    elements.append(g_factor_ts)
    elements.append(Spacer(0, 1 * cm))

    elements.append(h_factor_auto_correlation_rolling)
    elements.append(g_factor_auto_correlation_rolling)
    elements.append(PageBreak())
    if compare_style_flag:
        if factor_data_num > 250:
            elements.append(h_ls_corr_show)
            elements.append(g_ls_corr_show)
            elements.append(Spacer(0, 1 * cm))

        else:
            pass

    elements.append(h_ic_decay)
    elements.append(g_ic_decay)
    elements.append(g_ic_duration)
    elements.append(PageBreak())
    elements.append(h_ic_ts_combined_roll)
    elements.append(g_ic_ts_combined_roll)
    elements.append(PageBreak())

    elements.append(h_excess_ret_stat_use)
    elements.append(t_excess_ret_stat_use)
    elements.append(Spacer(0, 1 * cm))

    elements.append(h_seg_return_new)
    elements.append(g_seg_return_new)
    elements.append(PageBreak())

    elements.append(h_market_rank)
    elements.append(g_market_rank)
    elements.append(Spacer(0, 1 * cm))

    elements.append(h_seg_ret_bar)
    elements.append(g_seg_ret_bar)
    elements.append(PageBreak())

    # bie ȥ�� regression_analysis
    # elements.append(g_ic_bar)
    # bie barra factor delay online
    # if not easy_test:
    #     elements.append(g_ic_context_mean)
    # elements.append(PageBreak())


    # elements.append(h_seg_year)
    # elements.append(g_seg_ret_year)
    # elements.append(h_seg_ret)
    # elements.append(g_seg_ret_performance)
    # elements.append(PageBreak())

    # elements.append(g_ic_ts_combined_cumsum)

    # bie ȥ�� regression_analysis
    # elements.append(h_ic_by_month)
    # elements.append(g_ic_by_month)
    # elements.append(h_ic_score_weighted_by_month)
    # elements.append(g_ic_score_weighted_by_month)
    elements.append(h_seg_sharpe_year)
    elements.append(g_seg_sharpe_year)
    elements.append(Spacer(0, 1 * cm))

    elements.append(h_seg_cumret)
    elements.append(g_seg_cumret)
    elements.append(PageBreak())

    elements.append(h_er_by_month)
    elements.append(g_er_by_month)
    elements.append(Spacer(0, 1 * cm))

    elements.append(h_return_by_year)
    elements.append(g_return_by_year)
    elements.append(PageBreak())


    if easy_test == False:
        pass
        # bie ȥ�� regression_analysis
        # elements.append(h_factor_TIC_Test)
        # elements.append(t_factor_TIC_Test)
        # elements.append(PageBreak())

        # bie ȥ�� regression_analysis
        # elements.append(h_ic)
        # elements.append(g_ic)
        # elements.append(h_Tstat)
        # elements.append(g_Tstat)
        # bie barra factor delay online
        # elements.append(h_style_distribution)
        # elements.append(g_style_distribution)
        # elements.append(PageBreak())
        # bie barra factor delay online
        # elements.append(h_style_corr)
        # elements.append(g_style_corr)
        # elements.append(PageBreak())
        # bie barra factor delay online
        # elements.append(h_ic_style_corr)
        # elements.append(g_ic_style_corr)
    elements.append(h_seg_ret_table)
    elements.append(t_seg_ret)
    elements.append(Spacer(0, 1 * cm))

    if t_cost_flag:
        elements.append(h_seg_ret_table_after_cost)
        elements.append(t_seg_return_after_cost)
        elements.append(PageBreak())
    if seg_by_industry_flag:
        elements.append(h_ic_by_industry)
        elements.append(g_ic_ind_by_year)
        elements.append(g_ic_ind_by_month)
        elements.append(PageBreak())
        elements.append(h_seg_by_industry)
        elements.append(g_seg_ind_by_month)
        elements.append(g_seg_ind_by_year)
        elements.append(Spacer(0, 1 * cm))

        elements.append(h_excess_return_industry_sliced)
        elements.append(t_excess_return_industry_sliced)
        elements.append(PageBreak())
        if g_industry_concentration:
            elements.append(g_industry_concentration)
            elements.append(Spacer(0, 1 * cm))

    ########################### added by Jiaping You, 20191129  ###################
    # elements.append(PageBreak())
    elements.append(h_sample_ret_stat)
    if factor_data_num > 250:
        elements.append(g_sample_bins_ret_diff2ret)
        elements.append(g_sample_std2ret)
    elements.append(PageBreak())

    elements.append(t_sample_bins_ret_stat)
    elements.append(g_sample_bin_ret_mean)
    elements.append(Spacer(0, 1 * cm))

    elements.append(h_Calmar_half_year)
    elements.append(g_Calmar_half_year)
    ###############################################################################

    doc.build(elements, onFirstPage=generate_first_page, onLaterPages=generate_later_pages, canvasmaker=NumberedCanvas)
    pprint('Report generation complete')
    return pdf_name

if __name__ == "__main__":
    generate_pdf('/tmp/pycharm_project_317/day_factor_backtest/barra_cne6_beta/FactorBacktest_barra_cne6_beta.pkl',factor_data_num=242)
