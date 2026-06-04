# -*- coding: utf-8 -*-
import os
import datetime
import pandas as pd
import numpy as np
import warnings
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.platypus import PageBreak
from tquant.strategy.day_factor_backtest_new.util.utility import pprint, calc_year_date_num, calc_filter_correlation
from tquant.strategy.day_factor_backtest_new.index_calc.return_index_calc import calc_annualized_return, max_drawdown_ts, calc_cum_return_ts, calc_percentile
from tquant.strategy.day_factor_backtest_new.index_calc.segment_index_calc import find_er_ls_col, segment_performance_measure
from tquant.strategy.day_factor_backtest_new.report.pdf_config import *
from tquant.strategy.day_factor_backtest_new.util.naming_config import *


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
                  width=img_width * inch, height=img_height * inch, fig_height=fig_height,
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
    fig, ax = plt.subplots()
    df1_plot = df1.plot(ax=ax, kind=plot_type, figsize=(fig_width, fig_height),
                        fontsize=font_size_axis, legend=False, color='orangered')
    df1_plot.set_title(plot_name, fontsize=font_size_title, fontweight=font_title_weight)
    df1_plot.set_ylabel(y_label1, fontsize=font_size_axis)
    ax.set_xlabel(x_label, fontsize=font_size_axis)
    plt.legend(*legend_helper(), loc=legend_loc, fontsize=font_size_legend)
    imgdata = BytesIO()
    plt.savefig(imgdata, format=img_format, dpi=img_dpi)
    imgdata.seek(0)
    plt.close()
    return Image(imgdata, width=img_width * inch, height=img_height * inch)


def generate_ts_heatmap_by_month_plot(ps_raw, title_text, vmin, vmax, fmt='.2f', agg_method='mean',
                                      width=img_width * inch, height=img_height * inch, fig_height=fig_height):
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
    plt.subplot(211,axisbg='#FFDAB9')
    plt.bar(np.arange(len(df)), df[bar_column], color='orangered')
    if show_stats:
        # 计算均值及当前值在近20日的排名
        df_avg, df_pct = df[bar_column].mean(), calc_percentile(df[bar_column].dropna()).iloc[-1]
        title = title + ' - Avg: %s - Current Percentile(Rolling 20 Days): %s' % (
            num2str(df_avg, show_format), num2str(df_pct, 'pct2'))
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
    plt1 = _.plot(ax=ax, figsize=(fig_width, fig_height * 1.3), fontsize=font_size_axis, legend=False)
    _ = easy_seg_return_cum['MDD_L-index']
    _.name = 'MDD - ' + title_text
    plt2 = _.plot(ax=ax, figsize=(fig_width, fig_height * 1.3), secondary_y=True,
                  fontsize=font_size_axis, style='--', legend=False)
    plt.legend(*legend_helper(), loc=legend_loc, fontsize=font_size_legend)
    plt.ylim([0.05, mdd_l_index - 0.1])

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


