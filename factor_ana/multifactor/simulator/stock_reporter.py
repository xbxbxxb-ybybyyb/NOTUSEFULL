__author__ = "Software Authors: Xu Deyuan"
__copyright__ = "Copyright (C) 2019 HTSC"
__license__ = "Private"
__version__ = "1.0.3"
import numpy as np
import pandas as pd
import datetime as dt
from collections import Iterable
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdate
from matplotlib import colors as mcolors
import os
import seaborn as sns
from multifactor.backtest.pdf_config import*
from multifactor.backtest.naming_config import*
from multifactor.IO import IO
from multifactor.IO.IO_enums import*
import multifactor.utility.dt as tdt
from functools import partial
import scipy.stats as sps
import warnings
simulator_version=__version__
def generate_plot(df,plot_name,x_label,y_label,plot_type='line',rot=None,legend_outside=False,bottom=None,**kwargs):
    legend_on=True if min(df.shape)>1 else False
    fig,ax=plt.subplots()
    df_plot=df.plot(kind=plot_type,figsize=(fig_width,fig_height),legend=legend_on,fontsize=font_size_axis,rot=rot,**kwargs)
    if legend_on:
        if legend_outside:
            plt.legend(loc='center left',bbox_to_anchor=(1,0.5),fontsize=font_size_legend)
        else:
            plt.legend(loc=legend_loc,fontsize=font_size_legend)
    if bottom is not None:
        plt.subplots_adjust(bottom=bottom)
    df_plot.set_title(plot_name,fontsize=font_size_title,fontweight=font_title_weight)
    df_plot.set_xlabel(x_label,fontsize=font_size_axis)
    df_plot.set_ylabel(y_label,fontsize=font_size_axis)
    imgdata=BytesIO()
    df_plot.figure.savefig(imgdata,format=img_format,dpi=img_dpi)
    imgdata.seek(0)
    plt.clf()
    plt.close()
    return Image(imgdata,width=img_width*inch,height=img_height*inch)
def generate_table(df,col_type,axis,reformat_type):
    df_str=dataframe2str(df,col_type,axis,reformat_type)
    df_str[0]=[i.encode('utf-8')for i in df_str[0]]
    t=Table(df_str)
    mytable=TableStyle([('BACKGROUND',(0,0),(-1,0),colors.white),('TEXTCOLOR',(0,0),(-1,0),colors.black),('FONTNAME',(0,0),(-1,-1),font_name),('FONTSIZE',(0,0),(-1,-1),CANVAS_FONT_SIZE)])
    t.setStyle(mytable)
    return t
def dataframe2str(df,col_type,axis,reformat_type):
    df=df if axis==1 else df.T
    df_col=df.columns.tolist()
    df_row=df.index.tolist()
    df_str=['']+df_row
    for col,ct in zip(df_col,col_type):
        data=[col]+num2str(df[col].values.tolist(),ct)if reformat_type==True else[col]+df[col].values.tolist()
        df_str=np.vstack([df_str,data])
    df_str=df_str.T.tolist()if axis==1 else df_str.tolist()
    return df_str
def num2str(data,data_type):
    round_num=int(data_type[-1])
    number_type=data_type[:-1]
    if number_type=='pct':
        data=[('{:'+('.%d'%round_num)+'%'+'}').format(i)if not pd.isnull(i)else 'NaN' for i in data]
    elif number_type=='dcm':
        data=[('{:'+('.%d'%round_num)+'f'+'}').format(i)if not pd.isnull(i)else 'NaN' for i in data]
    return data
def acronym(phrase,min_len=6,seq=2):
    res=''
    assert isinstance(phrase,str)
    if len(phrase)<=min_len:
        res=phrase
    else:
        seq_counter=seq
        for l in phrase:
            if l.isupper():
                res+=l
                seq_counter=0
            elif seq_counter<seq:
                res+=l
                seq_counter+=1
    return res
def acronyms(phrases):
    assert not isinstance(phrases,str)
    return[acronym(item)for item in phrases]
def calc_cum_return_ts(return_ps,interest_type='SIMPLE'):
    if interest_type=='SIMPLE':
        res=return_ps.cumsum()+1
    else:
        res=(return_ps+1).cumprod()
    return res
def calc_annualized_return(return_ps,interest_type='SIMPLE'):
    year_date_num=calc_year_date_num(return_ps)
    if interest_type=='SIMPLE':
        res=return_ps.mean()*year_date_num
    else:
        _=calc_cum_return_ts(return_ps,interest_type=interest_type)
        if isinstance(_,np.ndarray):
            res=_[-1]**(year_date_num/len(return_ps))-1
        else:
            res=_.iloc[-1]**(year_date_num/len(return_ps))-1
    return res
def calc_year_date_num(ps_raw):
    predefined_num=252
    if isinstance(ps_raw,np.ndarray):
        return predefined_num
    year_list=list(ps_raw.index.year.unique())
    date_num_list=list()
    try:
        for year in year_list:
            year_date_num=len(tdt.get_trading_date_range(dt.datetime(year=int(year),month=1,day=1),dt.datetime(year=int(year),month=12,day=31)))
            date_num_list.append(year_date_num)
    except OSError:
        print('Cannot Retrieve Calendar Data')
        return predefined_num
    return np.mean(date_num_list)
def max_drawdown_ts(cum_return_ps,interest_type='SIMPLE',return_drawdown_period=False):
    assert isinstance(cum_return_ps,pd.Series)
    cum_return_ps=cum_return_ps.fillna(0)
    cum_max=np.maximum.accumulate(cum_return_ps)
    if interest_type=='SIMPLE':
        mdd_ts=cum_return_ps-cum_max
    else:
        mdd_ts=(cum_return_ps-cum_max)/cum_max
    mdd_idx=mdd_ts.idxmin()
    mdd_max_level=cum_max.loc[mdd_idx]
    _=cum_return_ps.loc[:mdd_idx]
    try:
        mdd_begin_idx=_[_==mdd_max_level].index[-1]
    except IndexError:
        mdd_begin_idx=pd.NaT
    _=cum_return_ps.loc[mdd_idx:]
    try:
        mdd_end_idx=_[_>=mdd_max_level].index[0]
    except IndexError:
        mdd_end_idx=pd.NaT
    if return_drawdown_period:
        return mdd_ts,(mdd_begin_idx,mdd_end_idx)
    else:
        return mdd_ts
def generate_line_subplot(df):
    df.index.name=''
    height_scaler=min(max_fig_height,fig_height*len(df.columns)*0.75)/fig_height
    df.plot(subplots=True,figsize=(fig_width,fig_height*height_scaler),fontsize=font_size_axis)
    [ax.legend(loc=legend_loc,fontsize=font_size_legend)for ax in plt.gcf().axes]
    plt.subplots_adjust(bottom=0.05,top=0.99,wspace=0,hspace=0.1)
    imgdata=BytesIO()
    plt.savefig(imgdata,format=img_format,dpi=img_dpi)
    imgdata.seek(0)
    plt.clf()
    plt.close()
    return Image(imgdata,width=img_width*inch,height=img_height*inch*height_scaler)
def generate_ts_heatmap_by_month_plot(ps_raw,title_text,vmin,vmax,fmt='.2f',agg_method='mean'):
    year_list=list(set(ps_raw.index.year))
    year_list.sort(reverse=False)
    month_ps=pd.DataFrame(index=[i for i in range(1,13)])
    for year in year_list:
        sliced=ps_raw.loc[str(year)]
        if agg_method=='mean':
            month_ps[year]=sliced.groupby(sliced.index.month).mean()
        elif agg_method=='sum':
            month_ps[year]=sliced.groupby(sliced.index.month).sum()
        else:
            raise NotImplementedError
    sns.set(font_scale=1.6)
    cmap=sns.diverging_palette(220,10,as_cmap=True)
    month_ps=month_ps.rename(index=month_mapper)
    month_ps.index.name=title_text
    month_ps.columns.name=''
    plt.figure(figsize=(fig_width,fig_height))
    sns.heatmap(month_ps.T,vmin=vmin,vmax=vmax,linewidths=.5,cmap=cmap,annot=True,fmt=fmt)
    imgdata=BytesIO()
    plt.subplots_adjust(right=1,top=1)
    plt.savefig(imgdata,format=img_format,dpi=img_dpi)
    imgdata.seek(0)
    plt.clf()
    plt.close()
    plt.style.use('ggplot')
    return Image(imgdata,width=img_width*inch,height=img_height*inch)