def generate_pdf_customization(factor_name, pickle_name, rolling_window=20, factor_data_num=0, cost_flag=True,
                               module=None):
    # complete 完整模式（全输出），basic基础模式（仅包含统计信息和与收益相关信息），segment分层模式 ，industry行业信息模式
    if not module:
        module = 'complete'
    if not isinstance(module, str):
        raise Exception("请输入正确格式的module,目前仅支持")
    if module == "basic":
        comment = ['basic']
    elif module == "basic_stability":
        comment = ['basic', 'stability']
    elif module == "basic_segment":
        comment = ['basic', 'segment']
    elif module == "basic_seg_stab":
        comment = ['basic', 'segment', 'stability']
    elif module == "industry":
        comment = ['basic', 'segment', 'industry']
    elif module == "complete":
        comment = ['basic', 'segment', 'industry', 'stability']
    else:
        raise Exception(
            "目前仅支持'basic', 'segment','basic_stability', 'basic_seg_stab' ,'industry', 'complete'六种格式的回测报告，暂不支持{}".format(
                module))

    interest_type = 'cumprod'
    compare_style = 'Size'
    ic_type = 'original'
    # ic_type = 'score_weighted'
    pprint('Generating pdf')
    output_folder = os.path.dirname(pickle_name)
    current_time = datetime.datetime.today()
    report_name = 'FactorBacktest_%s_%s' % (str(factor_name), current_time.strftime('%Y%m%d_%H%M%S'))
    pdf_name = os.path.join(output_folder, report_name + '.pdf')
    doc = SimpleDocTemplate(pdf_name,
                            pagesize=letter,
                            topMargin=0.8 * inch,
                            bottomMargin=0.8 * inch)

    elements = []
    # 回测日期
    pdf_report_date = '回测日期 :  ' + current_time.strftime('%Y-%m-%d %H:%M:%S')
    h_date = Paragraph(pdf_report_date, pdf_styles['STSONG'])
    elements.append(h_date)
    elements.append(Spacer(0, 1 * cm))
    output_dict = pd.read_pickle(pickle_name)

    if os.environ.get('backtest_desc'):
        import urllib.parse
        comments = urllib.parse.unquote(os.environ.get('backtest_desc'))
        try:
            elements.append(Paragraph("回测记录备注: {}".format(comments),pdf_styles['STSONG']))
        except:
            elements.append(Paragraph("Test Comment: {}".format(comments),heading_size))
    elements.append(Spacer(0, 1 * cm))
    
    if 'basic' in comment:
        # 回测报告信息
        sum_df = output_dict['summary_info']
        h_sum = Paragraph('回测报告信息', pdf_styles['STSONG'])
        t_sum = generate_basicinfo_table(sum_df, ['str1'] * len(sum_df), axis=0, reformat_type=False)
        elements.append(h_sum)
        elements.append(t_sum)
        elements.append(Spacer(0, 1 * cm))

        # 统计性指标表
        factor_stat = output_dict['distribution']
        factor_stat.columns = ['Basic Statistics']
        t_factor_stat = generate_table(factor_stat.T, ['dcm2', 'dcm2', 'pct2', 'dcm3', 'dcm3', 'dcm2', 'dcm2', 'dcm2'],
                                       axis=1, reformat_type=True)
        h_factor_stat = Paragraph('因子分布指标与IC统计表', pdf_styles['STSONG'])
        elements.append(h_factor_stat)
        elements.append(t_factor_stat)
        elements.append(Spacer(0, 1 * cm))

        # 因子的自相关性
        factor_auto_correlation = output_dict['factor_auto_correlation']
        factor_auto_correlation_roll = factor_auto_correlation.rolling(rolling_window).mean()
        auto_corr_mean = factor_auto_correlation.mean().values[0] * 100
        h_factor_auto_correlation_rolling = Paragraph('因子自相关', pdf_styles['STSONG'])
        g_factor_auto_correlation_rolling = generate_plot(factor_auto_correlation_roll,
                                                          plot_name='Factor Auto Correlation \n' + \
                                                                    '(avg correlation: %0.2f' % auto_corr_mean + '%)',
                                                          x_label='', y_label='Correlation')
        elements.append(h_factor_auto_correlation_rolling)
        elements.append(g_factor_auto_correlation_rolling)
        elements.append(Spacer(0, 1 * cm))

        # 因子覆盖率
        factor_ts = output_dict['stock_count']
        g_factor_ts = generate_plot(factor_ts, plot_name='Stock Count with Factor \n' + \
                                                         '(avg stock count: %d)' % (factor_ts.mean().values[0]),
                                    x_label='', y_label='Number of Stocks')
        h_factor_ts = Paragraph('因子覆盖率统计图', pdf_styles['STSONG'])
        elements.append(h_factor_ts)
        elements.append(g_factor_ts)
        elements.append(PageBreak())

        # 因子与收益的IC
        ic_stats = output_dict['ic_stats']
        h_ic_stats = Paragraph('因子IC指标统计图', pdf_styles['STSONG'])
        t_ic_stats = generate_table(ic_stats, ['dcm3'] * ic_stats.shape[1], axis=0, reformat_type=True)
        elements.append(h_ic_stats)
        elements.append(t_ic_stats)
        elements.append(Spacer(0, 1 * cm))

        # 因子与收益IC
        ic_ts_combined = output_dict['ic_ts_combined']
        ic_ts_combined_show = ic_ts_combined[[i for i in ic_ts_combined.columns if i[0] != 'Q']]
        ic_ts_combined_roll = ic_ts_combined_show.rolling(rolling_window, min_periods=0).apply(np.nanmean,raw=True)
        ic_percentile = calc_percentile(ic_ts_combined_roll).dropna().iloc[-1]
        h_ic_ts_combined_roll = Paragraph("因子与收益IC({}日平均)".format(rolling_window), pdf_styles['STSONG'])
        g_ic_ts_combined_roll = generate_plot_with_secondary(ic_ts_combined_roll,
                                                             'IC (Rolling %d day Average) \nCurrent %s Percentile %.2f' % (
                                                             rolling_window, 'IC Original',
                                                             ic_percentile.loc['IC Original']), '', 'IC', 'Bucket IC',
                                                             plot_type='line')
        elements.append(h_ic_ts_combined_roll)
        elements.append(g_ic_ts_combined_roll)
        elements.append(Spacer(0, 1 * cm))
        ic_duration = output_dict['ic_duration']
        ic_decay = output_dict['ic_decay']
        h_ic_decay = Paragraph('因子IC随时间的衰减图', pdf_styles['STSONG'])
        g_ic_decay = generate_plot(ic_decay, plot_name='IC Decay', x_label='Days after factor', y_label='IC')
        g_ic_duration = generate_plot(ic_duration, plot_name='IC Duration', x_label='Days after factor',
                                      y_label='IC', plot_type='bar', rot=0)
        elements.append(h_ic_decay)
        elements.append(g_ic_decay)
        elements.append(g_ic_duration)
        elements.append(Spacer(0, 1 * cm))

        alpha_cumsum = output_dict['alpha_cumsum']
        h_alpha_cumsum = Paragraph('因子IC的Alpha离散图', pdf_styles['STSONG'])
        g_alpha_cumsum = generate_plot(alpha_cumsum, plot_name='IC Alpha Cumsum', x_label='Days',
                                       y_label='COV(FAC,Ret)/STD(FAC)', rot=0)
        elements.append(h_alpha_cumsum)
        elements.append(g_alpha_cumsum)
        elements.append(PageBreak())

    if "segment" in comment:
        seg_ret_use = output_dict['seg_return']
        seg_num = int(
            max([float(item.replace('Q', '')) for item in seg_ret_use.columns if '-' not in item and 'Q' in item]))
        seg_cumret = calc_cum_return_ts(seg_ret_use, interest_type=interest_type)
        h_seg_cumret = Paragraph("分层累积收益", pdf_styles['STSONG'])
        g_seg_cumret = generate_plot(seg_cumret, plot_name='Segment Return', x_label='', y_label='Cummulative Return')
        elements.append(h_seg_cumret)
        elements.append(g_seg_cumret)
        elements.append(Spacer(0, 1 * cm))

        # 分层测试年化Sharpe统计图
        seg_return_stat_year = output_dict['seg_return_stat_year']
        seg_return_stat_year.index.names = ['dt', '']
        seg_ret_year = seg_return_stat_year['Return(Ann.)'].unstack()
        seg_er_col = [col for col in seg_ret_year.columns.tolist() if col.find('-') > 0]
        assert len(seg_er_col) == 1
        seg_col_name_order = ['Q' + str(i + 1) for i in range(seg_num)] + seg_er_col + ['Index']
        seg_sharpe_year = (seg_return_stat_year['Sharpe'].unstack())[seg_col_name_order]
        h_seg_sharpe_year = Paragraph("分层测试年化Sharpe统计图", pdf_styles['STSONG'])
        g_seg_sharpe_year = generate_plot(seg_sharpe_year, plot_name='Sharpe', x_label='', y_label='Sharpe',
                                          plot_type='bar', legend_outside=True, rot=45)
        elements.append(h_seg_sharpe_year)
        elements.append(g_seg_sharpe_year)
        elements.append(PageBreak())

        # 年度超额收益图
        seg_return_by_year_list = []
        seg_er_col = [col for col in seg_ret_year.columns.tolist() if col.find('-') > 0]
        assert len(seg_er_col) == 1
        for year in seg_ret_use.index.year.unique():
            _ = calc_cum_return_ts(seg_ret_use[seg_er_col[0]].loc[str(year)], interest_type=interest_type)
            _.name = year
            _.index = range(1, len(_) + 1)
            seg_return_by_year_list.append(_)
        seg_return_by_year = pd.concat(seg_return_by_year_list, axis=1)

        g_return_by_year = generate_plot(seg_return_by_year, plot_name=seg_er_col[0] + ' Return by Year',
                                         x_label='Day in Year',
                                         y_label='Cummulative Return')
        h_return_by_year = Paragraph('年度超额收益图', pdf_styles['STSONG'])
        elements.append(h_return_by_year)
        elements.append(g_return_by_year)
        elements.append(Spacer(0, 1 * cm))


        seg_ret_stat = output_dict['seg_return_stat']
        h_seg_ret = Paragraph('分层测试指标统计表({})'.format("费后" if cost_flag else "费前"), pdf_styles['STSONG'])
        t_seg_ret = generate_table(seg_ret_stat, ['dcm2', 'dcm2', 'pct2', 'dcm3', 'dcm3', 'dcm2', 'dcm2', 'dcm2']*2,
                                   axis=1, reformat_type=True)
        elements.append(h_seg_ret)
        elements.append(t_seg_ret)
        elements.append(Spacer(0, 1 * cm))
        if 'industry' not in comment:
            import collections
            show_dict = collections.OrderedDict()
            show_dict['收益分析'] = output_dict['seg_return']
            show_dict_stat = {i: segment_performance_measure(show_dict[i], interest_type) for i in show_dict}
            seg_ret_sum_stats = pd.concat([show_dict_stat[i].iloc[-1] for i in show_dict_stat], axis=1).T
            seg_ret_sum_stats.index = list(show_dict.keys())
            seg_ret_sum_stats = seg_ret_sum_stats[['Return(Ann.)', 'Vol(Ann.)', 'Sharpe', 'MDD', 'HitRate']]
            h_excess_ret_stat_use = Paragraph('分层测试最佳组合收益统计', pdf_styles['STSONG'])
            t_excess_ret_stat_use = generate_table(seg_ret_sum_stats, ['pct2', 'pct2', 'dcm2', 'pct2', 'pct2'], axis=1, reformat_type=True)
            elements.append(h_excess_ret_stat_use)
            elements.append(t_excess_ret_stat_use)
            elements.append(PageBreak())


        # 月度超额收益热力图
        er_col_use, l_col_use, s_col_use = find_er_ls_col(seg_ret_use)
        er_use = seg_ret_use[er_col_use]  # 超额收益
        h_er_by_month = Paragraph('月度超额收益热力图', pdf_styles['STSONG'])
        g_er_by_month = generate_ts_heatmap_by_month_plot(er_use * 100,
                                                          title_text='{} Excess Return(%) by Month'.format(
                                                              er_col_use),
                                                          vmin=-10, vmax=10, fmt='.2f', agg_method='sum',
                                                          fig_height=fig_height * 1.5
                                                          )  #
        elements.append(h_er_by_month)
        elements.append(g_er_by_month)
        elements.append(Spacer(0, 1 * cm))

        # 分层测试最佳组合超额收益
        seg_ret_use['Avg %d Period' % rolling_window] = seg_ret_use[er_col_use].rolling(
            rolling_window).mean()  # 滚动平均，seg_er_col最大收益层的超额收益
        h_seg_ret_bar = Paragraph("分层测试最佳组合超额收益({}日平均)".format(rolling_window), pdf_styles['STSONG'])
        g_seg_ret_bar = generate_bar_line_plot(df=seg_ret_use, title='{} Excess Return'.format(er_col_use),
                                               bar_column=er_col_use,
                                               line_column='Avg %d Period' % (rolling_window), show_stats=True,
                                               show_format='pct2')
        elements.append(h_seg_ret_bar)
        elements.append(g_seg_ret_bar)
        elements.append(Spacer(0, 1 * cm))


        market_rank = output_dict['market_rank']
        h_market_rank = Paragraph('最佳组合收益在全市场的排序图', pdf_styles['STSONG'])
        market_rank_df = pd.concat([market_rank, market_rank.rolling(rolling_window).mean()], axis=1)
        col_name_roll = '%d 日平均' % (rolling_window)
        market_rank_df.columns = ['market_rank', col_name_roll]
        g_market_rank = generate_bar_line_plot(df=market_rank_df, title='Top Segment Total Return Market Rank',
                                               bar_column='market_rank',
                                               line_column=col_name_roll, show_stats=True, show_format='pct2')
        elements.append(h_market_rank)
        elements.append(g_market_rank)
        elements.append(Spacer(0, 1 * cm))


        # 超过一年才能计算的指标
        if factor_data_num>250:
            seg_return_fac = output_dict['seg_return_fac']
            er_col_use_fac, l_col_use_fac, s_col_use_fac = find_er_ls_col(seg_return_fac)  # Q10-Index， Q1，Q10
            ls_ret_use_fac = er_col_use_fac[l_col_use_fac] - er_col_use_fac[s_col_use_fac]  # ls，多空组合，第一层减去最后一层
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
            add_avg_str = '\n 历史相关性: %s: %s   %s: %s' % (
                corr_df.columns[0], num2str(all_history_corr, 'pct2'),
                corr_df.columns[1], num2str(all_history_remove_mid_corr, 'pct2'))
            plt_name = 'Correlation with %s (Rolling %d Days) \n (Factor Excess Return vs Style Long Short Return)%s' % (
                compare_style, corr_win, add_avg_str)
            h_ls_corr_show = Paragraph('相关性 %s ( %d 天窗口)' % (compare_style, corr_win), pdf_styles['STSONG'])
            g_ls_corr_show = generate_plot(corr_df, plot_name=plt_name, x_label='', y_label='Correlation',
                                           show_stats=True, show_format='pct2', fig_height=fig_height * 1.1)
            elements.append(h_ls_corr_show)
            elements.append(g_ls_corr_show)
            elements.append(PageBreak())

    if 'industry' in comment:
        h_ic_by_industry = Paragraph('行业与收益的IC', pdf_styles['STSONG'])
        ic_by_industry = output_dict['ic_by_industry']
        g_ic_ind_by_month = generate_ts_by_type_plot(ic_by_industry, by='Month', x_label=ic_type, fmt='.3f')
        g_ic_ind_by_year = generate_ts_by_type_plot(ic_by_industry, by='Year', x_label=ic_type, fmt='.3f')
        elements.append(h_ic_by_industry)
        elements.append(g_ic_ind_by_year)
        elements.append(g_ic_ind_by_month)
        elements.append(Spacer(0, 1 * cm))


        seg_return_each_industry = output_dict['seg_return_each_industry']
        ind_seg_er_col = [col for col in seg_return_each_industry.columns.tolist() if col.find('-') > 0]
        assert len(ind_seg_er_col) == 1
        seg_by_industry = seg_return_each_industry[ind_seg_er_col[0]].unstack() * 100
        g_seg_ind_by_month = generate_ts_by_type_plot(seg_by_industry, by='Month', x_label='Excess Return(%)',
                                                      ann_scale=True, vmin=-10, vmax=10)
        g_seg_ind_by_year = generate_ts_by_type_plot(seg_by_industry, by='Year', x_label='Excess Return(%)',
                                                     ann_scale=True, vmin=-50, vmax=50)
        h_seg_by_industry = Paragraph('行业超额收益率统计图({})'.format("费后" if cost_flag else "费前"), pdf_styles['STSONG'])
        elements.append(h_seg_by_industry)
        elements.append(g_seg_ind_by_month)
        elements.append(g_seg_ind_by_year)
        elements.append(Spacer(0, 1 * cm))

        industry_concentration = output_dict['industry_concentration']
        if not industry_concentration.dropna().empty:
            g_industry_concentration = generate_plot(industry_concentration,
                                                     plot_name='Excess Return - Industry Concentration',
                                                     x_label='', y_label='Concentration', plot_type='line',
                                                     show_stats=True)  # , rot=45)
            elements.append(g_industry_concentration)
            elements.append(Spacer(0, 1 * cm))

        seg_return_each_industry_stat = output_dict['seg_return_each_industry_stat']
        excess_return_industry_sliced = seg_return_each_industry_stat.xs(ind_seg_er_col[0], level=1)
        h_excess_return_industry_sliced = Paragraph('按行业分层超额收益统计表({})'.format("费后" if cost_flag else "费前"), pdf_styles['STSONG'])
        t_excess_return_industry_sliced = generate_table(excess_return_industry_sliced[['Return(Ann.)', 'Vol(Ann.)', 'Sharpe', 'MDD', 'HitRate']], ['pct2', 'pct2', 'dcm2', 'pct2', 'pct2'],
                                                         axis=1, reformat_type=True)
        elements.append(h_excess_return_industry_sliced)
        elements.append(t_excess_return_industry_sliced)
        elements.append(Spacer(0, 1 * cm))

        import collections
        show_dict = collections.OrderedDict()
        show_dict['收益分析'] = output_dict['seg_return']

        show_dict_stat = {i: segment_performance_measure(show_dict[i], interest_type) for i in show_dict}
        seg_ret_sum_stats = pd.concat([show_dict_stat[i].iloc[-1] for i in show_dict_stat], axis=1).T
        seg_ret_sum_stats.index = list(show_dict.keys())
        seg_ret_sum_stats = seg_ret_sum_stats[['Return(Ann.)', 'Vol(Ann.)', 'Sharpe', 'MDD', 'HitRate']]
        h_excess_ret_stat_use = Paragraph('分层测试最佳组合收益统计', pdf_styles['STSONG'])
        t_excess_ret_stat_use = generate_table(seg_ret_sum_stats, ['pct2', 'pct2', 'dcm2', 'pct2', 'pct2'], axis=1, reformat_type=True)
        elements.append(h_excess_ret_stat_use)
        elements.append(t_excess_ret_stat_use)
        elements.append(PageBreak())

    if "stability" in comment:
        sample_bin_ret_mean = output_dict['sample_bin_ret_mean']
        sample_bins_ret_stat = output_dict['sample_bins_ret_stat']
        h_sample_bins_ret_stat =Paragraph('采样超额收益', pdf_styles['STSONG'])
        t_sample_bins_ret_stat = generate_table(sample_bins_ret_stat, ['dcm2', 'dcm2'], axis=0, reformat_type=True)
        g_sample_bin_ret_mean = generate_plot(sample_bin_ret_mean, plot_name='Sampled mean excess return',
                                              x_label='Sample',
                                              y_label='Mean Return ', plot_type='bar', rot=45)
        elements.append(h_sample_bins_ret_stat)
        elements.append(t_sample_bins_ret_stat)
        elements.append(g_sample_bin_ret_mean)
        elements.append(Spacer(0, 1 * cm))

        if factor_data_num > 250:
            sample_std2ret = output_dict['sample_std2ret']
            sample_bins_ret_diff2ret = output_dict['sample_bins_ret_diff2ret']
            g_sample_bins_ret_diff2ret = generate_plot(sample_bins_ret_diff2ret,
                                                       plot_name='Rolling (Max ret - Min ret) / Mean ret', x_label='',
                                                       y_label='', rot=45)
            g_sample_std2ret = generate_plot(sample_std2ret,
                                             plot_name='Rolling Variance ratio of sampled ret (STD/Mean)',
                                             x_label='', y_label='', rot=45)
            elements.append(g_sample_bins_ret_diff2ret)
            elements.append(g_sample_std2ret)
            elements.append(Spacer(0, 1 * cm))

        Calmar_half_year = output_dict['Calmar_half_year']
        h_Calmar_half_year = Paragraph("Calmar比率图(半年)", pdf_styles['STSONG'])
        g_Calmar_half_year = generate_plot(Calmar_half_year, plot_name='Calmar ratio in half year', x_label='',
                                           y_label='Calmar Ratio', plot_type='bar', rot=30, bottom=0.2)
        elements.append(h_Calmar_half_year)
        elements.append(g_Calmar_half_year)
        elements.append(PageBreak())

    ###############################################################################

    doc.build(elements, onFirstPage=generate_first_page, onLaterPages=generate_later_pages, canvasmaker=NumberedCanvas)
    pprint('Report generation complete')
    return pdf_name


if __name__ == "__main__":
    generate_pdf('/tmp/pycharm_project_317/day_factor_backtest/barra_cne6_beta/FactorBacktest_barra_cne6_beta.pkl',
                 factor_data_num=242)