def generate_whisker_plot(df,title='Style Correlation Distribution',rot=0,bottom=None,ylim=None,**kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        df.index.name=''
        df.plot(kind='box',figsize=(fig_width,fig_height),rot=rot,fontsize=font_size_axis,**kwargs)
        if ylim is not None:
            plt.ylim(ylim)
        plt.title(title,fontsize=font_size_title,fontweight=font_title_weight)
        if bottom is not None:
            plt.subplots_adjust(bottom=bottom)
        imgdata=BytesIO()
        plt.savefig(imgdata,format=img_format,dpi=img_dpi)
        imgdata.seek(0)
        plt.clf()
        plt.close()
    return Image(imgdata,width=img_width*inch,height=img_height*inch)
def legend_helper(axes=None):
    handles,labels=[],[]
    _=plt.gcf().axes if axes is None else axes
    assert isinstance(_,Iterable)
    for ax in _:
        for h,l in zip(*ax.get_legend_handles_labels()):
            handles.append(h)
            labels.append(l)
    return handles,labels
def reversed_dict(x):
    assert isinstance(x,dict)
    return{v:k for k,v in x.items()}
universe_mapper={'ZZ500':'index_500','HS300':'index_300','SZ50':'index_50','alpha_index':'alpha_universe','alpha_universe':'alpha_universe'}
reversed_universe_mapper=reversed_dict(universe_mapper)
index_mapper={'ZZ500':'000905.SH','ZZ800':'000906.SH','SZ50':'000016.SH','HS300':'000300.SH','alpha_index':'alpha_index'}
reversed_index_mapper=reversed_dict(index_mapper)
weight_mapper={'ZZ500':'index_weight_zz500','HS300':'index_weight_hs300','SZ50':'index_weight_sh50'}
reversed_weight_mapper=reversed_dict(weight_mapper)
def pnl_stats_helper(daily_return_ps,interest_type):
    daily_return_ps=daily_return_ps.dropna()
    cum_daily_return=calc_cum_return_ts(daily_return_ps,interest_type=interest_type)
    mdd_ts,(mdd_begin,mdd_end)=max_drawdown_ts(cum_daily_return,interest_type=interest_type,return_drawdown_period=True)
    if mdd_begin is not pd.NaT and mdd_end is not pd.NaT:
        mdd_duration=len(daily_return_ps.loc[mdd_begin:mdd_end])
    else:
        mdd_duration=np.nan
    cum_daily_return.name='Cum Return'
    mdd_ts.name='Max Drawdown'
    year_date_num=calc_year_date_num(daily_return_ps)
    ann_ret=calc_annualized_return(daily_return_ps,interest_type=interest_type)
    ann_vol=daily_return_ps.std()*np.sqrt(year_date_num)
    ann_sharpe=ann_ret/ann_vol
    hit_rate=len(daily_return_ps[daily_return_ps>0])/len(daily_return_ps)
    return{'daily_return_ps':daily_return_ps,'cum_daily_return':cum_daily_return,'ret':cum_daily_return[-1]-1,'mdd_ts':mdd_ts,'mdd':mdd_ts.min(),'mdd_begin':mdd_begin,'mdd_end':mdd_end,'mdd_duration':mdd_duration,'ann_ret':ann_ret,'ann_vol':ann_vol,'ann_sharpe':ann_sharpe,'hit_rate':hit_rate}
def pnl_with_mdd_plot_helper(daily_return_ps,index_daily_return_ps,title_text,interest_type,label=False,rot=0,benchmark='Index'):
    stats=pnl_stats_helper(daily_return_ps,interest_type)
    if index_daily_return_ps is not None:
        index_stats=pnl_stats_helper(index_daily_return_ps,interest_type)
    else:
        index_stats=None
    ax=plt.gca()
    plt1=stats['cum_daily_return'].plot(ax=ax,fontsize=font_size_axis,legend=False,rot=rot)
    plt2=(stats['mdd_ts']*100).plot(ax=ax,secondary_y=True,fontsize=font_size_axis,style='--',legend=False,rot=rot)
    if index_stats is not None:
        _=index_stats['cum_daily_return']
        _.name=_.name+': '+benchmark
        plt3=_.plot(ax=ax,fontsize=font_size_axis,legend=False,rot=rot)
        plt3.set_xlabel('')
    if label:
        plt.legend(*legend_helper(),loc=legend_loc,fontsize=font_size_legend)
    plt1.set_title('Annualized Return: %.2f%%'%(stats['ann_ret']*100)+', '+'Max Drawdown: %.2f%%'%(stats['mdd']*100)+', '+'Sharpe: %.2f'%stats['ann_sharpe']+title_text,fontsize=font_size_title,fontweight=font_title_weight)
    plt1.set_xlabel('')
    plt2.set_xlabel('')
    if label:
        plt1.set_ylabel('Cum Return',fontsize=font_size_axis)
        plt2.set_ylabel('Max Drawdown %',fontsize=font_size_axis)
    _bot,_top=plt1.get_ylim()
    plt1.set_ylim((_bot,_top+0.2*(_top-_bot)))
    _bot,_top=plt2.get_ylim()
    plt2.set_ylim((0,_bot-0.5*(_top-_bot)))
    plt2.invert_yaxis()
    plt.grid(True)
def generate_pnl_with_mdd_plot(daily_return_ps,index_daily_return_ps,interest_type,benchmark):
    plt.figure(figsize=(fig_width,fig_height))
    pnl_with_mdd_plot_helper(daily_return_ps,index_daily_return_ps,'',interest_type,label=True,benchmark=benchmark)
    imgdata=BytesIO()
    plt.savefig(imgdata,format=img_format,dpi=img_dpi)
    imgdata.seek(0)
    plt.clf()
    plt.close()
    return Image(imgdata,width=img_width*inch,height=img_height*inch)
def generate_pnl_with_mdd_year_plot(daily_return_ps,interest_type):
    year_list=list(daily_return_ps.index.year.unique())
    year_list.sort(reverse=True)
    year_num=len(year_list)
    plt_rows=int(np.ceil(year_num/2))
    height_scaler=min(max_fig_height,fig_height*plt_rows*0.75)/fig_height
    plt.figure(figsize=(fig_width,fig_height*height_scaler))
    for i in range(year_num):
        ax=plt.subplot(plt_rows,2,i+1)
        stats=pnl_stats_helper(daily_return_ps.loc[str(year_list[i])],interest_type)
        stats['cum_daily_return'].plot(fontsize=font_size_axis)
        plt.title('%d - Ret %.2f%%, MDD %.2f%%, Sharpe %.2f'%(year_list[i],stats['ret']*100,stats['mdd']*100,stats['ann_sharpe']),fontsize=font_size_title,fontweight=font_title_weight)
        ax.xaxis.set_major_formatter(plt_dates.DateFormatter('%m-%d'))
    plt.tight_layout()
    imgdata=BytesIO()
    plt.savefig(imgdata,format=img_format,dpi=img_dpi)
    imgdata.seek(0)
    plt.clf()
    plt.close()
    return Image(imgdata,width=img_width*inch,height=img_height*inch*height_scaler)
def sharpe_helper(daily_return_ps,year_date_num,interest_type):
    ann_ret=calc_annualized_return(daily_return_ps,interest_type=interest_type)
    ann_vol=daily_return_ps.std()*np.sqrt(year_date_num)
    return ann_ret/ann_vol
def generate_rolling_sharpe_plot(daily_return_ps,index_daily_return_ps,benchmark='Index',rolling_window=60,interest_type='SIMPLE'):
    if len(daily_return_ps)<=rolling_window:
        if len(daily_return_ps)<=10:
            return Paragraph('Not enough data for rolling sharpe calculation',pdf_styles['Normal'])
        rolling_window=int(len(daily_return_ps)/2)
    year_date_num=calc_year_date_num(daily_return_ps)
    rolling_sharpe_ps=daily_return_ps.rolling(rolling_window).apply(sharpe_helper,args=(year_date_num,interest_type))
    rolling_sharpe_ps.name='Strategy'
    index_rolling_sharpe_ps=index_daily_return_ps.rolling(rolling_window).apply(sharpe_helper,args=(year_date_num,interest_type))
    index_rolling_sharpe_ps.name=benchmark
    plt.figure(figsize=(fig_width,fig_height))
    ax1=plt.subplot(1,2,1)
    rolling_sharpe_ps.plot(ax=ax1,fontsize=font_size_axis)
    index_rolling_sharpe_ps.plot(ax=ax1,fontsize=font_size_axis)
    plt.legend(loc=legend_loc,fontsize=font_size_legend)
    plt.title('Sharpe Ratio (Rolling %d Days)'%rolling_window,fontsize=font_size_title,fontweight=font_title_weight)
    ax2=plt.subplot(1,2,2)
    pd.concat([index_rolling_sharpe_ps,rolling_sharpe_ps],axis=1).plot.scatter(ax=ax2,x=0,y=1,fontsize=font_size_axis)
    plt.title('Sharpe Ratio Distribution Relationship',fontsize=font_size_title,fontweight=font_title_weight)
    ax2.set_xlabel('%s Sharpe Ratio'%benchmark,fontsize=font_size_axis)
    ax2.set_ylabel('Strategy Sharpe Ratio',fontsize=font_size_axis)
    imgdata=BytesIO()
    plt.savefig(imgdata,format=img_format,dpi=img_dpi)
    imgdata.seek(0)
    plt.clf()
    plt.close()
    return Image(imgdata,width=img_width*inch,height=img_height*inch)
def generate_rolling_corr_plot(daily_return_ps,index_daily_return_ps,benchmark='Index',rolling_window=120,min_periods=5):
    if len(daily_return_ps)<=rolling_window:
        if len(daily_return_ps)<=10:
            return Paragraph('Not enough data for rolling correlation calculation',pdf_styles['Normal'])
        rolling_window=int(len(daily_return_ps)/2)
    plt.figure(figsize=(fig_width,fig_height))
    ax=plt.gca()
    df=pd.concat([daily_return_ps,index_daily_return_ps],axis=1)
    df_up=df.copy()
    df_up.loc[df.iloc[:,1]<0]=np.nan
    df_down=df.copy()
    df_down.loc[df.iloc[:,1]>0]=np.nan
    df_corr_ps=df.rolling(rolling_window,min_periods=min_periods).corr().xs(df.columns[0],level=1)[df.columns[1]]
    df_corr_up_ps=df_up.rolling(rolling_window,min_periods=min_periods).corr().xs(df.columns[0],level=1)[df.columns[1]]
    df_corr_down_ps=df_down.rolling(rolling_window,min_periods=min_periods).corr().xs(df.columns[0],level=1)[df.columns[1]]
    df_corr_ps.plot(ax=ax,fontsize=font_size_axis)
    df_corr_up_ps.plot(ax=ax,fontsize=font_size_axis)
    df_corr_down_ps.plot(ax=ax,fontsize=font_size_axis)
    plt.legend(['%s, all days'%benchmark,'%s, up days'%benchmark,'%s, down days'%benchmark],loc=legend_loc,fontsize=font_size_legend)
    plt.title('Strategy & %s Correlation (Rolling %d Days)'%(benchmark,rolling_window),fontsize=font_size_title,fontweight=font_title_weight)
    imgdata=BytesIO()
    plt.savefig(imgdata,format=img_format,dpi=img_dpi)
    imgdata.seek(0)
    plt.clf()
    plt.close()
    return Image(imgdata,width=img_width*inch,height=img_height*inch)
def generate_size_analysis_plots(sim_stock_book_value_detail,benchmark):
    sim_stock_weight=sim_stock_book_value_detail.divide(sim_stock_book_value_detail.abs().sum(axis=1),axis=0)
    sd=sim_stock_weight.index[0]
    ed=sim_stock_weight.index[-1]
    index_details=IO.read_data([sd,ed],columns=['index_50','index_300','index_500','alpha_universe'],ftype=FType.UNIV,dsource=DSource.OPTM)
    size=IO.read_data([sd,ed],columns=['Size'],ftype=FType.RISK,dsource=DSource.STYLEFACTOR)
    sim_stock_weight_stack=sim_stock_weight.stack()
    sim_stock_weight_stack=sim_stock_weight_stack.loc[sim_stock_weight_stack!=0]
    sim_stock_weight_stack.name='weight'
    sim_stock_weight_stack.index.names=['dt','Ticker']
    data=pd.concat([sim_stock_weight_stack,index_details],axis=1,join_axes=[sim_stock_weight_stack.index]).replace(np.nan,False)
    data['other']=~data[['index_50','index_500','index_300']].any(axis=1)
    data['wt_50']=data['weight']*data['index_50']
    data['wt_500']=data['weight']*data['index_500']
    data['wt_300']=data['weight']*data['index_300']
    data['wt_other']=data['weight']*data['other']
    res=data.groupby('dt').sum()
    res=res.rename(columns={'index_50':'num in 50','index_500':'num in 500','index_300':'num in 300','wt_50':'weight in 50','wt_500':'weight in 500','wt_300':'weight in 300','wt_other':'weight other'})
    plt.figure(figsize=(fig_width,fig_height))
    ax=plt.gca()
    res[['num in 50','num in 500','num in 300','other']].plot(ax=ax,fontsize=font_size_axis)
    plt.legend(loc=legend_loc,fontsize=font_size_legend)
    plt.title('Stock Numbers of Portfolio inside Indexs',fontsize=font_size_title,fontweight=font_title_weight)
    imgdata=BytesIO()
    plt.savefig(imgdata,format=img_format,dpi=img_dpi)
    imgdata.seek(0)
    plt.clf()
    plt.close()
    g_num_img=Image(imgdata,width=img_width*inch,height=img_height*inch)
    plt.figure(figsize=(fig_width,fig_height))
    ax=plt.gca()
    res[['weight in 50','weight in 500','weight in 300','weight other']].plot(ax=ax,fontsize=font_size_axis)
    plt.legend(loc=legend_loc,fontsize=font_size_legend)
    plt.title('Weights of Portfolio inside Indexs',fontsize=font_size_title,fontweight=font_title_weight)
    imgdata=BytesIO()
    plt.savefig(imgdata,format=img_format,dpi=img_dpi)
    imgdata.seek(0)
    plt.clf()
    plt.close()
    g_weight_img=Image(imgdata,width=img_width*inch,height=img_height*inch)
    plt.figure(figsize=(fig_width,fig_height))
    data=pd.concat([sim_stock_weight_stack,size],axis=1,join_axes=[sim_stock_weight_stack.index])
    bench_weight_col=weight_mapper[benchmark]
    index_weights=IO.read_data([sd,ed],columns=bench_weight_col,ftype=FType.INDEXWEIGHT,dsource=DSource.CSI)
    ind_data=pd.concat([size,index_details,index_weights],axis=1,join_axes=[size.index])
    ind_data['size_ind']=ind_data['Size']*ind_data[universe_mapper[benchmark]].replace(False,np.nan)
    stock_color=mcolors.TABLEAU_COLORS['tab:blue']
    ind_color=mcolors.TABLEAU_COLORS['tab:gray']
    ax1=plt.subplot(1,2,1)
    data['Size'].dropna().plot(kind='hist',bins=200,ax=ax1,fontsize=font_size_axis,fill=False,histtype='step',color=stock_color,lw=2,label='Portfolio')
    ax1_1=ax1.twinx()
    ind_data['size_ind'].dropna().plot(kind='hist',bins=200,ax=ax1_1,fontsize=font_size_axis,fill=False,histtype='step',color=ind_color,lw=2,label=benchmark)
    ax1.set_ylabel('Frequency',fontsize=font_size_axis)
    ax1_1.set_ylabel('',fontsize=font_size_axis)
    plt.legend(*legend_helper([ax1,ax1_1]),loc=legend_loc,fontsize=font_size_legend)
    plt.title('Portfolio & %s Size Distribution'%benchmark,fontsize=font_size_title,fontweight=font_title_weight)
    ax2=plt.subplot(1,2,2)
    data=data.sort_values(by='Size').dropna()
    ind_data=ind_data[['size_ind',bench_weight_col]].loc[ind_data[universe_mapper[benchmark]].replace(np.nan,False)].dropna()
    ax2.hist(data['Size'],bins=200,weights=data['weight'],fill=False,histtype='step',color=stock_color,lw=2,label='Portfolio')
    ax2_1=ax2.twinx()
    ind_data=ind_data.fillna(0)
    ax2_1.hist(ind_data['size_ind'],bins=200,weights=ind_data[bench_weight_col],fill=False,histtype='step',color=ind_color,lw=2,label=benchmark)
    ax2.set_ylabel('Frequency',fontsize=font_size_axis)
    ax2_1.set_ylabel('',fontsize=font_size_axis)
    plt.legend(*legend_helper([ax2,ax2_1]),loc=legend_loc,fontsize=font_size_legend)
    plt.title('Portfolio & %s Cap-Weighted Size Distribution'%benchmark,fontsize=font_size_title,fontweight=font_title_weight)
    imgdata=BytesIO()
    plt.savefig(imgdata,format=img_format,dpi=img_dpi)
    imgdata.seek(0)
    plt.clf()
    plt.close()
    g_size_img=Image(imgdata,width=img_width*inch,height=img_height*inch)
    return g_num_img,g_weight_img,g_size_img
def generate_line_ma_plot(ps_raw,variable_name,title_text,new_plot=True,title_format='.2g'):
    if new_plot:
        plt.figure(figsize=(fig_width,fig_height))
    ax=plt.gca()
    ps_raw_by_month=ps_raw.resample('M').mean()
    ps_raw.plot(ax=ax,style='*',fontsize=font_size_axis,alpha=0.2)
    ps_raw_by_month.plot(ax=ax,fontsize=font_size_axis,alpha=1,lw=2)
    ax.axhline(ps_raw.mean(),color='grey',linestyle='--',lw=3,alpha=0.6)
    ax.legend(['Daily %s'%variable_name,'Average Daily %s, by Month'%variable_name,'Average Daily %s, Net'%variable_name],loc=legend_loc,fontsize=font_size_legend)
    ax.set_title(title_text+(': Avg {:%s} '%title_format).format(ps_raw.mean()),fontsize=font_size_title)
    ax.set_xlabel('')
    if new_plot:
        imgdata=BytesIO()
        plt.savefig(imgdata,format=img_format,dpi=img_dpi)
        imgdata.seek(0)
        plt.clf()
        plt.close()
        return Image(imgdata,width=img_width*inch,height=img_height*inch)
def generate_turnover_ma_plot(turnover_ps):
    _=turnover_ps.iloc[:10]
    _.loc[_>=0.9]=np.nan
    return generate_line_ma_plot(turnover_ps,'Turnover','Turnover',title_format='.2%')
def generate_book_value_ma_plot(book_value_ps):
    _=book_value_ps.iloc[:10]
    _.loc[_==0]=np.nan
    book_value_ps.name='Stock Position'
    return generate_line_ma_plot(book_value_ps,'Stock Position','Stock Position',title_format=',.2f')
def generate_pnl_by_year(daily_return_ps,interest_type):
    selected_keys=['ann_ret','ann_vol','ann_sharpe','mdd','mdd_begin','mdd_end','mdd_duration','hit_rate']
    ps_list=list()
    stats=pnl_stats_helper(daily_return_ps,interest_type)
    _=pd.Series({key:stats[key]for key in stats if key in selected_keys})
    _.name='all'
    ps_list.append(_)
    year_list=list(daily_return_ps.index.year.unique())
    for year in year_list:
        stats=pnl_stats_helper(daily_return_ps.loc[str(year)],interest_type)
        _=pd.Series({key:stats[key]for key in stats if key in selected_keys})
        _.name=str(year)
        ps_list.append(_)
    stats_pd=pd.concat(ps_list,axis=1).T.reindex(columns=selected_keys)
    stats_pd=stats_pd.rename(columns={'ann_ret':'Return','ann_vol':'Volatility','ann_sharpe':'Sharpe','mdd':'Max Drawdown','mdd_begin':'MDD Start','mdd_end':'MDD End','mdd_duration':'MDD Duration','hit_rate':'Hit Rate'})
    stats_pd['MDD Start']=stats_pd['MDD Start'].dt.strftime('%Y-%m-%d')
    stats_pd['MDD End']=stats_pd['MDD End'].dt.strftime('%Y-%m-%d')
    return stats_pd
def solve_data(csv_path,stock_leverage,fts_leverage,trade_cycle,benchmark):
    industry_mapper=CITIC_I_abbr_mapper
    industry_str='ind'
    sim_stats_daily=pd.read_csv(os.path.join(csv_path,'sim_stats_daily.csv'),index_col=0,parse_dates=True)
    sim_stats_daily['cum_profit']=sim_stats_daily['net_return'].cumsum()
    if fts_leverage is not None:
        sim_stats_daily['daily_return']=sim_stats_daily['net_return']/(sim_stats_daily['stocks_total_book_value']/stock_leverage+sim_stats_daily['fts_total_book_value']/fts_leverage)
    else:
        sim_stats_daily['daily_return']=sim_stats_daily['net_return']/(sim_stats_daily['stocks_total_book_value']/stock_leverage)
    sim_stats_daily['cum_ret']=sim_stats_daily['daily_return'].cumsum()
    sim_stats_daily['hedge ratio']=sim_stats_daily['stocks_total_book_value']/sim_stats_daily['fts_total_book_value']
    sim_stats_daily['hedge ratio']=sim_stats_daily['hedge ratio'].replace([np.nan,np.inf,-np.inf],0)
    sim_stock_book_value_detail=pd.read_csv(os.path.join(csv_path,'sim_stock_book_value_detail.csv'),index_col=0,parse_dates=True)
    sim_stock_holding_num=(sim_stock_book_value_detail>0).sum(axis=1)
    sim_stock_factor_expo_detail=pd.read_csv(os.path.join(csv_path,'sim_stock_factor_expo_detail.csv'),index_col=0,parse_dates=True)
    sim_stock_factor_expo_detail.columns=[int(item.replace(industry_str,''))if industry_str in item else item                                            for item in sim_stock_factor_expo_detail.columns]
    sim_stock_factor_expo_detail=sim_stock_factor_expo_detail.rename(columns=industry_mapper)
    industry_list=[item for item in sim_stock_factor_expo_detail.columns if item in industry_mapper.values()]
    style_list=[item for item in sim_stock_factor_expo_detail.columns if item not in list(industry_mapper.values())+['alpha_expo']]
    sim_futures_close_price=pd.read_csv(os.path.join(csv_path,'sim_futures_close_price.csv'),index_col=0,parse_dates=True)
    sim_bench_stock_weight=pd.read_csv(os.path.join(csv_path,'sim_bench_stock_weight.csv'),index_col=0,parse_dates=True)
    sim_stock_adjusted_close_price=pd.read_csv(os.path.join(csv_path,'sim_stock_adjusted_close_price.csv'),index_col=0,parse_dates=True)
    sim_stock_industry=pd.read_csv(os.path.join(csv_path,'sim_stock_industry.csv'),index_col=0,parse_dates=True)
    sim_stock_pnl_detail=pd.read_csv(os.path.join(csv_path,'sim_stock_pnl_detail.csv'),index_col=0,parse_dates=True).diff()
    sim_stock_weights_target_detail=pd.read_csv(os.path.join(csv_path,'sim_stock_weights_target_detail.csv'),index_col=0,parse_dates=True)
    stock_daily_gain=sim_stock_adjusted_close_price/sim_stock_adjusted_close_price.shift(1)-1
    _stock_daily_gain=stock_daily_gain.stack()
    aligned_unstacked_pd=pd.concat([sim_bench_stock_weight.stack(),_stock_daily_gain,sim_stock_industry.stack(),sim_stock_pnl_detail.stack(),sim_stock_book_value_detail.stack()],axis=1,join_axes=[_stock_daily_gain.index])
    aligned_unstacked_pd.columns=['bench_weight','stock_gain','industry','holding_pnl','book_value']
    aligned_unstacked_pd.index.names=['dt','Ticker']
    aligned_unstacked_pd['index_return']=aligned_unstacked_pd['bench_weight']*aligned_unstacked_pd['stock_gain']
    grouped=aligned_unstacked_pd.groupby(by=['dt','industry'])
    sim_index_daily_return_per_industry=grouped['index_return'].sum().unstack().resample('M').sum()/grouped['bench_weight'].sum().unstack().resample('M').mean()
    sim_portfolio_daily_return_per_industry=grouped['holding_pnl'].sum().unstack().resample('M').sum()/grouped['book_value'].sum().unstack().resample('M').mean()*stock_leverage
    sim_index_daily_return_per_industry.columns=[int(item.replace(industry_str,''))for item in sim_index_daily_return_per_industry.columns]
    sim_index_daily_return_per_industry=sim_index_daily_return_per_industry.rename(columns=industry_mapper)
    sim_index_daily_return_per_industry.index.name=''
    sim_portfolio_daily_return_per_industry.columns=[int(item.replace(industry_str,''))for item in sim_portfolio_daily_return_per_industry.columns]
    sim_portfolio_daily_return_per_industry=sim_portfolio_daily_return_per_industry.rename(columns=industry_mapper)
    sim_portfolio_daily_return_per_industry.index.name=''
    if not isinstance(trade_cycle,int):
        if trade_cycle in trade_cycle_mapper:
            trade_cycle=trade_cycle_mapper[trade_cycle]
        else:
            raise AssertionError
    stock_holding_period_return=sim_stock_adjusted_close_price.shift(-trade_cycle)/sim_stock_adjusted_close_price-1
    benchmark_holding_period_return=sim_futures_close_price.shift(-trade_cycle)/sim_futures_close_price-1
    stock_excess_hpr=stock_holding_period_return.subtract(benchmark_holding_period_return[benchmark],axis=0)
    _=stock_excess_hpr.reindex(sim_stock_weights_target_detail.index)*sim_stock_weights_target_detail.replace(0,np.nan)
    sim_winning_ratio_per_day=(_>0).sum(axis=1)/np.isfinite(_).sum(axis=1)
    benchmark_daily_gain=sim_futures_close_price/sim_futures_close_price.shift(1)-1
    HS300_ZZ500_daily_return_diff=benchmark_daily_gain['HS300']-benchmark_daily_gain['ZZ500']
    res={'sim_stats_daily':sim_stats_daily,'sim_stock_book_value_detail':sim_stock_book_value_detail,'sim_stock_holding_num':sim_stock_holding_num,'sim_stock_factor_expo_detail':sim_stock_factor_expo_detail,'sim_index_daily_return_per_industry':sim_index_daily_return_per_industry,'sim_portfolio_daily_return_per_industry':sim_portfolio_daily_return_per_industry,'sim_winning_ratio_per_day':sim_winning_ratio_per_day,'HS300_ZZ500_daily_return_diff':HS300_ZZ500_daily_return_diff,'benchmark_daily_gain':benchmark_daily_gain,'industry_list':industry_list,'style_list':style_list}
    return res
def report_generator(csv_path='',config_str=None,stock_leverage=1,fts_leverage=4,interest_type='SIMPLE',benchmark='ZZ500',trade_cycle='DAILY'):
    print('begin simulation report generation')
    solved_data=solve_data(csv_path,stock_leverage,fts_leverage,trade_cycle,benchmark)
    print('basic data parsed from csv')
    sim_stats_daily=solved_data['sim_stats_daily']
    sim_stock_book_value_detail=solved_data['sim_stock_book_value_detail']
    sim_stock_holding_num=solved_data['sim_stock_holding_num']
    sim_stock_factor_expo_detail=solved_data['sim_stock_factor_expo_detail']
    sim_index_daily_return_per_industry=solved_data['sim_index_daily_return_per_industry']
    sim_portfolio_daily_return_per_industry=solved_data['sim_portfolio_daily_return_per_industry']
    sim_winning_ratio_per_day=solved_data['sim_winning_ratio_per_day']
    HS300_ZZ500_daily_return_diff=solved_data['HS300_ZZ500_daily_return_diff']
    benchmark_daily_gain=solved_data['benchmark_daily_gain']
    industry_list=solved_data['industry_list']
    style_list=solved_data['style_list']
    style_list = [i for i in style_list if i!='Industry']
    daily_return_ps=sim_stats_daily['daily_return']
    index_daily_return_ps=benchmark_daily_gain[benchmark]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        VaR_level=0.95
        _daily_return_ps=daily_return_ps.dropna()
        daily_return_skew=sps.skew(_daily_return_ps)
        daily_return_kurtosis=sps.kurtosis(_daily_return_ps)
        daily_return_bot_percentile=_daily_return_ps.quantile(1-VaR_level)
        daily_return_mean=_daily_return_ps.mean()
        print('return statistics calculated')
    now=dt.datetime.today()
    file_date=now.strftime("%Y%m%d_%H%M%S")
    pdf_report_info='PDF Date: '+now.strftime("%Y-%m-%d %H:%M:%S")+', Simulator: v.'+simulator_version
    report_name='StrategyBacktest_'+str(file_date)+'.pdf'
    g_pnl_with_mdd=generate_pnl_with_mdd_plot(daily_return_ps,index_daily_return_ps,interest_type,benchmark)
    g_pnl_with_mdd_year=generate_pnl_with_mdd_year_plot(daily_return_ps,interest_type)
    g_rolling_sharpe=generate_rolling_sharpe_plot(daily_return_ps,index_daily_return_ps,benchmark=benchmark,interest_type=interest_type)
    g_turnover_ma=generate_turnover_ma_plot(sim_stats_daily['turnover']/2)
    g_book_value_ma=generate_book_value_ma_plot(sim_stats_daily['stocks_total_book_value'])
    g_hedge_ratio_ma=generate_line_ma_plot(sim_stats_daily['hedge ratio'],'Hedge Ratio','Hedge Ratio',title_format='.2f')
    g_winning_ratio_ma=generate_line_ma_plot(sim_winning_ratio_per_day,'Winning Ratio','Prediction Winning Ratio (Cross Sectional)',title_format='.2%')
    g_stock_holding_num_ma=generate_line_ma_plot(sim_stock_holding_num,'Stock Holding Number','Stock Holding Number',title_format='.0f')
    if 'alpha_expo' in sim_stock_factor_expo_detail:
        g_style_exposure=generate_line_subplot(sim_stock_factor_expo_detail[style_list+['alpha_expo']])
    else:
        g_style_exposure=generate_line_subplot(sim_stock_factor_expo_detail[style_list])
    acronym_stock_factor_expo_detail=sim_stock_factor_expo_detail[style_list].copy()
    acronym_stock_factor_expo_detail.columns=acronyms(acronym_stock_factor_expo_detail.columns)
    g_style_exposure_distribution=generate_whisker_plot(acronym_stock_factor_expo_detail,title='Style Exposure Distribution')
    g_ind_exposure_distribution=generate_whisker_plot(sim_stock_factor_expo_detail[industry_list],title='Industry Exposure Distribution',rot=90,bottom=0.2)
    g_daily_return_heatmap=generate_ts_heatmap_by_month_plot(daily_return_ps,title_text='Return by Month',vmax=0.05,vmin=-0.02,fmt='.2%',agg_method='sum')
    g_daily_return_rolling_corr=generate_rolling_corr_plot(daily_return_ps,index_daily_return_ps,benchmark=benchmark)
    g_daily_return_rolling_corr_diff=generate_rolling_corr_plot(daily_return_ps,HS300_ZZ500_daily_return_diff,benchmark='HS300 minus ZZ500')
    return_distribution_description='Daily Return Distribution \n'+'Skew: {:.2f},  Kurtosis: {:.2f},  {:.0%} VaR: {:.3%},  Mean: {:.3%}'.format(daily_return_skew,daily_return_kurtosis,VaR_level,daily_return_bot_percentile,daily_return_mean)
    g_return_distribution=generate_plot(pd.DataFrame(daily_return_ps),return_distribution_description,'Daily Return','Frequency',plot_type='hist',bins=200)
    per_industry_excess_pnl=sim_portfolio_daily_return_per_industry-sim_index_daily_return_per_industry
    assert set(per_industry_excess_pnl.columns)==set(industry_list)
    g_ind_excess_pnl_distribution=generate_whisker_plot(per_industry_excess_pnl[industry_list],title='Monthly Industry Excess Return Distribution',rot=90,bottom=0.2,showfliers=False)
    g_stock_num_index,g_weight_in_index,g_size_distribution=generate_size_analysis_plots(sim_stock_book_value_detail,benchmark)
    print('graphs generated')
    col_type=['pct2','pct2','dcm2','pct2','str1','str1','dcm0','pct2']
    t_pnl_by_year=generate_table(generate_pnl_by_year(daily_return_ps,interest_type),col_type,axis=1,reformat_type=True)
    mytable=TableStyle([('ALIGNMENT',(0,0),(-1,-1),'CENTER'),('LINEABOVE',(0,1),(-1,1),1,colors.black)])
    t_pnl_by_year.setStyle(mytable)
    h_gapping=Paragraph('',pdf_styles['Heading6'])
    h_info=Paragraph(pdf_report_info,pdf_styles['Normal'])
    h_portfolio_return=Paragraph('Portfolio Return',heading_size)
    h_portfolio_return_by_year=Paragraph('Portfolio Return by Year',heading_size)
    h_style_ind_exposure_distribution=Paragraph('Style & Industry Exposures Distribution',heading_size)
    h_style_exposure=Paragraph('Style Exposure Time Series',heading_size)
    h_return_distribution=Paragraph('Daily Return Distribution',heading_size)
    h_winning_ratio_ma=Paragraph('Cross Sectional Prediction Winning Ratio',heading_size)
    h_stock_holding_num_ma=Paragraph('Stock Holding Number',heading_size)
    h_turnover_ma=Paragraph('Turnover',heading_size)
    h_book_value_ma=Paragraph('Stock Position',heading_size)
    h_hedge_ratio_ma=Paragraph('Hedge Ratio - Stock / Futures',heading_size)
    h_rolling_sharpe=Paragraph('Rolling Sharpe with Market',heading_size)
    h_daily_return_rolling_corr=Paragraph('Return Correlation with Market',heading_size)
    h_daily_return_rolling_corr_diff=Paragraph('Return Correlation with HS300-ZZ500',heading_size)
    h_stock_num_index=Paragraph('Stock Numbers of Portfolio inside Indexs',heading_size)
    h_weight_in_index=Paragraph('Weights of Portfolio inside Indexs',heading_size)
    h_size_distribution=Paragraph('Size Distribution Analysis',heading_size)
    if config_str is not None:
        h_config=Paragraph(config_str.replace('\n','<br />\n'),pdf_styles['Code'])
    doc=SimpleDocTemplate(os.path.join(csv_path,report_name),pagesize=letter,topMargin=0.8*inch,bottomMargin=0.8*inch)
    elements=[]
    elements.append(h_gapping)
    elements.append(h_gapping)
    elements.append(h_info)
    elements.append(h_portfolio_return)
    elements.append(g_pnl_with_mdd)
    elements.append(g_daily_return_heatmap)
    elements.append(h_gapping)
    elements.append(t_pnl_by_year)
    elements.append(PageBreak())
    elements.append(h_portfolio_return_by_year)
    elements.append(g_pnl_with_mdd_year)
    elements.append(PageBreak())
    elements.append(h_return_distribution)
    elements.append(g_return_distribution)
    elements.append(h_winning_ratio_ma)
    elements.append(g_winning_ratio_ma)
    elements.append(h_stock_holding_num_ma)
    elements.append(g_stock_holding_num_ma)
    elements.append(PageBreak())
    elements.append(h_turnover_ma)
    elements.append(g_turnover_ma)
    elements.append(h_book_value_ma)
    elements.append(g_book_value_ma)
    elements.append(h_hedge_ratio_ma)
    elements.append(g_hedge_ratio_ma)
    elements.append(PageBreak())
    elements.append(h_size_distribution)
    elements.append(g_size_distribution)
    elements.append(h_stock_num_index)
    elements.append(g_stock_num_index)
    elements.append(h_weight_in_index)
    elements.append(g_weight_in_index)
    elements.append(PageBreak())
    elements.append(h_rolling_sharpe)
    elements.append(g_rolling_sharpe)
    elements.append(h_daily_return_rolling_corr)
    elements.append(g_daily_return_rolling_corr)
    elements.append(h_daily_return_rolling_corr_diff)
    elements.append(g_daily_return_rolling_corr_diff)
    elements.append(PageBreak())
    elements.append(h_style_ind_exposure_distribution)
    elements.append(g_style_exposure_distribution)
    elements.append(g_ind_exposure_distribution)
    elements.append(g_ind_excess_pnl_distribution)
    elements.append(PageBreak())
    elements.append(h_style_exposure)
    elements.append(g_style_exposure)
    elements.append(PageBreak())
    if config_str is not None:
        elements.append(h_config)
    _generate_first_page=partial(generate_first_page,title='Alpha Strategy Backtest Report')
    doc.build(elements,onFirstPage=_generate_first_page,onLaterPages=generate_later_pages,canvasmaker=NumberedCanvas)
    plt.close('all')
    print('finished')
